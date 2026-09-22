"""Same-fold benchmark of recent missing-modality survival method families.

U10 adds transparent blood--ICD--TMA adaptations of the fusion families used
by two 2026 studies without changing the frozen U9 benchmark or the locked
V1R predictions.  The adaptations retain each family's defining fusion
principle but use a common censoring-aware discrete-hazard head so every row
targets the same estimand.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from torch import Tensor, nn

from trust_hn.pattern_surv_hn.hancock_contract import HancockContractBuilder
from trust_hn.pattern_surv_hn.u9_published_comparators import (
    FoldFeatures,
    _discrete_targets,
    _prepare_features,
    _set_torch_seed,
    _time_grid,
)
from trust_hn.pattern_surv_hn.v0_clinical_anchor import (
    _development_arrays,
    evaluate_predictions,
    structured_survival,
)

METHODS = (
    "EARLY_FUSION",
    "LATE_FUSION",
    "MASKED_ATTENTION",
    "BILINEAR_FUSION",
    "RUFFINI2026",
    "HAF2026",
    "V1R",
)
DEFAULT_SPEC = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U10_recent_comparator_benchmark/frozen_u10_recent_comparator_benchmark_spec.yaml"
)
DEFAULT_V1R_OOF = Path(
    "results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv"
)
DEFAULT_OUTPUT = Path("results/metrics/pattern_surv_hn/U10_recent_comparator_benchmark")
DEFAULT_PREDICTIONS = Path(
    "results/predictions/pattern_surv_hn/U10_recent_comparators"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _load_spec(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if payload.get("analysis_label") != "post_hoc_exploratory_recent_method_benchmark":
        raise ValueError("U10 must remain explicitly post-hoc exploratory")
    if tuple(payload.get("methods", {})) != METHODS[:-1]:
        raise ValueError("U10 method order differs from the frozen method list")
    governance = payload.get("governance", {})
    if not governance.get("post_hoc_exploratory"):
        raise ValueError("U10 cannot be labelled confirmatory")
    if governance.get("confirmation_outcomes_used") or governance.get("retune_v1r"):
        raise ValueError("U10 governance permits a prohibited action")
    return payload


def _modality_tensors(features: FoldFeatures) -> tuple[Tensor, tuple[Tensor, ...], Tensor]:
    clinical = torch.as_tensor(features.clinical, dtype=torch.float64)
    modalities = tuple(
        torch.as_tensor(values, dtype=torch.float64) for values in features.modalities
    )
    active = torch.as_tensor(features.active, dtype=torch.bool)
    return clinical, modalities, active


def _hazard_nll_rows(logits: Tensor, bins: Tensor, event: Tensor) -> Tensor:
    log_hazard = torch.nn.functional.logsigmoid(logits)
    log_survival = torch.nn.functional.logsigmoid(-logits)
    positions = torch.arange(logits.shape[1], device=logits.device)[None, :]
    before = positions < bins[:, None]
    through = positions <= bins[:, None]
    event_ll = (log_survival * before).sum(dim=1) + log_hazard.gather(
        1, bins[:, None]
    ).squeeze(1)
    censored_ll = (log_survival * through).sum(dim=1)
    return -torch.where(event, event_ll, censored_ll)


def _hazard_nll(logits: Tensor, bins: Tensor, event: Tensor) -> Tensor:
    return _hazard_nll_rows(logits, bins, event).mean()


class _Encoder(nn.Module):
    def __init__(self, input_dim: int, representation_dim: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, representation_dim),
            nn.LayerNorm(representation_dim),
            nn.ReLU(),
            nn.Linear(representation_dim, representation_dim),
            nn.ReLU(),
        )

    def forward(self, values: Tensor) -> Tensor:
        return self.layers(values)


def _availability(active: Tensor) -> Tensor:
    return torch.column_stack(
        [torch.ones(active.shape[0], dtype=torch.bool, device=active.device), active]
    )


class _RuffiniIntermediateFusion(nn.Module):
    """Adapted frozen-encoder intermediate fusion from Ruffini et al. (2026)."""

    def __init__(self, dimensions: Sequence[int], representation_dim: int, intervals: int):
        super().__init__()
        self.encoders = nn.ModuleList(
            [_Encoder(int(width), representation_dim) for width in dimensions]
        )
        self.unimodal_heads = nn.ModuleList(
            [nn.Linear(representation_dim, intervals) for _ in dimensions]
        )
        fused_dim = representation_dim * len(dimensions) + len(dimensions)
        self.fusion_head = nn.Sequential(
            nn.Linear(fused_dim, representation_dim),
            nn.ReLU(),
            nn.Linear(representation_dim, intervals),
        )
        self.double()

    def encode(
        self, clinical: Tensor, modalities: Sequence[Tensor], active: Tensor
    ) -> tuple[list[Tensor], Tensor]:
        available = _availability(active)
        inputs = (clinical, *modalities)
        tokens: list[Tensor] = []
        for index, (encoder, values) in enumerate(zip(self.encoders, inputs, strict=True)):
            token = encoder(values)
            token = torch.where(available[:, index : index + 1], token, 0.0)
            tokens.append(token)
        return tokens, available

    def forward(
        self, clinical: Tensor, modalities: Sequence[Tensor], active: Tensor
    ) -> Tensor:
        tokens, available = self.encode(clinical, modalities, active)
        fused = torch.cat([*tokens, available.to(torch.float64)], dim=1)
        return self.fusion_head(fused)


class _HeterogeneousAlignedFusion(nn.Module):
    """Description-faithful HAF adaptation with explicit availability masking."""

    def __init__(
        self,
        dimensions: Sequence[int],
        representation_dim: int,
        alignment_dim: int,
        intervals: int,
    ):
        super().__init__()
        self.encoders = nn.ModuleList(
            [_Encoder(int(width), representation_dim) for width in dimensions]
        )
        self.unimodal_heads = nn.ModuleList(
            [nn.Linear(representation_dim, intervals) for _ in dimensions]
        )
        self.projectors = nn.ModuleList(
            [nn.Linear(representation_dim, alignment_dim) for _ in dimensions]
        )
        self.aligned_head = nn.Linear(alignment_dim, intervals)
        self.gate = nn.Linear(alignment_dim, 1)
        self.modality_bias = nn.Parameter(torch.zeros(len(dimensions), dtype=torch.float64))
        self.fusion_head = nn.Sequential(
            nn.Linear(alignment_dim + len(dimensions), representation_dim),
            nn.ReLU(),
            nn.Linear(representation_dim, intervals),
        )
        self.double()

    def aligned_tokens(
        self, clinical: Tensor, modalities: Sequence[Tensor], active: Tensor
    ) -> tuple[Tensor, Tensor]:
        inputs = (clinical, *modalities)
        available = _availability(active)
        projected = []
        for index, (encoder, projector, values) in enumerate(
            zip(self.encoders, self.projectors, inputs, strict=True)
        ):
            token = projector(encoder(values))
            token = torch.where(available[:, index : index + 1], token, 0.0)
            projected.append(token)
        return torch.stack(projected, dim=1), available

    def fuse(self, tokens: Tensor, available: Tensor) -> Tensor:
        scores = self.gate(tokens).squeeze(-1) + self.modality_bias[None, :]
        scores = scores.masked_fill(~available, -1e9)
        weights = torch.softmax(scores, dim=1)
        fused = (tokens * weights[:, :, None]).sum(dim=1)
        return self.fusion_head(torch.cat([fused, available.to(torch.float64)], dim=1))

    def forward(
        self, clinical: Tensor, modalities: Sequence[Tensor], active: Tensor
    ) -> Tensor:
        tokens, available = self.aligned_tokens(clinical, modalities, active)
        return self.fuse(tokens, available)


class _EarlyFusion(nn.Module):
    """Availability-aware feature concatenation followed by a shared hazard head."""

    def __init__(self, dimensions: Sequence[int], representation_dim: int, intervals: int):
        super().__init__()
        input_dim = int(sum(dimensions)) + len(dimensions) - 1
        self.head = nn.Sequential(
            nn.Linear(input_dim, representation_dim),
            nn.ReLU(),
            nn.Linear(representation_dim, intervals),
        )
        self.double()

    def forward(
        self, clinical: Tensor, modalities: Sequence[Tensor], active: Tensor
    ) -> Tensor:
        masked = [
            torch.where(active[:, index : index + 1], values, 0.0)
            for index, values in enumerate(modalities)
        ]
        return self.head(torch.cat([clinical, *masked, active.to(torch.float64)], dim=1))


class _MaskedAttentionFusion(nn.Module):
    """Intermediate attention fusion without HAF's alignment or monotonic losses."""

    def __init__(self, dimensions: Sequence[int], representation_dim: int, intervals: int):
        super().__init__()
        self.encoders = nn.ModuleList(
            [_Encoder(int(width), representation_dim) for width in dimensions]
        )
        self.gate = nn.Linear(representation_dim, 1)
        self.head = nn.Sequential(
            nn.Linear(representation_dim + len(dimensions), representation_dim),
            nn.ReLU(),
            nn.Linear(representation_dim, intervals),
        )
        self.double()

    def forward(
        self, clinical: Tensor, modalities: Sequence[Tensor], active: Tensor
    ) -> Tensor:
        available = _availability(active)
        tokens = torch.stack(
            [
                torch.where(
                    available[:, index : index + 1], encoder(values), 0.0
                )
                for index, (encoder, values) in enumerate(
                    zip(self.encoders, (clinical, *modalities), strict=True)
                )
            ],
            dim=1,
        )
        scores = self.gate(tokens).squeeze(-1).masked_fill(~available, -1e9)
        weights = torch.softmax(scores, dim=1)
        fused = (tokens * weights[:, :, None]).sum(dim=1)
        return self.head(torch.cat([fused, available.to(torch.float64)], dim=1))


