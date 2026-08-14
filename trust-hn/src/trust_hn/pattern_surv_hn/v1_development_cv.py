"""Development-only nested cross-validation for PATTERN-Surv-HN V1.

Uses eligible HANCOCK official-training records only. Every learned transform is fold-bound;
patient OOF output is git-ignored; official-test and external outcomes remain sealed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from torch import Tensor

from trust_hn.pattern_surv_hn.hancock_contract import (
    ANCHOR_CATEGORICAL_FEATURES,
    ANCHOR_NUMERIC_FEATURES,
    BLOOD_FEATURES,
    ICD_FEATURES,
    TMA_FEATURES,
    FoldBoundBlockPreprocessor,
    FoldBoundMixedPreprocessor,
    HancockContract,
    HancockContractBuilder,
)
from trust_hn.pattern_surv_hn.v0_clinical_anchor import (
    CoxnetCandidate,
    V0Spec,
    _development_arrays,
    _event_stratified_splits,
    _fit_anchor,
    _predict_anchor,
    _prepare_inner_folds,
    _select_candidate,
    assert_aggregate_only,
    evaluate_predictions,
    structured_survival,
)
from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import (
    MODALITY_ORDER,
    STATUS_LEVELS,
    V1SmokeSpec,
)
from trust_hn.pattern_surv_hn.v1_trainable_smoke import (
    TorchModalityBatch,
    TrainableClinicalResidualDeepSetsCox,
)

ANALYSIS_DATE = "2026-08-14"
MODEL_ID = "V1"
MODEL_NAME = "Clinical_Residual_Deep_Sets_Cox"
DEFAULT_SPEC_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U2_V1_development_cv/frozen_u2_v1_development_cv_spec.yaml"
)
DEFAULT_GATE_RELATIVE = DEFAULT_SPEC_RELATIVE.parent / "frozen_v0_v1_complexity_gate.yaml"
DEFAULT_AUDIT_RELATIVE = DEFAULT_SPEC_RELATIVE.parent / "aggregate_u2_v1_development_cv_audit.json"
DEFAULT_V0_SPEC_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U1_2_V0_clinical_anchor/frozen_v0_spec.yaml"
)
DEFAULT_ARCHITECTURE_SPEC_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U1_3_V1_smoke/frozen_v1_smoke_spec.yaml"
)
DEFAULT_V0_OOF_RELATIVE = Path(
    "results/predictions/pattern_surv_hn/U1_2_V0/"
    "v0_repeated_nested_oof_predictions.csv"
)
DEFAULT_PATIENT_OUTPUT_RELATIVE = Path("results/predictions/pattern_surv_hn/U2_V1")
MODALITY_FEATURES = {"blood": BLOOD_FEATURES, "icd": ICD_FEATURES, "tma": TMA_FEATURES}


@dataclass(frozen=True)
class U2Spec:
    horizon_days: float
    outer_folds: int
    outer_repetition_seeds: tuple[int, ...]
    inner_folds: int
    residual_penalty_grid: tuple[float, ...]
    checkpoint_steps: tuple[int, ...]
    learning_rate: float
    weight_decay: float
    gradient_clip_norm: float
    pattern_minimum_n: int
    pattern_minimum_events: int
    expected_n: int
    expected_events: int
    deterministic_algorithms: bool

    @classmethod
    def from_yaml(cls, path: Path) -> U2Spec:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
        cross, select = payload["cross_fitting"], payload["inner_selection"]
        optim = payload["optimization"]
        support, population = payload["evaluation"]["pattern_metric_support"], payload["population"]
        spec = cls(
            float(payload["endpoint"]["horizon_days"]), int(cross["outer_folds"]),
            tuple(int(v) for v in cross["outer_repetition_seeds"]), int(cross["inner_folds"]),
            tuple(float(v) for v in select["residual_penalty_grid"]),
            tuple(int(v) for v in select["checkpoint_steps"]),
            float(optim["learning_rate"]), float(optim["weight_decay"]),
            float(optim["gradient_clip_norm"]), int(support["minimum_n"]),
            int(support["minimum_events"]), int(population["expected_n"]),
            int(population["expected_events"]), bool(optim["deterministic_algorithms"]),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if self.horizon_days <= 0 or self.outer_folds < 2 or self.inner_folds < 2:
            raise ValueError("invalid U2 horizon/fold specification")
        if not self.outer_repetition_seeds or not self.residual_penalty_grid:
            raise ValueError("U2 requires seeds and residual penalties")
        if any(v < 0 for v in self.residual_penalty_grid):
            raise ValueError("residual penalties must be nonnegative")
        if not self.checkpoint_steps or self.checkpoint_steps[0] != 0:
            raise ValueError("checkpoint_steps must start at zero")
        if tuple(sorted(set(self.checkpoint_steps))) != self.checkpoint_steps:
            raise ValueError("checkpoint_steps must be unique and increasing")
        if self.learning_rate <= 0 or self.weight_decay < 0 or self.gradient_clip_norm <= 0:
            raise ValueError("invalid optimizer settings")


@dataclass(frozen=True)
class FoldTensorInputs:
    clinical_score: Tensor
    modalities: tuple[TorchModalityBatch, ...]
    duration: Tensor
    event: Tensor


@dataclass(frozen=True)
class CoxLossPlan:
    order: Tensor
    group_index: Tensor
    group_end_index: Tensor
    event_count: Tensor
    event_sorted: Tensor


@dataclass(frozen=True)
class SelectedV1Candidate:
    residual_penalty: float
    optimization_steps: int


@dataclass(frozen=True)
class FittedV1:
    model: TrainableClinicalResidualDeepSetsCox
    initial_cox_loss: float
    final_cox_loss: float
    final_total_loss: float


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _make_cox_loss_plan(duration: Tensor, event: Tensor) -> CoxLossPlan:
    if duration.ndim != 1 or event.shape != duration.shape or duration.numel() < 2:
        raise ValueError("duration and event must be equal-length vectors")
    if not bool(torch.all(torch.isfinite(duration))) or bool(torch.any(duration <= 0)):
        raise ValueError("duration must be finite and positive")
    if not bool(event.bool().any()):
        raise ValueError("at least one event is required")
    order = torch.argsort(duration, descending=True, stable=True)
    duration_sorted = duration[order]
    event_sorted = event[order].to(torch.float64)
    new_group = torch.ones(duration.numel(), dtype=torch.bool)
    new_group[1:] = duration_sorted[1:] != duration_sorted[:-1]
    group_index = torch.cumsum(new_group.to(torch.long), dim=0) - 1
    group_count = int(group_index[-1]) + 1
    group_end = torch.cat(
        [duration_sorted[:-1] != duration_sorted[1:], torch.ones(1, dtype=torch.bool)]
    )
    group_end_index = torch.nonzero(group_end, as_tuple=False).squeeze(1)
    event_count = torch.zeros(group_count, dtype=torch.float64)
    event_count.scatter_add_(0, group_index, event_sorted)
    return CoxLossPlan(order, group_index, group_end_index, event_count, event_sorted)


def _negative_breslow_cox_loss(score: Tensor, plan: CoxLossPlan) -> Tensor:
    if score.ndim != 1 or score.numel() != plan.order.numel():
        raise ValueError("score length differs from Cox plan")
    sorted_score = score[plan.order]
    event_score = torch.zeros(plan.event_count.numel(), dtype=score.dtype)
    event_score.scatter_add_(
        0, plan.group_index, sorted_score * plan.event_sorted.to(dtype=score.dtype)
    )
    log_risk = torch.logcumsumexp(sorted_score, dim=0)[plan.group_end_index]
    event_count = plan.event_count.to(dtype=score.dtype)
    active = event_count > 0
    return -(event_score[active] - event_count[active] * log_risk[active]).sum() / event_count.sum()


def breslow_risk_at_horizon(
    train_duration: Sequence[float], train_event: Sequence[bool],
    train_score: Sequence[float], eval_score: Sequence[float], horizon: float,
) -> np.ndarray:
    duration, event = np.asarray(train_duration, float), np.asarray(train_event, bool)
    score, evaluation_score = np.asarray(train_score, float), np.asarray(eval_score, float)
    if duration.shape != event.shape or duration.shape != score.shape:
        raise ValueError("Breslow training lengths differ")
    if np.any(~np.isfinite(duration)) or np.any(duration <= 0):
        raise ValueError("training durations must be finite and positive")
    if np.any(~np.isfinite(score)) or np.any(~np.isfinite(evaluation_score)):
        raise ValueError("Breslow scores must be finite")
    event_times = np.unique(duration[event & (duration <= horizon)])
    if not event_times.size:
        return np.zeros(evaluation_score.shape, dtype=float)
    center = float(np.max(score))
    relative_hazard = np.exp(np.clip(score - center, -50.0, 50.0))
    cumulative_hazard = 0.0
    for event_time in event_times:
        deaths = int(np.sum(event & (duration == event_time)))
        denominator = float(np.sum(relative_hazard[duration >= event_time]))
        if denominator <= 0 or not math.isfinite(denominator):
            raise RuntimeError("invalid Breslow denominator")
        cumulative_hazard += deaths / denominator
    eval_hazard = np.exp(np.clip(evaluation_score - center, -50.0, 50.0))
    return np.clip(1.0 - np.exp(-cumulative_hazard * eval_hazard), 0.0, 1.0)


def _new_model(architecture: V1SmokeSpec) -> TrainableClinicalResidualDeepSetsCox:
    model = TrainableClinicalResidualDeepSetsCox(architecture)
    with torch.no_grad():
        model.rho[-1].weight.zero_()
        model.rho[-1].bias.zero_()
    return model


def _to_tensor_inputs(clinical, modalities, duration, event) -> FoldTensorInputs:
    return FoldTensorInputs(
        torch.as_tensor(clinical, dtype=torch.float64), modalities,
        torch.as_tensor(duration, dtype=torch.float64), torch.as_tensor(event, dtype=torch.bool),
    )


def _fit_modality_preprocessors(contract, metadata, training_ids, evaluation_ids):
    training_batches, evaluation_batches, audit = [], [], {}
    for name in MODALITY_ORDER:
        frame = getattr(contract, name).reindex(metadata.index)
        features = MODALITY_FEATURES[name]
        prep = FoldBoundBlockPreprocessor(
            features, add_missing_indicators=True, allowed_fit_ids=set(training_ids)
        )
        train_block = prep.fit_transform(frame, training_ids)
        eval_block = prep.transform(frame, evaluation_ids)
        if tuple(prep.fit_ids_) != tuple(str(v) for v in training_ids):
            raise RuntimeError("modality preprocessor fit-ID audit failed")
        expected_width = 2 * len(features)
        if train_block.values.shape[1] != expected_width:
            raise RuntimeError(f"{name} preprocessing width differs from contract")

        def make_batch(ids, values, modality_name=name):
            subset = metadata.loc[list(ids)]
            missing = subset[f"{modality_name}_missing_fraction"].to_numpy(dtype=float)
            quality = np.column_stack([missing, 1.0 - missing])
            status = [STATUS_LEVELS.index(str(v)) for v in subset[f"{modality_name}_status"]]
            return TorchModalityBatch(
                modality_name, torch.as_tensor(values, dtype=torch.float64),
                torch.as_tensor(subset[f"{modality_name}_usable"].to_numpy(bool), dtype=torch.bool),
                torch.as_tensor(status, dtype=torch.long),
                torch.as_tensor(quality, dtype=torch.float64),
            )

        training_batches.append(make_batch(training_ids, train_block.values))
        evaluation_batches.append(make_batch(evaluation_ids, eval_block.values))
        audit[name] = {
            "fit_n": len(prep.fit_ids_), "output_width": expected_width,
            "training_active_n": int(training_batches[-1].active.sum()),
            "validation_active_n": int(evaluation_batches[-1].active.sum()),
        }
    return tuple(training_batches), tuple(evaluation_batches), audit


def _fit_anchor_for_split(
    contract, training_ids, evaluation_ids, training_event, training_time,
    candidate, v0_spec,
):
    prep = FoldBoundMixedPreprocessor(
        numeric=ANCHOR_NUMERIC_FEATURES, categorical=ANCHOR_CATEGORICAL_FEATURES,
        allowed_fit_ids=set(training_ids.tolist()),
    )
    train_block = prep.fit_transform(contract.anchor, training_ids.tolist())
    eval_block = prep.transform(contract.anchor, evaluation_ids.tolist())
    if tuple(prep.fit_ids_) != tuple(training_ids.tolist()):
        raise RuntimeError("clinical preprocessor fit-ID audit failed")
    y_train = structured_survival(training_event, training_time)
    fitted = _fit_anchor(
        train_block.values, y_train, candidate, v0_spec, train_block.feature_names
    )
    train_score = np.asarray(fitted.model.predict(train_block.values), dtype=float)
    eval_score, eval_risk = _predict_anchor(fitted, eval_block.values, v0_spec.horizon_days)
    return train_score, eval_score, eval_risk, {
        "clinical_fit_n": len(prep.fit_ids_),
        "clinical_encoded_feature_count": int(train_block.values.shape[1]),
    }


def _predict_model(model, inputs):
    model.eval()
    with torch.no_grad():
        forward = model(inputs.clinical_score, inputs.modalities)
    return (
        forward.fused_score.numpy(), forward.residual_score.numpy(),
        forward.active_token_count.numpy(),
    )


def _fit_v1(architecture, inputs, spec, candidate):
    model = _new_model(architecture)
    plan = _make_cox_loss_plan(inputs.duration, inputs.event)
    with torch.no_grad():
        initial = model(inputs.clinical_score, inputs.modalities)
        initial_loss = float(_negative_breslow_cox_loss(initial.fused_score, plan))
    optimizer = torch.optim.Adam(
        model.parameters(), lr=spec.learning_rate, weight_decay=spec.weight_decay
    )
    final_total = initial_loss
    for _ in range(candidate.optimization_steps):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        forward = model(inputs.clinical_score, inputs.modalities)
        cox = _negative_breslow_cox_loss(forward.fused_score, plan)
        loss = cox + candidate.residual_penalty * torch.mean(forward.residual_score.square())
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), spec.gradient_clip_norm)
        optimizer.step()
        final_total = float(loss.detach())
    model.eval()
    with torch.no_grad():
        final = model(inputs.clinical_score, inputs.modalities)
        final_cox = float(_negative_breslow_cox_loss(final.fused_score, plan))
    return FittedV1(model, initial_loss, final_cox, final_total)


def _inner_select_v1(
    contract, metadata, outer_ids, outer_event, outer_time, anchor_candidate,
    v0_spec, architecture, spec, seed,
):
    values = defaultdict(list)
    max_steps = max(spec.checkpoint_steps)
    for train_idx, valid_idx in _event_stratified_splits(
        outer_event, spec.inner_folds, seed
    ):
        train_ids, valid_ids = outer_ids[train_idx], outer_ids[valid_idx]
        train_event, valid_event = outer_event[train_idx], outer_event[valid_idx]
        train_time, valid_time = outer_time[train_idx], outer_time[valid_idx]
        train_clinical, valid_clinical, _, _ = _fit_anchor_for_split(
            contract, train_ids, valid_ids, train_event, train_time,
            anchor_candidate, v0_spec,
        )
        train_modalities, valid_modalities, _ = _fit_modality_preprocessors(
            contract, metadata, train_ids.tolist(), valid_ids.tolist()
        )
        train_inputs = _to_tensor_inputs(
            train_clinical, train_modalities, train_time, train_event
        )
        valid_inputs = _to_tensor_inputs(
            valid_clinical, valid_modalities, valid_time, valid_event
        )
        train_y = structured_survival(train_event, train_time)
        valid_y = structured_survival(valid_event, valid_time)
        plan = _make_cox_loss_plan(train_inputs.duration, train_inputs.event)
        for penalty in spec.residual_penalty_grid:
            model = _new_model(architecture)
            optimizer = torch.optim.Adam(
                model.parameters(), lr=spec.learning_rate, weight_decay=spec.weight_decay
            )
            checkpoints = set(spec.checkpoint_steps)
            for step in range(max_steps + 1):
                if step in checkpoints:
                    train_score, _, _ = _predict_model(model, train_inputs)
                    valid_score, _, _ = _predict_model(model, valid_inputs)
                    valid_risk = breslow_risk_at_horizon(
                        train_time, train_event, train_score, valid_score, spec.horizon_days
                    )
                    values[(penalty, step)].append(
                        evaluate_predictions(
                            train_y, valid_y, valid_score, valid_risk, spec.horizon_days
                        )
                    )
                if step == max_steps:
                    break
                model.train()
                optimizer.zero_grad(set_to_none=True)
                forward = model(train_inputs.clinical_score, train_inputs.modalities)
                cox = _negative_breslow_cox_loss(forward.fused_score, plan)
                loss = cox + penalty * torch.mean(forward.residual_score.square())
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), spec.gradient_clip_norm)
                optimizer.step()

    rows = []
    for (penalty, steps), metrics in sorted(values.items()):
        brier = np.asarray([row["ipcw_brier_24m"] for row in metrics], float)
        uno = np.asarray([row["uno_c_24m"] for row in metrics], float)
        rows.append({
            "residual_penalty": float(penalty),
            "optimization_steps": float(steps),
            "mean_inner_ipcw_brier_24m": float(np.mean(brier)),
            "mean_inner_uno_c_24m": (
                float(np.mean(uno[np.isfinite(uno)])) if np.isfinite(uno).any() else -math.inf
            ),
            "successful_inner_folds": float(len(metrics)),
        })
    valid_rows = [row for row in rows if row["successful_inner_folds"] == spec.inner_folds]
    if not valid_rows:
        raise RuntimeError("no V1 candidate completed all inner folds")
    winner = min(valid_rows, key=lambda row: (
        row["mean_inner_ipcw_brier_24m"], -row["mean_inner_uno_c_24m"],
        -row["residual_penalty"], row["optimization_steps"],
    ))
    selected = SelectedV1Candidate(
        float(winner["residual_penalty"]), int(winner["optimization_steps"])
    )
    return selected, rows


def _load_v0_reference(path, expected_sha256=None):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"frozen V0 OOF reference is missing: {path}")
    if expected_sha256 is not None and _sha256(path) != expected_sha256:
        raise RuntimeError("frozen V0 OOF SHA256 differs from U2 spec")
    frame = pd.read_csv(path, dtype={"native_id": str, "acquisition_pattern": str})
    required = {
        "native_id", "repetition_seed", "outer_fold", "risk_score", "risk_24m",
        "selected_alpha", "selected_l1_ratio",
    }
    if not required.issubset(frame.columns):
        raise ValueError("V0 OOF reference lacks paired-comparison columns")
    return frame


def _reference_candidate(reference, repetition_seed, outer_fold, validation_ids):
    group = reference[
        (reference["repetition_seed"] == repetition_seed)
        & (reference["outer_fold"] == outer_fold)
    ].copy()
    if set(group["native_id"].astype(str)) != set(validation_ids.tolist()):
        raise RuntimeError("V0 reference IDs do not match regenerated outer fold")
    candidates = group[["selected_alpha", "selected_l1_ratio"]].drop_duplicates()
    if len(candidates) != 1:
        raise RuntimeError("V0 fold has nonunique selected candidate")
    row = candidates.iloc[0]
    return CoxnetCandidate(float(row["selected_alpha"]), float(row["selected_l1_ratio"])), group


def _fallback_errors(model, inputs):
    inactive = tuple(
        TorchModalityBatch(
            batch.name, torch.full_like(batch.content, torch.nan),
            torch.zeros_like(batch.active),
            torch.full_like(batch.status_index, STATUS_LEVELS.index("absent")),
            torch.column_stack([
                torch.ones(inputs.clinical_score.numel(), dtype=torch.float64),
                torch.zeros(inputs.clinical_score.numel(), dtype=torch.float64),
            ]),
        )
        for batch in inputs.modalities
    )
    model.eval()
    with torch.no_grad():
        result = model(inputs.clinical_score, inactive)
    return (
        float(torch.max(torch.abs(result.residual_score))),
        float(torch.max(torch.abs(result.fused_score - inputs.clinical_score))),
    )


def _select_anchor_without_reference(contract, ids, event, time, v0_spec, seed):
    prepared = _prepare_inner_folds(contract.anchor, ids, event, time, v0_spec, seed)
    selected, _ = _select_candidate(prepared, v0_spec)
    return selected


def development_cross_fit(
    contract: HancockContract, spec: U2Spec, v0_spec: V0Spec,
    architecture: V1SmokeSpec, *, v0_reference: pd.DataFrame | None,
    verbose: bool = False,
):
    development, ids, event, time, patterns = _development_arrays(contract)
    if len(ids) != spec.expected_n or int(event.sum()) != spec.expected_events:
        raise RuntimeError("development estimand differs from frozen U2 contract")
    if spec.horizon_days != v0_spec.horizon_days:
        raise RuntimeError("U2 and V0 horizons differ")
    metadata = contract.patient_frame().set_index("native_id")
    sealed = metadata[metadata["official_partition"] == "test"]
    if sealed["duration_days"].notna().any() or sealed["event"].notna().any():
        raise RuntimeError("official-test outcomes were exposed")

    rows, fold_audit = [], []
    selection_counter, anchor_counter = Counter(), Counter()
    parameter_count = _new_model(architecture).parameter_count
    for repetition_seed in spec.outer_repetition_seeds:
        seen = []
        splits = _event_stratified_splits(event, spec.outer_folds, repetition_seed)
        for outer_fold, (train_idx, valid_idx) in enumerate(splits):
            train_ids, valid_ids = ids[train_idx], ids[valid_idx]
            if v0_reference is not None:
                anchor_candidate, reference_fold = _reference_candidate(
                    v0_reference, repetition_seed, outer_fold, valid_ids
                )
            else:
                anchor_candidate = _select_anchor_without_reference(
                    contract, train_ids, event[train_idx], time[train_idx], v0_spec,
                    repetition_seed * 100 + outer_fold + 1,
                )
                reference_fold = pd.DataFrame()
            anchor_counter[(anchor_candidate.alpha, anchor_candidate.l1_ratio)] += 1
            selected, inner_rows = _inner_select_v1(
                contract, metadata, train_ids, event[train_idx], time[train_idx],
                anchor_candidate, v0_spec, architecture, spec,
                repetition_seed * 100 + outer_fold + 1,
            )
            selection_counter[(selected.residual_penalty, selected.optimization_steps)] += 1
            train_clinical, valid_clinical, valid_v0_risk, anchor_audit = (
                _fit_anchor_for_split(
                    contract, train_ids, valid_ids, event[train_idx], time[train_idx],
                    anchor_candidate, v0_spec,
                )
            )
            reference_score_error = reference_risk_error = 0.0
            if not reference_fold.empty:
                aligned_ref = reference_fold.set_index("native_id").loc[valid_ids]
                reference_score_error = float(np.max(np.abs(
                    valid_clinical - aligned_ref["risk_score"].to_numpy(float)
                )))
                reference_risk_error = float(np.max(np.abs(
                    valid_v0_risk - aligned_ref["risk_24m"].to_numpy(float)
                )))
                if reference_score_error > 1e-10 or reference_risk_error > 1e-10:
                    raise RuntimeError("refitted V0 differs from frozen OOF reference")
            train_modalities, valid_modalities, modality_audit = (
                _fit_modality_preprocessors(
                    contract, metadata, train_ids.tolist(), valid_ids.tolist()
                )
            )
            train_inputs = _to_tensor_inputs(
                train_clinical, train_modalities, time[train_idx], event[train_idx]
            )
            valid_inputs = _to_tensor_inputs(
                valid_clinical, valid_modalities, time[valid_idx], event[valid_idx]
            )
            fitted = _fit_v1(architecture, train_inputs, spec, selected)
            train_fused, _, _ = _predict_model(fitted.model, train_inputs)
            valid_fused, valid_residual, valid_active_count = _predict_model(
                fitted.model, valid_inputs
            )
            valid_v1_risk = breslow_risk_at_horizon(
                time[train_idx], event[train_idx], train_fused, valid_fused,
                spec.horizon_days,
            )
            fallback_residual_error, fallback_fused_error = _fallback_errors(
                fitted.model, valid_inputs
            )
            y_train = structured_survival(event[train_idx], time[train_idx])
            y_valid = structured_survival(event[valid_idx], time[valid_idx])
            fold_v0 = evaluate_predictions(
                y_train, y_valid, valid_clinical, valid_v0_risk, spec.horizon_days
            )
            fold_v1 = evaluate_predictions(
                y_train, y_valid, valid_fused, valid_v1_risk, spec.horizon_days
            )
            best_inner = next(
                row for row in inner_rows
                if row["residual_penalty"] == selected.residual_penalty
                and int(row["optimization_steps"]) == selected.optimization_steps
            )
            fold_audit.append({
                "repetition_seed": repetition_seed, "outer_fold": outer_fold,
                "train_n": len(train_idx), "train_events": int(event[train_idx].sum()),
                "validation_n": len(valid_idx),
                "validation_events": int(event[valid_idx].sum()),
                "selected_anchor_alpha": anchor_candidate.alpha,
                "selected_anchor_l1_ratio": anchor_candidate.l1_ratio,
                "selected_residual_penalty": selected.residual_penalty,
                "selected_optimization_steps": selected.optimization_steps,
                "selected_inner_ipcw_brier_24m": best_inner["mean_inner_ipcw_brier_24m"],
                "selected_inner_uno_c_24m": best_inner["mean_inner_uno_c_24m"],
                "initial_training_cox_loss": fitted.initial_cox_loss,
                "final_training_cox_loss": fitted.final_cox_loss,
                "reference_v0_score_max_abs_error": reference_score_error,
                "reference_v0_risk_max_abs_error": reference_risk_error,
                "fallback_residual_max_abs_error": fallback_residual_error,
                "fallback_fused_max_abs_error": fallback_fused_error,
                "clinical_preprocessing": anchor_audit,
                "modality_preprocessing": modality_audit,
                "V0_metrics": fold_v0, "V1_metrics": fold_v1,
            })
            for local, global_index in enumerate(valid_idx):
                native_id = str(ids[global_index])
                seen.append(native_id)
                rows.append({
                    "native_id": native_id, "repetition_seed": repetition_seed,
                    "outer_fold": outer_fold, "duration_days": float(time[global_index]),
                    "event": int(event[global_index]),
                    "acquisition_pattern": str(patterns[global_index]),
                    "usable_pattern": str(development.iloc[global_index]["usable_pattern"]),
                    "v0_risk_score": float(valid_clinical[local]),
                    "v0_risk_24m": float(valid_v0_risk[local]),
                    "v1_residual_score": float(valid_residual[local]),
                    "v1_risk_score": float(valid_fused[local]),
                    "v1_risk_24m": float(valid_v1_risk[local]),
                    "v1_survival_24m": float(1.0 - valid_v1_risk[local]),
                    "active_token_count": int(valid_active_count[local]),
                    "selected_residual_penalty": selected.residual_penalty,
                    "selected_optimization_steps": selected.optimization_steps,
                })
            if verbose:
                print(
                    f"seed={repetition_seed} fold={outer_fold} "
                    f"penalty={selected.residual_penalty:g} steps={selected.optimization_steps}",
                    flush=True,
                )
        if len(seen) != len(ids) or len(seen) != len(set(seen)) or set(seen) != set(ids):
            raise RuntimeError(f"V1 OOF coverage failed for seed {repetition_seed}")

    oof = pd.DataFrame(rows).sort_values(
        ["repetition_seed", "outer_fold", "native_id"], ignore_index=True
    )
    full_y = structured_survival(event, time)
    id_to_index = {native_id: index for index, native_id in enumerate(ids)}
    per_seed, pattern_rows = [], []
    for repetition_seed, group in oof.groupby("repetition_seed", sort=True):
        aligned = group.set_index("native_id").loc[ids]
        v0_metrics = evaluate_predictions(
            full_y, full_y, aligned["v0_risk_score"].to_numpy(float),
            aligned["v0_risk_24m"].to_numpy(float), spec.horizon_days,
        )
        v1_metrics = evaluate_predictions(
            full_y, full_y, aligned["v1_risk_score"].to_numpy(float),
            aligned["v1_risk_24m"].to_numpy(float), spec.horizon_days,
        )
        metric_names = (
            "ipcw_brier_24m", "harrell_c", "uno_c_24m", "auc_24m",
            "calibration_in_the_large_24m", "calibration_slope_24m",
            "mean_predicted_risk_24m",
        )
        deltas = {key: float(v1_metrics[key] - v0_metrics[key]) for key in metric_names}
        per_seed.append({
            "repetition_seed": int(repetition_seed), "V0": v0_metrics,
            "V1": v1_metrics, "delta_V1_minus_V0": deltas,
        })
        for pattern, pattern_group in aligned.groupby("acquisition_pattern", sort=True):
            indices = np.asarray([id_to_index[str(v)] for v in pattern_group.index])
            n, events = len(pattern_group), int(event[indices].sum())
            supported = n >= spec.pattern_minimum_n and events >= spec.pattern_minimum_events
            record = {
                "repetition_seed": int(repetition_seed), "acquisition_pattern": str(pattern),
                "n": n, "events": events, "metric_support": supported,
                "interpretation": (
                    "supported_exploratory" if supported else "descriptive_counts_only"
                ),
            }
            if supported:
                pattern_y = structured_survival(event[indices], time[indices])
                v0_pattern = evaluate_predictions(
                    full_y, pattern_y, pattern_group["v0_risk_score"].to_numpy(float),
                    pattern_group["v0_risk_24m"].to_numpy(float), spec.horizon_days,
                )
                v1_pattern = evaluate_predictions(
                    full_y, pattern_y, pattern_group["v1_risk_score"].to_numpy(float),
                    pattern_group["v1_risk_24m"].to_numpy(float), spec.horizon_days,
                )
                record.update({
                    "V0": v0_pattern, "V1": v1_pattern,
                    "delta_V1_minus_V0": {
                        "ipcw_brier_24m": float(
                            v1_pattern["ipcw_brier_24m"] - v0_pattern["ipcw_brier_24m"]
                        ),
                        "uno_c_24m": float(
                            v1_pattern["uno_c_24m"] - v0_pattern["uno_c_24m"]
                        ),
                    },
                })
            pattern_rows.append(record)

    metric_names = (
        "ipcw_brier_24m", "harrell_c", "uno_c_24m", "auc_24m",
        "calibration_in_the_large_24m", "calibration_slope_24m",
        "mean_predicted_risk_24m",
    )
    summary = {}
    for metric in metric_names:
        v0_values = np.asarray([row["V0"][metric] for row in per_seed], float)
        v1_values = np.asarray([row["V1"][metric] for row in per_seed], float)
        delta = v1_values - v0_values
        summary[metric] = {
            "V0_mean": float(np.nanmean(v0_values)),
            "V1_mean": float(np.nanmean(v1_values)),
            "mean_delta_V1_minus_V0": float(np.nanmean(delta)),
            "delta_sample_sd": (
                float(np.nanstd(delta, ddof=1)) if np.isfinite(delta).sum() > 1 else 0.0
            ),
            "V1_better_seed_count": int(
                np.sum(delta < 0) if metric == "ipcw_brier_24m" else np.sum(delta > 0)
            ),
        }
    aggregate = {
        "folds": fold_audit, "per_seed_metrics": per_seed,
        "across_seed_summary": summary, "pattern_stratified_metrics": pattern_rows,
        "v1_selection_frequency": [
            {"residual_penalty": penalty, "optimization_steps": steps,
             "outer_fold_count": count}
            for (penalty, steps), count in sorted(selection_counter.items())
        ],
        "anchor_selection_frequency": [
            {"alpha": alpha, "l1_ratio": ratio, "outer_fold_count": count}
            for (alpha, ratio), count in sorted(anchor_counter.items())
        ],
        "parameter_count": parameter_count,
    }
    return oof, aggregate


def apply_complexity_gate(oof, aggregate, gate_payload):
    per_seed = aggregate["per_seed_metrics"]
    patterns, folds = aggregate["pattern_stratified_metrics"], aggregate["folds"]
    expected_rows = oof["native_id"].nunique() * len(per_seed)
    finite_v0 = np.isfinite(oof[["v0_risk_score", "v0_risk_24m"]]).all(axis=1)
    finite_v1 = np.isfinite(oof[["v1_risk_score", "v1_risk_24m"]]).all(axis=1)
    v0_coverage = float(finite_v0.sum() / expected_rows)
    v1_coverage = float(finite_v1.sum() / expected_rows)
    coverage_spec = gate_payload["coverage_gate"]
    coverage_pass = (
        v0_coverage == float(coverage_spec["required_V0_coverage"])
        and v1_coverage == float(coverage_spec["required_V1_coverage"])
    )
    max_residual_error = max(float(row["fallback_residual_max_abs_error"]) for row in folds)
    max_fused_error = max(float(row["fallback_fused_max_abs_error"]) for row in folds)
    structural_spec = gate_payload["structural_gate"]
    structural_pass = (
        max_residual_error <= float(structural_spec["exact_empty_set_residual_max_abs_error"])
        and max_fused_error <= float(structural_spec["exact_clinical_fallback_max_abs_error"])
        and int(aggregate["parameter_count"]) <= int(structural_spec["parameter_ceiling"])
    )
    brier_deltas = np.asarray([
        row["delta_V1_minus_V0"]["ipcw_brier_24m"] for row in per_seed
    ], float)
    uno_deltas = np.asarray([
        row["delta_V1_minus_V0"]["uno_c_24m"] for row in per_seed
    ], float)
    v0_citl = np.asarray([row["V0"]["calibration_in_the_large_24m"] for row in per_seed], float)
    v1_citl = np.asarray([row["V1"]["calibration_in_the_large_24m"] for row in per_seed], float)
    v0_slope = np.asarray([row["V0"]["calibration_slope_24m"] for row in per_seed], float)
    v1_slope = np.asarray([row["V1"]["calibration_slope_24m"] for row in per_seed], float)
    citl_deterioration = float(np.nanmean(np.abs(v1_citl)) - np.nanmean(np.abs(v0_citl)))
    slope_deterioration = float(
        np.nanmean(np.abs(v1_slope - 1.0)) - np.nanmean(np.abs(v0_slope - 1.0))
    )
    supported_regrets = [
        float(row["delta_V1_minus_V0"]["ipcw_brier_24m"])
        for row in patterns if row["metric_support"]
    ]
    worst_regret = max(supported_regrets) if supported_regrets else math.nan
    safety_spec = gate_payload["safety_gate"]
    safety_checks = {
        "overall_brier_noninferiority": float(np.mean(brier_deltas))
        <= float(safety_spec["mean_delta_IPCW_Brier_24m_maximum"]),
        "supported_pattern_regret": bool(supported_regrets)
        and worst_regret <= float(safety_spec["supported_pattern_worst_Brier_regret_maximum"]),
        "calibration_in_the_large": citl_deterioration
        <= float(safety_spec["mean_absolute_CITL_deterioration_maximum"]),
        "calibration_slope": slope_deterioration
        <= float(safety_spec["mean_absolute_calibration_slope_error_deterioration_maximum"]),
    }
    safety_pass = all(safety_checks.values())
    paths = []
    for path in gate_payload["incremental_value_gate"]["qualifying_paths"]:
        if path["name"] == "probability_error":
            effect_pass = float(np.mean(brier_deltas)) <= float(
                path["mean_delta_IPCW_Brier_24m_maximum"]
            )
            direction_count = int(np.sum(brier_deltas < 0))
        elif path["name"] == "discrimination":
            effect_pass = float(np.mean(uno_deltas)) >= float(
                path["mean_delta_Uno_C_24m_minimum"]
            )
            direction_count = int(np.sum(uno_deltas > 0))
        else:
            raise ValueError(f"unknown incremental-value path: {path['name']}")
        stability_pass = direction_count >= int(path["minimum_supporting_seeds"])
        paths.append({
            "name": path["name"], "effect_size_pass": effect_pass,
            "supporting_seed_count": direction_count,
            "seed_stability_pass": stability_pass,
            "path_pass": effect_pass and stability_pass,
        })
    incremental_pass = any(row["path_pass"] for row in paths)
    earns = coverage_pass and structural_pass and safety_pass and incremental_pass
    return {
        "decision": "V1_EARNS_COMPLEXITY" if earns else "V1_DOES_NOT_EARN_COMPLEXITY",
        "coverage": {"V0": v0_coverage, "V1": v1_coverage, "pass": coverage_pass},
        "structural": {
            "fallback_residual_max_abs_error": max_residual_error,
            "fallback_fused_max_abs_error": max_fused_error,
            "parameter_count": int(aggregate["parameter_count"]), "pass": structural_pass,
        },
        "safety": {
            "mean_delta_IPCW_Brier_24m": float(np.mean(brier_deltas)),
            "supported_pattern_worst_Brier_regret": worst_regret,
            "mean_absolute_CITL_deterioration": citl_deterioration,
            "mean_absolute_calibration_slope_error_deterioration": slope_deterioration,
            "checks": safety_checks, "pass": safety_pass,
        },
        "incremental_value": {
            "mean_delta_Uno_C_24m": float(np.mean(uno_deltas)),
            "paths": paths, "pass": incremental_pass,
        },
        "all_required_gates_pass": earns,
    }


def _json_safe(value):
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating | float):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def run_u2_experiment(
    project_root: Path, *, spec_path: Path | None = None,
    gate_path: Path | None = None, v0_spec_path: Path | None = None,
    architecture_spec_path: Path | None = None, v0_oof_path: Path | None = None,
    patient_output_dir: Path | None = None,
    aggregate_audit_path: Path | None = None, verbose: bool = False,
):
    root = Path(project_root).resolve()
    spec_path = Path(spec_path or root / DEFAULT_SPEC_RELATIVE).resolve()
    gate_path = Path(gate_path or root / DEFAULT_GATE_RELATIVE).resolve()
    v0_spec_path = Path(v0_spec_path or root / DEFAULT_V0_SPEC_RELATIVE).resolve()
    architecture_spec_path = Path(
        architecture_spec_path or root / DEFAULT_ARCHITECTURE_SPEC_RELATIVE
    ).resolve()
    v0_oof_path = Path(v0_oof_path or root / DEFAULT_V0_OOF_RELATIVE).resolve()
    patient_output_dir = Path(
        patient_output_dir or root / DEFAULT_PATIENT_OUTPUT_RELATIVE
    ).resolve()
    aggregate_audit_path = Path(
        aggregate_audit_path or root / DEFAULT_AUDIT_RELATIVE
    ).resolve()
    raw_spec = yaml.safe_load(spec_path.read_text(encoding="utf-8-sig"))
    expected_v0_hash = raw_spec["clinical_anchor"]["reference_oof_sha256"]
    spec, v0_spec = U2Spec.from_yaml(spec_path), V0Spec.from_yaml(v0_spec_path)
    gate_payload = yaml.safe_load(gate_path.read_text(encoding="utf-8-sig"))
    architecture = V1SmokeSpec.from_yaml(architecture_spec_path)
    torch.use_deterministic_algorithms(spec.deterministic_algorithms)
    torch.set_num_threads(1)
    contract = HancockContractBuilder(root).build()
    reference = _load_v0_reference(v0_oof_path, expected_v0_hash)
    oof, aggregate = development_cross_fit(
        contract, spec, v0_spec, architecture,
        v0_reference=reference, verbose=verbose,
    )
    gate_result = apply_complexity_gate(oof, aggregate, gate_payload)
    patient_output_dir.mkdir(parents=True, exist_ok=True)
    oof_path = patient_output_dir / "v1_repeated_nested_oof_predictions.csv"
    oof.to_csv(oof_path, index=False)
    payload = {
        "schema_version": "0.1", "study_id": "pattern_surv_hn",
        "stage_id": "U2_V1_DEVELOPMENT_CV", "analysis_label": "post_lock_exploratory",
        "completed_on": ANALYSIS_DATE,
        "model": {
            "id": MODEL_ID, "name": MODEL_NAME,
            "parameter_count": int(aggregate["parameter_count"]),
            "clinical_anchor": "U1.2_V0",
        },
        "estimand": {
            "cohort": "HANCOCK_official_training", "eligible_n": spec.expected_n,
            "events": spec.expected_events, "horizon_days": spec.horizon_days,
        },
        "cross_fitting": {
            "outer_folds": spec.outer_folds,
            "outer_repetition_seeds": list(spec.outer_repetition_seeds),
            "inner_folds": spec.inner_folds, "oof_rows": len(oof),
            "expected_oof_rows": spec.expected_n * len(spec.outer_repetition_seeds),
            "fold_bound_clinical_preprocessing": True,
            "fold_bound_modality_preprocessing": True,
            "training_fold_Breslow_baseline": True,
            "reference_v0_outer_folds_reused": True,
        },
        "results": aggregate, "complexity_gate": gate_result,
        "governance": {
            "official_test_outcomes_derived_exposed_or_evaluated": False,
            "external_outcomes_used": False, "V2_trained": False,
            "calibration_bridge_trained": False, "router_labels_created": False,
            "router_trained": False, "tracked_artifacts_aggregate_only": True,
            "patient_level_oof_git_ignored": True, "coverage_reduction_used": False,
        },
        "artifacts": {
            "frozen_spec": spec_path.relative_to(root).as_posix(),
            "frozen_spec_sha256": _sha256(spec_path),
            "frozen_gate": gate_path.relative_to(root).as_posix(),
            "frozen_gate_sha256": _sha256(gate_path),
            "v0_reference_oof_sha256": _sha256(v0_oof_path),
            "patient_oof_relative_path": oof_path.relative_to(root).as_posix(),
            "patient_oof_sha256": _sha256(oof_path), "patient_oof_tracked": False,
        },
        "limitations": [
            "Results are post-lock exploratory internal development estimates.",
            "The complexity gate is not official-test or external confirmation.",
            "No calibration bridge or Global Value Router was trained in U2.",
            "Patterns below the frozen support gate are descriptive only.",
        ],
    }
    safe_payload = _json_safe(payload)
    assert_aggregate_only(safe_payload)
    aggregate_audit_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_audit_path.write_text(
        json.dumps(safe_payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return safe_payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--v0-spec", type=Path)
    parser.add_argument("--architecture-spec", type=Path)
    parser.add_argument("--v0-oof", type=Path)
    parser.add_argument("--patient-output-dir", type=Path)
    parser.add_argument("--aggregate-audit", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    result = run_u2_experiment(
        args.project_root, spec_path=args.spec, gate_path=args.gate,
        v0_spec_path=args.v0_spec, architecture_spec_path=args.architecture_spec,
        v0_oof_path=args.v0_oof, patient_output_dir=args.patient_output_dir,
        aggregate_audit_path=args.aggregate_audit, verbose=args.verbose,
    )
    print(json.dumps(result["complexity_gate"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
