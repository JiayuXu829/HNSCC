"""Trainable PyTorch smoke implementation of PATTERN-Surv-HN V1.

The module is restricted to deterministic synthetic optimization. It does not load patient data,
perform development cross-validation, evaluate outcomes, or implement calibration/routing.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import Tensor, nn

from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import (
    DEFAULT_SPEC_RELATIVE as DEFAULT_ARCHITECTURE_SPEC_RELATIVE,
)
from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import (
    MODALITY_ORDER,
    SENSITIVE_KEYS,
    STATUS_LEVELS,
    V1SmokeSpec,
)

MODEL_ID = "V1"
MODEL_NAME = "Clinical_Residual_Deep_Sets_Cox"
DEFAULT_TRAINING_SPEC_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U1_4_V1_trainable_smoke/frozen_v1_trainable_smoke_spec.yaml"
)
DEFAULT_AUDIT_RELATIVE = (
    DEFAULT_TRAINING_SPEC_RELATIVE.parent / "aggregate_v1_trainable_smoke_audit.json"
)


@dataclass(frozen=True)
class V1TrainableSmokeSpec:
    """Frozen synthetic optimization settings for U1.4."""

    synthetic_rows: int
    optimization_steps: int
    learning_rate: float
    weight_decay: float
    seed: int
    minimum_relative_loss_reduction: float
    gradient_clip_norm: float
    dtype: str
    device: str

    @classmethod
    def from_yaml(cls, path: Path) -> V1TrainableSmokeSpec:
        import yaml

        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
        synthetic = payload["synthetic_training"]
        optimization = payload["optimization"]
        spec = cls(
            synthetic_rows=int(synthetic["rows"]),
            optimization_steps=int(optimization["steps"]),
            learning_rate=float(optimization["learning_rate"]),
            weight_decay=float(optimization["weight_decay"]),
            seed=int(synthetic["seed"]),
            minimum_relative_loss_reduction=float(
                optimization["minimum_relative_loss_reduction"]
            ),
            gradient_clip_norm=float(optimization["gradient_clip_norm"]),
            dtype=str(payload["runtime"]["dtype"]),
            device=str(payload["runtime"]["device"]),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if self.synthetic_rows < 16:
            raise ValueError("synthetic smoke requires at least 16 rows")
        if self.optimization_steps < 1:
            raise ValueError("optimization_steps must be positive")
        if self.learning_rate <= 0 or self.weight_decay < 0:
            raise ValueError("invalid optimizer settings")
        if not 0 < self.minimum_relative_loss_reduction < 1:
            raise ValueError("minimum_relative_loss_reduction must be in (0, 1)")
        if self.gradient_clip_norm <= 0:
            raise ValueError("gradient_clip_norm must be positive")
        if self.dtype != "float64":
            raise ValueError("U1.4 deterministic smoke is frozen to float64")
        if self.device != "cpu":
            raise ValueError("U1.4 deterministic smoke is frozen to CPU")


@dataclass(frozen=True)
class TorchModalityBatch:
    """Tensor input for one named modality."""

    name: str
    content: Tensor
    active: Tensor
    status_index: Tensor
    quality: Tensor


@dataclass(frozen=True)
class TorchDeepSetsForward:
    clinical_score: Tensor
    residual_score: Tensor
    fused_score: Tensor
    active_token_count: Tensor


class TrainableClinicalResidualDeepSetsCox(nn.Module):
    """Trainable V1 backbone preserving the U1.3 exact-fallback contract."""

    def __init__(self, architecture: V1SmokeSpec):
        super().__init__()
        self.architecture = architecture
        torch.manual_seed(architecture.seed)
        token = architecture.token_dimension
        self.adapters = nn.ModuleDict(
            {
                name: nn.Linear(width, token)
                for name, width in architecture.modality_input_dimensions.items()
            }
        )
        self.identity_embedding = nn.Embedding(len(MODALITY_ORDER), token)
        self.status_embedding = nn.Embedding(len(STATUS_LEVELS), token)
        self.quality_projection = nn.Linear(len(architecture.quality_features), token, bias=False)
        self.phi = nn.Sequential(
            nn.Linear(token, architecture.phi_hidden_dimension),
            nn.Tanh(),
            nn.Linear(architecture.phi_hidden_dimension, token),
            nn.Tanh(),
        )
        self.rho = nn.Sequential(
            nn.Linear(token, architecture.rho_hidden_dimension),
            nn.Tanh(),
            nn.Linear(architecture.rho_hidden_dimension, 1),
        )
        self.to(dtype=torch.float64, device="cpu")
        if self.parameter_count > architecture.maximum_parameter_count:
            raise ValueError("trainable V1 exceeds the frozen parameter-count ceiling")

    @property
    def parameter_count(self) -> int:
        return int(sum(parameter.numel() for parameter in self.parameters()))

    def _validate_batch(self, batch: TorchModalityBatch, batch_size: int) -> None:
        if batch.name not in self.architecture.modality_input_dimensions:
            raise ValueError(f"unknown modality: {batch.name}")
        width = self.architecture.modality_input_dimensions[batch.name]
        if tuple(batch.content.shape) != (batch_size, width):
            raise ValueError(f"{batch.name} content must have shape ({batch_size}, {width})")
        if tuple(batch.active.shape) != (batch_size,) or batch.active.dtype != torch.bool:
            raise ValueError(f"{batch.name} active must be a boolean vector")
        if tuple(batch.status_index.shape) != (batch_size,):
            raise ValueError(f"{batch.name} status_index must have shape ({batch_size},)")
        if batch.status_index.dtype != torch.long:
            raise ValueError("status_index must use torch.long")
        if bool(torch.any((batch.status_index < 0) | (batch.status_index >= len(STATUS_LEVELS)))):
            raise ValueError("status_index contains an unknown status")
        expected_quality = (batch_size, len(self.architecture.quality_features))
        if tuple(batch.quality.shape) != expected_quality:
            raise ValueError(f"{batch.name} quality must have shape {expected_quality}")
        if not bool(torch.all(torch.isfinite(batch.quality))):
            raise ValueError("quality features must be finite")
        if bool(torch.any((batch.quality < 0) | (batch.quality > 1))):
            raise ValueError("quality features must lie in [0, 1]")
        if batch.active.any() and not bool(torch.all(torch.isfinite(batch.content[batch.active]))):
            raise ValueError("active modality content must be finite")

    def encode_modality(self, batch: TorchModalityBatch, batch_size: int) -> tuple[Tensor, Tensor]:
        self._validate_batch(batch, batch_size)
        safe_content = torch.where(
            torch.isfinite(batch.content), batch.content, torch.zeros_like(batch.content)
        )
        identity_index = torch.full(
            (batch_size,),
            MODALITY_ORDER.index(batch.name),
            dtype=torch.long,
            device=batch.content.device,
        )
        token = torch.tanh(
            torch.tanh(self.adapters[batch.name](safe_content))
            + self.identity_embedding(identity_index)
            + self.status_embedding(batch.status_index)
            + self.quality_projection(batch.quality)
        )
        return token, batch.active

    def forward(
        self,
        clinical_score: Tensor,
        modalities: Sequence[TorchModalityBatch],
    ) -> TorchDeepSetsForward:
        if clinical_score.ndim != 1 or clinical_score.numel() < 1:
            raise ValueError("clinical_score must be a non-empty vector")
        if not bool(torch.all(torch.isfinite(clinical_score))):
            raise ValueError("clinical_score must be finite")
        names = [batch.name for batch in modalities]
        if len(names) != len(set(names)):
            raise ValueError("each modality may appear at most once")

        rows = clinical_score.numel()
        pooled_sum = torch.zeros(
            (rows, self.architecture.token_dimension),
            dtype=clinical_score.dtype,
            device=clinical_score.device,
        )
        active_count = torch.zeros(rows, dtype=torch.long, device=clinical_score.device)
        for batch in modalities:
            token, active = self.encode_modality(batch, rows)
            encoded = self.phi(token)
            pooled_sum = pooled_sum + encoded * active[:, None]
            active_count = active_count + active.long()

        has_evidence = active_count > 0
        denominator = active_count.clamp_min(1).to(clinical_score.dtype)[:, None]
        pooled = pooled_sum / denominator
        residual = torch.zeros_like(clinical_score)
        if bool(has_evidence.any()):
            residual = residual.index_put(
                (has_evidence,),
                self.rho(pooled[has_evidence]).squeeze(-1),
            )
        return TorchDeepSetsForward(
            clinical_score=clinical_score,
            residual_score=residual,
            fused_score=clinical_score + residual,
            active_token_count=active_count,
        )


def negative_breslow_cox_loss(duration: Tensor, event: Tensor, score: Tensor) -> Tensor:
    """Differentiable mean negative Breslow Cox partial log likelihood."""

    if duration.ndim != 1 or event.shape != duration.shape or score.shape != duration.shape:
        raise ValueError("duration, event, and score must be equal-length vectors")
    if duration.numel() < 2 or not bool(torch.all(torch.isfinite(duration))):
        raise ValueError("duration must contain at least two finite rows")
    if bool(torch.any(duration <= 0)) or not bool(torch.all(torch.isfinite(score))):
        raise ValueError("duration must be positive and scores must be finite")
    observed = event.bool()
    event_times = torch.unique(duration[observed])
    if event_times.numel() == 0:
        raise ValueError("at least one event is required")
    terms: list[Tensor] = []
    event_count = 0
    for event_time in event_times:
        tied = observed & (duration == event_time)
        tied_count = int(tied.sum().item())
        risk = duration >= event_time
        terms.append(score[tied].sum() - tied_count * torch.logsumexp(score[risk], dim=0))
        event_count += tied_count
    return -torch.stack(terms).sum() / event_count


def _status_index(name: str) -> int:
    return STATUS_LEVELS.index(name)


def make_synthetic_survival_batch(
    architecture: V1SmokeSpec,
    training: V1TrainableSmokeSpec,
) -> tuple[Tensor, tuple[TorchModalityBatch, ...], Tensor, Tensor]:
    """Create deterministic variable-pattern synthetic survival data with a learnable signal."""

    generator = torch.Generator(device="cpu").manual_seed(training.seed)
    rows = training.synthetic_rows
    dtype = torch.float64
    clinical = torch.randn(rows, generator=generator, dtype=dtype) * 0.35
    coefficients = {"blood": 1.10, "icd": -0.85, "tma": 0.70}
    probabilities = {"blood": 0.72, "icd": 0.78, "tma": 0.66}
    true_score = clinical.clone()
    batches: list[TorchModalityBatch] = []

    for name in MODALITY_ORDER:
        width = architecture.modality_input_dimensions[name]
        content = torch.randn((rows, width), generator=generator, dtype=dtype)
        active = torch.rand(rows, generator=generator) < probabilities[name]
        active[0] = False
        active[1] = True
        partial = (torch.rand(rows, generator=generator) < 0.30) & active
        missing_fraction = torch.rand(rows, generator=generator, dtype=dtype) * 0.25
        missing_fraction = torch.where(partial, missing_fraction + 0.20, missing_fraction)
        missing_fraction = torch.where(active, missing_fraction, torch.ones_like(missing_fraction))
        observed_fraction = 1.0 - missing_fraction
        quality = torch.column_stack([missing_fraction, observed_fraction])
        status = torch.full(
            (rows,),
            _status_index("absent"),
            dtype=torch.long,
        )
        status[active] = _status_index("usable_complete")
        status[partial] = _status_index("usable_partial")
        if name == "icd":
            status[active] = _status_index("conditional_provenance")
        true_score = true_score + active.to(dtype) * coefficients[name] * content[:, 0]
        content = content.clone()
        content[~active] = torch.nan
        batches.append(
            TorchModalityBatch(
                name=name,
                content=content,
                active=active,
                status_index=status,
                quality=quality,
            )
        )

    jitter = torch.linspace(0.001, 0.099, rows, dtype=dtype)
    duration = 30.0 + 120.0 * torch.exp(-true_score) + jitter
    event = torch.ones(rows, dtype=torch.bool)
    event[::7] = False
    event[1] = True
    return clinical, tuple(batches), duration, event


def _parameter_vector(model: nn.Module) -> Tensor:
    return torch.cat([parameter.detach().reshape(-1) for parameter in model.parameters()])


def _contains_sensitive_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in SENSITIVE_KEYS or _contains_sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def run_trainable_smoke(
    architecture: V1SmokeSpec,
    training: V1TrainableSmokeSpec,
) -> dict[str, object]:
    """Train on synthetic data and return an aggregate-only deterministic audit."""

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(training.seed)
    model = TrainableClinicalResidualDeepSetsCox(architecture)
    clinical, batches, duration, event = make_synthetic_survival_batch(architecture, training)
    initial_parameters = _parameter_vector(model).clone()

    model.eval()
    with torch.no_grad():
        canonical = model(clinical, batches)
        permuted = model(clinical, (batches[2], batches[0], batches[1]))
        empty = tuple(
            TorchModalityBatch(
                name=batch.name,
                content=torch.full_like(batch.content, torch.nan),
                active=torch.zeros_like(batch.active),
                status_index=torch.full_like(batch.status_index, _status_index("absent")),
                quality=torch.column_stack(
                    [torch.ones(clinical.numel()), torch.zeros(clinical.numel())]
                ).to(torch.float64),
            )
            for batch in batches
        )
        initial_loss = float(
            negative_breslow_cox_loss(duration, event, canonical.fused_score).item()
        )
        shifted_loss = float(
            negative_breslow_cox_loss(duration, event, canonical.fused_score + 13.0).item()
        )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=training.learning_rate,
        weight_decay=training.weight_decay,
    )
    gradient_norm_first = math.nan
    losses: list[float] = []
    model.train()
    for step in range(training.optimization_steps):
        optimizer.zero_grad(set_to_none=True)
        output = model(clinical, batches)
        loss = negative_breslow_cox_loss(duration, event, output.fused_score)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(
            model.parameters(), training.gradient_clip_norm
        )
        if step == 0:
            gradient_norm_first = float(gradient_norm.item())
        optimizer.step()
        losses.append(float(loss.detach().item()))

    model.eval()
    with torch.no_grad():
        final_output = model(clinical, batches)
        final_loss = float(
            negative_breslow_cox_loss(duration, event, final_output.fused_score).item()
        )
        final_permuted = model(clinical, (batches[1], batches[2], batches[0]))
        final_fallback = model(clinical, empty)
    final_parameters = _parameter_vector(model)

    relative_reduction = (initial_loss - final_loss) / initial_loss
    permutation_error = float(
        torch.max(torch.abs(final_output.fused_score - final_permuted.fused_score)).item()
    )
    pretrain_permutation_error = float(
        torch.max(torch.abs(canonical.fused_score - permuted.fused_score)).item()
    )
    fallback_residual_error = float(torch.max(torch.abs(final_fallback.residual_score)).item())
    fallback_fused_error = float(
        torch.max(torch.abs(final_fallback.fused_score - clinical)).item()
    )
    parameter_change = float(torch.linalg.vector_norm(final_parameters - initial_parameters).item())

    checks = {
        "torch_cpu_runtime": torch.__version__.endswith("+cpu") and not torch.cuda.is_available(),
        "finite_initial_loss": math.isfinite(initial_loss),
        "finite_final_loss": math.isfinite(final_loss),
        "finite_nonzero_gradient": math.isfinite(gradient_norm_first)
        and gradient_norm_first > 0.0,
        "parameters_updated": parameter_change > 0.0,
        "minimum_loss_reduction": relative_reduction
        >= training.minimum_relative_loss_reduction,
        "pretrain_permutation_invariance": pretrain_permutation_error <= 1e-12,
        "posttrain_permutation_invariance": permutation_error <= 1e-12,
        "exact_zero_residual_without_active_tokens": fallback_residual_error == 0.0,
        "exact_clinical_only_fallback": fallback_fused_error == 0.0,
        "cox_score_shift_invariance": abs(initial_loss - shifted_loss) <= 1e-12,
        "parameter_ceiling": model.parameter_count <= architecture.maximum_parameter_count,
    }
    result: dict[str, object] = {
        "schema_version": "0.1",
        "study_id": "pattern_surv_hn",
        "stage": "U1.4/V1 trainable implementation",
        "model_id": MODEL_ID,
        "model_name": MODEL_NAME,
        "scope": "synthetic_optimization_smoke_only_no_patient_training",
        "framework": "pytorch",
        "torch_version": torch.__version__,
        "torch_cuda_build": torch.version.cuda,
        "device": training.device,
        "dtype": training.dtype,
        "synthetic_rows": training.synthetic_rows,
        "optimization_steps": training.optimization_steps,
        "learning_rate": training.learning_rate,
        "weight_decay": training.weight_decay,
        "parameter_count": model.parameter_count,
        "metrics": {
            "initial_cox_loss": initial_loss,
            "final_cox_loss": final_loss,
            "relative_loss_reduction": relative_reduction,
            "first_gradient_global_norm": gradient_norm_first,
            "parameter_l2_change": parameter_change,
            "pretrain_permutation_max_abs_error": pretrain_permutation_error,
            "posttrain_permutation_max_abs_error": permutation_error,
            "fallback_residual_max_abs_error": fallback_residual_error,
            "fallback_fused_max_abs_error": fallback_fused_error,
            "cox_shift_invariance_error": abs(initial_loss - shifted_loss),
            "minimum_training_loss": min(losses),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "patient_level_data_used": False,
        "patient_level_output_written": False,
        "patient_model_checkpoint_written": False,
        "outcomes_used": False,
        "official_test_accessed": False,
        "external_data_accessed": False,
        "formal_development_cv_performed": False,
        "router_or_calibrator_used": False,
        "limitations": [
            "Optimization used deterministic synthetic outcomes only.",
            "Loss reduction establishes trainability, not prognostic performance.",
            "Formal HANCOCK development cross-validation remains separately gated.",
        ],
    }
    if _contains_sensitive_key(result):
        raise RuntimeError("aggregate trainable smoke audit contains an identifier-like key")
    if not result["all_checks_pass"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"V1 trainable smoke checks failed: {failed}")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--architecture-spec", type=Path)
    parser.add_argument("--training-spec", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    architecture_path = args.architecture_spec or root / DEFAULT_ARCHITECTURE_SPEC_RELATIVE
    training_path = args.training_spec or root / DEFAULT_TRAINING_SPEC_RELATIVE
    output_path = args.output or root / DEFAULT_AUDIT_RELATIVE
    architecture = V1SmokeSpec.from_yaml(architecture_path)
    training = V1TrainableSmokeSpec.from_yaml(training_path)
    result = run_trainable_smoke(architecture, training)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