class _BilinearFusion(nn.Module):
    """Low-rank pairwise interaction fusion over the available modality tokens."""

    def __init__(self, dimensions: Sequence[int], representation_dim: int, intervals: int):
        super().__init__()
        self.encoders = nn.ModuleList(
            [_Encoder(int(width), representation_dim) for width in dimensions]
        )
        self.head = nn.Sequential(
            nn.Linear(2 * representation_dim + len(dimensions), representation_dim),
            nn.ReLU(),
            nn.Linear(representation_dim, intervals),
        )
        self.double()

    def forward(
        self, clinical: Tensor, modalities: Sequence[Tensor], active: Tensor
    ) -> Tensor:
        available = _availability(active)
        tokens = torch.stack(
            [
                torch.where(
                    available[:, index : index + 1], encoder(values), 0.0
                )
                for index, (encoder, values) in enumerate(
                    zip(self.encoders, (clinical, *modalities), strict=True)
                )
            ],
            dim=1,
        )
        count = available.sum(dim=1).clamp_min(1).to(torch.float64)[:, None]
        first_order = tokens.sum(dim=1) / count
        pair_sum = torch.zeros_like(first_order)
        pair_count = torch.zeros((tokens.shape[0], 1), dtype=torch.float64)
        for left in range(tokens.shape[1]):
            for right in range(left + 1, tokens.shape[1]):
                paired = available[:, left] & available[:, right]
                pair_sum = pair_sum + tokens[:, left] * tokens[:, right] * paired[:, None]
                pair_count = pair_count + paired.to(torch.float64)[:, None]
        interactions = pair_sum / pair_count.clamp_min(1.0)
        return self.head(
            torch.cat([first_order, interactions, available.to(torch.float64)], dim=1)
        )


def _fit_unimodal_encoders(
    model: _RuffiniIntermediateFusion | _HeterogeneousAlignedFusion,
    clinical: Tensor,
    modalities: Sequence[Tensor],
    active: Tensor,
    bins: Tensor,
    event: Tensor,
    *,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
) -> None:
    available = _availability(active)
    inputs = (clinical, *modalities)
    for index, (encoder, head, values) in enumerate(
        zip(model.encoders, model.unimodal_heads, inputs, strict=True)
    ):
        keep = available[:, index]
        optimizer = torch.optim.Adam(
            [*encoder.parameters(), *head.parameters()],
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        for _ in range(epochs):
            optimizer.zero_grad(set_to_none=True)
            loss = _hazard_nll(head(encoder(values[keep])), bins[keep], event[keep])
            loss.backward()
            torch.nn.utils.clip_grad_norm_([*encoder.parameters(), *head.parameters()], 5.0)
            optimizer.step()
    for parameter in model.encoders.parameters():
        parameter.requires_grad_(False)
    for parameter in model.unimodal_heads.parameters():
        parameter.requires_grad_(False)


def _risks_from_logits(
    logits: Tensor, edges: np.ndarray, horizon: float
) -> tuple[np.ndarray, np.ndarray]:
    hazards = torch.sigmoid(logits).detach().cpu().numpy()
    cumulative_risk = 1.0 - np.cumprod(1.0 - hazards, axis=1)
    horizon_bin = min(int(np.searchsorted(edges, horizon, side="left")), len(edges) - 1)
    return cumulative_risk[:, -1], np.clip(cumulative_risk[:, horizon_bin], 0.0, 1.0)


def _train_joint_fusion(
    model: nn.Module,
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Train a censoring-aware fusion family on one outer-training fold."""
    _set_torch_seed(seed)
    edges = _time_grid(duration, int(config["intervals"]))
    bins = torch.as_tensor(_discrete_targets(duration, edges), dtype=torch.long)
    event_tensor = torch.as_tensor(event, dtype=torch.bool)
    clinical, modalities, active = _modality_tensors(train)
    eval_clinical, eval_modalities, eval_active = _modality_tensors(evaluation)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    for _ in range(int(config["epochs"])):
        optimizer.zero_grad(set_to_none=True)
        loss = _hazard_nll(model(clinical, modalities, active), bins, event_tensor)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
    model.eval()
    with torch.no_grad():
        logits = model(eval_clinical, eval_modalities, eval_active)
    return _risks_from_logits(logits, edges, horizon)


def _train_early(
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    _set_torch_seed(seed)
    model = _EarlyFusion(
        [train.clinical.shape[1], *(values.shape[1] for values in train.modalities)],
        int(config["representation_dim"]),
        len(_time_grid(duration, int(config["intervals"]))),
    )
    return _train_joint_fusion(
        model, train, event, duration, evaluation, config, seed, horizon
    )


def _train_attention(
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    _set_torch_seed(seed)
    model = _MaskedAttentionFusion(
        [train.clinical.shape[1], *(values.shape[1] for values in train.modalities)],
        int(config["representation_dim"]),
        len(_time_grid(duration, int(config["intervals"]))),
    )
    return _train_joint_fusion(
        model, train, event, duration, evaluation, config, seed, horizon
    )


def _train_bilinear(
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    _set_torch_seed(seed)
    model = _BilinearFusion(
        [train.clinical.shape[1], *(values.shape[1] for values in train.modalities)],
        int(config["representation_dim"]),
        len(_time_grid(duration, int(config["intervals"]))),
    )
    return _train_joint_fusion(
        model, train, event, duration, evaluation, config, seed, horizon
    )


def _train_late(
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Average modality-specific hazard logits over the inputs available per patient."""
    _set_torch_seed(seed)
    edges = _time_grid(duration, int(config["intervals"]))
    bins = torch.as_tensor(_discrete_targets(duration, edges), dtype=torch.long)
    event_tensor = torch.as_tensor(event, dtype=torch.bool)
    clinical, modalities, active = _modality_tensors(train)
    eval_clinical, eval_modalities, eval_active = _modality_tensors(evaluation)
    model = _RuffiniIntermediateFusion(
        [train.clinical.shape[1], *(values.shape[1] for values in train.modalities)],
        int(config["representation_dim"]),
        len(edges),
    )
    _fit_unimodal_encoders(
        model,
        clinical,
        modalities,
        active,
        bins,
        event_tensor,
        epochs=int(config["unimodal_epochs"]),
        learning_rate=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    with torch.no_grad():
        available = _availability(eval_active)
        inputs = (eval_clinical, *eval_modalities)
        logits = torch.stack(
            [
                head(encoder(values))
                for encoder, head, values in zip(
                    model.encoders, model.unimodal_heads, inputs, strict=True
                )
            ],
            dim=1,
        )
        logits = (logits * available[:, :, None]).sum(dim=1) / available.sum(
            dim=1
        ).to(torch.float64)[:, None]
    return _risks_from_logits(logits, edges, horizon)


def _train_ruffini(
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    _set_torch_seed(seed)
    edges = _time_grid(duration, int(config["intervals"]))
    bins = torch.as_tensor(_discrete_targets(duration, edges), dtype=torch.long)
    event_tensor = torch.as_tensor(event, dtype=torch.bool)
    clinical, modalities, active = _modality_tensors(train)
    eval_clinical, eval_modalities, eval_active = _modality_tensors(evaluation)
    model = _RuffiniIntermediateFusion(
        [train.clinical.shape[1], *(values.shape[1] for values in train.modalities)],
        int(config["representation_dim"]),
        len(edges),
    )
    _fit_unimodal_encoders(
        model,
        clinical,
        modalities,
        active,
        bins,
        event_tensor,
        epochs=int(config["unimodal_epochs"]),
        learning_rate=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    optimizer = torch.optim.Adam(
        model.fusion_head.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    for _ in range(int(config["fusion_epochs"])):
        optimizer.zero_grad(set_to_none=True)
        loss = _hazard_nll(model(clinical, modalities, active), bins, event_tensor)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.fusion_head.parameters(), 5.0)
        optimizer.step()
    model.eval()
    with torch.no_grad():
        logits = model(eval_clinical, eval_modalities, eval_active)
    return _risks_from_logits(logits, edges, horizon)


def _train_haf(
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    _set_torch_seed(seed)
    edges = _time_grid(duration, int(config["intervals"]))
    bins = torch.as_tensor(_discrete_targets(duration, edges), dtype=torch.long)
    event_tensor = torch.as_tensor(event, dtype=torch.bool)
    clinical, modalities, active = _modality_tensors(train)
    eval_clinical, eval_modalities, eval_active = _modality_tensors(evaluation)
    model = _HeterogeneousAlignedFusion(
        [train.clinical.shape[1], *(values.shape[1] for values in train.modalities)],
        int(config["representation_dim"]),
        int(config["alignment_dim"]),
        len(edges),
    )
    _fit_unimodal_encoders(
        model,
        clinical,
        modalities,
        active,
        bins,
        event_tensor,
        epochs=int(config["unimodal_epochs"]),
        learning_rate=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    alignment_parameters = [
        *model.projectors.parameters(),
        *model.aligned_head.parameters(),
    ]
    optimizer = torch.optim.Adam(
        alignment_parameters,
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    for _ in range(int(config["alignment_epochs"])):
        optimizer.zero_grad(set_to_none=True)
        tokens, available = model.aligned_tokens(clinical, modalities, active)
        pair_losses = []
        prognostic_losses = []
        for left in range(tokens.shape[1]):
            keep = available[:, left]
            prognostic_losses.append(
                _hazard_nll(model.aligned_head(tokens[keep, left]), bins[keep], event_tensor[keep])
            )
            for right in range(left + 1, tokens.shape[1]):
                paired = available[:, left] & available[:, right]
                if paired.any():
                    pair_losses.append(
                        torch.nn.functional.mse_loss(
                            tokens[paired, left], tokens[paired, right]
                        )
                    )
        alignment_loss = torch.stack(pair_losses).mean()
        prognostic_loss = torch.stack(prognostic_losses).mean()
        loss = prognostic_loss + float(config["alignment_weight"]) * alignment_loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(alignment_parameters, 5.0)
        optimizer.step()
    for parameter in model.projectors.parameters():
        parameter.requires_grad_(False)
    for parameter in model.aligned_head.parameters():
        parameter.requires_grad_(False)

    fusion_parameters = [
        *model.gate.parameters(),
        model.modality_bias,
        *model.fusion_head.parameters(),
    ]
    optimizer = torch.optim.Adam(
        fusion_parameters,
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    dropout = float(config["modality_dropout"])
    monotonic_weight = float(config["monotonic_weight"])
    for _ in range(int(config["fusion_epochs"])):
        optimizer.zero_grad(set_to_none=True)
        tokens, available = model.aligned_tokens(clinical, modalities, active)
        full_logits = model.fuse(tokens, available)
        subset = available.clone()
        subset[:, 1:] &= torch.rand_like(subset[:, 1:].to(torch.float64)) > dropout
        subset[:, 0] = True
        subset_logits = model.fuse(tokens, subset)
        full_rows = _hazard_nll_rows(full_logits, bins, event_tensor)
        subset_rows = _hazard_nll_rows(subset_logits, bins, event_tensor)
        monotonic = torch.relu(full_rows - subset_rows).mean()
        loss = full_rows.mean() + 0.5 * subset_rows.mean() + monotonic_weight * monotonic
        loss.backward()
        torch.nn.utils.clip_grad_norm_(fusion_parameters, 5.0)
        optimizer.step()
    model.eval()
    with torch.no_grad():
        logits = model(eval_clinical, eval_modalities, eval_active)
    return _risks_from_logits(logits, edges, horizon)


def _fit_predict(
    method: str,
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    if method == "EARLY_FUSION":
        return _train_early(train, event, duration, evaluation, config, seed, horizon)
    if method == "LATE_FUSION":
        return _train_late(train, event, duration, evaluation, config, seed, horizon)
    if method == "MASKED_ATTENTION":
        return _train_attention(train, event, duration, evaluation, config, seed, horizon)
    if method == "BILINEAR_FUSION":
        return _train_bilinear(train, event, duration, evaluation, config, seed, horizon)
    if method == "RUFFINI2026":
        return _train_ruffini(train, event, duration, evaluation, config, seed, horizon)
    if method == "HAF2026":
        return _train_haf(train, event, duration, evaluation, config, seed, horizon)
    raise ValueError(f"unsupported U10 method: {method}")


def _summary(metrics: pd.DataFrame, methods: Mapping[str, object]) -> pd.DataFrame:
    metric_names = [
        "ipcw_brier_24m",
        "uno_c_24m",
        "auc_24m",
        "harrell_c",
        "calibration_in_the_large_24m",
        "calibration_slope_24m",
        "runtime_seconds",
    ]
    rows: list[dict[str, object]] = []
    for method in METHODS:
        local = metrics[metrics["method"] == method]
        metadata = methods.get(method, {})
        row: dict[str, object] = {
            "method": method,
            "label": metadata.get("label", "PATTERN-Surv-HN V1R"),
            "citation_key": metadata.get("citation_key"),
            "seeds": len(local),
            "coverage": 1.0,
        }
        for metric in metric_names:
            row[f"{metric}_mean"] = float(local[metric].mean())
            row[f"{metric}_sd"] = float(local[metric].std(ddof=1))
        rows.append(row)
    return pd.DataFrame(rows)


def run_benchmark(project_root: Path, *, verbose: bool = False) -> dict[str, object]:
    root = Path(project_root).resolve()
    spec_path = root / DEFAULT_SPEC
    spec = _load_spec(spec_path)
    horizon = float(spec["endpoint"]["horizon_days"])
    seeds = [int(value) for value in spec["cross_fitting"]["outer_repetition_seeds"]]
    methods = spec["methods"]
    contract = HancockContractBuilder(root).build()
    metadata, ids, event, duration, _ = _development_arrays(contract)
    metadata = metadata.reindex(ids)
    id_to_index = {patient_id: index for index, patient_id in enumerate(ids)}
    v1r_path = root / DEFAULT_V1R_OOF
    v1r = pd.read_csv(v1r_path, dtype={"native_id": str})
    if len(v1r) != len(ids) * len(seeds):
        raise ValueError("V1R OOF row count differs from the U10 estimand")
    output_dir = root / DEFAULT_OUTPUT
    prediction_dir = root / DEFAULT_PREDICTIONS
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_dir.mkdir(parents=True, exist_ok=True)
    metric_rows: list[dict[str, object]] = []
    prediction_rows: list[dict[str, object]] = []

    for seed in seeds:
        seed_reference = v1r[v1r["repetition_seed"] == seed]
        if set(seed_reference["native_id"]) != set(ids):
            raise RuntimeError(f"V1R reference IDs differ for seed {seed}")
        for method in METHODS[:-1]:
            oof_score = np.full(len(ids), np.nan)
            oof_risk = np.full(len(ids), np.nan)
            started = time.perf_counter()
            for fold in sorted(seed_reference["outer_fold"].unique()):
                valid_ids = seed_reference.loc[
                    seed_reference["outer_fold"] == fold, "native_id"
                ].astype(str).to_numpy()
                valid_set = set(valid_ids)
                train_ids = np.asarray([value for value in ids if value not in valid_set])
                train_indices = np.asarray([id_to_index[value] for value in train_ids], dtype=int)
                valid_indices = np.asarray([id_to_index[value] for value in valid_ids], dtype=int)
                train_features, valid_features = _prepare_features(
                    contract, metadata, train_ids, valid_ids
                )
                score, risk = _fit_predict(
                    method,
                    train_features,
                    event[train_indices],
                    duration[train_indices],
                    valid_features,
                    methods[method],
                    seed * 100 + int(fold) + 1,
                    horizon,
                )
                oof_score[valid_indices] = score
                oof_risk[valid_indices] = risk
            runtime = time.perf_counter() - started
            if not np.isfinite(oof_score).all() or not np.isfinite(oof_risk).all():
                raise RuntimeError(f"incomplete predictions for {method}, seed {seed}")
            values = evaluate_predictions(
                structured_survival(event, duration),
                structured_survival(event, duration),
                oof_score,
                oof_risk,
                horizon,
            )
            metric_rows.append(
                {"method": method, "seed": seed, "runtime_seconds": runtime, **values}
            )
            prediction_rows.extend(
                {
                    "native_id": patient_id,
                    "repetition_seed": seed,
                    "method": method,
                    "risk_score": float(oof_score[index]),
                    "risk_24m": float(oof_risk[index]),
                }
                for index, patient_id in enumerate(ids)
            )
            if verbose:
                print(
                    f"seed={seed} method={method} "
                    f"brier={values['ipcw_brier_24m']:.6f}"
                )

        ordered = seed_reference.set_index("native_id").loc[ids]
        v1r_score = ordered["v1_risk_score"].to_numpy(float)
        v1r_risk = ordered["v1_risk_24m"].to_numpy(float)
        v1r_values = evaluate_predictions(
            structured_survival(event, duration),
            structured_survival(event, duration),
            v1r_score,
            v1r_risk,
            horizon,
        )
        metric_rows.append(
            {"method": "V1R", "seed": seed, "runtime_seconds": math.nan, **v1r_values}
        )
        prediction_rows.extend(
            {
                "native_id": patient_id,
                "repetition_seed": seed,
                "method": "V1R",
                "risk_score": float(v1r_score[index]),
                "risk_24m": float(v1r_risk[index]),
            }
            for index, patient_id in enumerate(ids)
        )
        pd.DataFrame(metric_rows).to_csv(
            output_dir / "u10_metrics_checkpoint.csv", index=False
        )
        pd.DataFrame(prediction_rows).to_csv(
            prediction_dir / "u10_predictions_checkpoint.csv", index=False
        )

    metric_frame = pd.DataFrame(metric_rows)
    summary = _summary(metric_frame, methods)
    per_seed_path = output_dir / "u10_metrics_by_seed.csv"
    summary_path = output_dir / "u10_main_table_summary.csv"
    prediction_path = prediction_dir / "u10_repeated_oof_predictions.csv"
    metric_frame.to_csv(per_seed_path, index=False)
    summary.to_csv(summary_path, index=False)
    pd.DataFrame(prediction_rows).to_csv(prediction_path, index=False)
    payload = {
        "schema_version": "0.1",
        "stage_id": "U10_RECENT_COMPARATOR_BENCHMARK",
        "analysis_label": spec["analysis_label"],
        "estimand": {
            "cohort": "HANCOCK_official_training",
            "n": len(ids),
            "events": int(event.sum()),
            "horizon_days": horizon,
        },
        "methods": list(METHODS),
        "adaptation_boundary": spec["adaptation_boundary"],
        "seeds": seeds,
        "outer_folds": int(spec["cross_fitting"]["outer_folds"]),
        "governance": spec["governance"],
        "spec_sha256": _sha256(spec_path),
        "v1r_oof_sha256": _sha256(v1r_path),
        "outputs": {
            "metrics_by_seed": str(per_seed_path.relative_to(root)).replace("\\", "/"),
            "main_table_summary": str(summary_path.relative_to(root)).replace("\\", "/"),
            "patient_predictions": str(prediction_path.relative_to(root)).replace("\\", "/"),
        },
        "summary": summary.to_dict(orient="records"),
    }
    audit_path = output_dir / "aggregate_u10_recent_comparator_benchmark_audit.json"
    audit_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "u10_metrics_checkpoint.csv").unlink(missing_ok=True)
    (prediction_dir / "u10_predictions_checkpoint.csv").unlink(missing_ok=True)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    run_benchmark(args.project_root, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
