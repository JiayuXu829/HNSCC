"""Structural smoke implementation of the PATTERN-Surv-HN V1 backbone.

This module is deliberately limited to a deterministic NumPy reference forward pass and Cox
partial-likelihood check. It validates the Clinical-Residual Deep Sets contract without training
on patient outcomes and without introducing an unapproved deep-learning dependency.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from trust_hn.pattern_surv_hn.hancock_contract import ModalityStatus

MODEL_ID = "V1"
MODEL_NAME = "Clinical_Residual_Deep_Sets_Cox"
MODALITY_ORDER: tuple[str, ...] = ("blood", "icd", "tma")
STATUS_LEVELS: tuple[str, ...] = tuple(status.value for status in ModalityStatus)
DEFAULT_SPEC_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U1_3_V1_smoke/frozen_v1_smoke_spec.yaml"
)
DEFAULT_AUDIT_RELATIVE = DEFAULT_SPEC_RELATIVE.parent / "aggregate_v1_smoke_audit.json"
SENSITIVE_KEYS = frozenset({"native_id", "patient_id", "case_id", "submitter_id"})


@dataclass(frozen=True)
class V1SmokeSpec:
    """Frozen structural dimensions for the dependency-free V1 smoke reference."""

    token_dimension: int
    phi_hidden_dimension: int
    rho_hidden_dimension: int
    quality_features: tuple[str, ...]
    modality_input_dimensions: Mapping[str, int]
    seed: int
    maximum_parameter_count: int

    @classmethod
    def from_yaml(cls, path: Path) -> V1SmokeSpec:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
        model = payload["model"]
        constraints = payload["constraints"]
        spec = cls(
            token_dimension=int(model["token_dimension"]),
            phi_hidden_dimension=int(model["phi_hidden_dimension"]),
            rho_hidden_dimension=int(model["rho_hidden_dimension"]),
            quality_features=tuple(model["quality_features"]),
            modality_input_dimensions={
                str(name): int(size)
                for name, size in model["modality_input_dimensions"].items()
            },
            seed=int(model["deterministic_reference_seed"]),
            maximum_parameter_count=int(constraints["maximum_parameter_count"]),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if self.token_dimension < 1:
            raise ValueError("token_dimension must be positive")
        if self.phi_hidden_dimension < 1 or self.rho_hidden_dimension < 1:
            raise ValueError("hidden dimensions must be positive")
        if not self.quality_features:
            raise ValueError("at least one quality feature is required")
        if set(self.modality_input_dimensions) != set(MODALITY_ORDER):
            raise ValueError("V1 smoke spec must define blood, icd, and tma dimensions")
        if any(size < 1 for size in self.modality_input_dimensions.values()):
            raise ValueError("modality input dimensions must be positive")
        if self.maximum_parameter_count < 1:
            raise ValueError("maximum_parameter_count must be positive")


@dataclass(frozen=True)
class ModalityBatch:
    """One named modality token source for a batch of synthetic or fold-preprocessed rows."""

    name: str
    content: np.ndarray
    active: np.ndarray
    status: Sequence[str]
    quality: np.ndarray


@dataclass(frozen=True)
class DeepSetsForward:
    """Forward outputs needed by the survival backbone and structural audits."""

    clinical_score: np.ndarray
    residual_score: np.ndarray
    fused_score: np.ndarray
    active_token_count: np.ndarray


class ClinicalResidualDeepSetsCox:
    """Deterministic dependency-free reference for the V1 set-residual contract.

    Parameters are intentionally fixed random reference weights. This object is not the formally
    trainable V1 estimator; it exists to validate interfaces, set invariance, status/quality
    encoding, arbitrary-subset handling, and exact clinical-only fallback before dependency and
    development-CV approval.
    """

    def __init__(self, spec: V1SmokeSpec):
        self.spec = spec
        rng = np.random.default_rng(spec.seed)
        token = spec.token_dimension
        quality = len(spec.quality_features)

        self.adapter_weights = {
            name: self._weight(rng, input_size, token)
            for name, input_size in spec.modality_input_dimensions.items()
        }
        self.adapter_biases = {
            name: self._weight(rng, 1, token).reshape(token)
            for name in MODALITY_ORDER
        }
        self.identity_embeddings = self._weight(rng, len(MODALITY_ORDER), token)
        self.status_embeddings = self._weight(rng, len(STATUS_LEVELS), token)
        self.quality_weights = self._weight(rng, quality, token)
        self.phi_weight_1 = self._weight(rng, token, spec.phi_hidden_dimension)
        self.phi_bias_1 = self._weight(rng, 1, spec.phi_hidden_dimension).reshape(
            spec.phi_hidden_dimension
        )
        self.phi_weight_2 = self._weight(rng, spec.phi_hidden_dimension, token)
        self.phi_bias_2 = self._weight(rng, 1, token).reshape(token)
        self.rho_weight_1 = self._weight(rng, token, spec.rho_hidden_dimension)
        self.rho_bias_1 = self._weight(rng, 1, spec.rho_hidden_dimension).reshape(
            spec.rho_hidden_dimension
        )
        self.rho_weight_2 = self._weight(rng, spec.rho_hidden_dimension, 1)
        self.rho_bias_2 = self._weight(rng, 1, 1).reshape(1)
        if self.parameter_count > spec.maximum_parameter_count:
            raise ValueError("V1 smoke reference exceeds the frozen parameter-count ceiling")

    @staticmethod
    def _weight(rng: np.random.Generator, rows: int, columns: int) -> np.ndarray:
        scale = 1.0 / math.sqrt(max(1, rows))
        return rng.normal(0.0, scale, size=(rows, columns)).astype(float)

    @property
    def parameter_count(self) -> int:
        arrays = [
            *self.adapter_weights.values(),
            *self.adapter_biases.values(),
            self.identity_embeddings,
            self.status_embeddings,
            self.quality_weights,
            self.phi_weight_1,
            self.phi_bias_1,
            self.phi_weight_2,
            self.phi_bias_2,
            self.rho_weight_1,
            self.rho_bias_1,
            self.rho_weight_2,
            self.rho_bias_2,
        ]
        return int(sum(array.size for array in arrays))

    def _validate_batch(self, batch: ModalityBatch, batch_size: int) -> tuple[np.ndarray, ...]:
        if batch.name not in self.spec.modality_input_dimensions:
            raise ValueError(f"unknown modality: {batch.name}")
        content = np.asarray(batch.content, dtype=float)
        active = np.asarray(batch.active, dtype=bool)
        quality = np.asarray(batch.quality, dtype=float)
        status = np.asarray(tuple(batch.status), dtype=object)
        expected_width = self.spec.modality_input_dimensions[batch.name]
        if content.shape != (batch_size, expected_width):
            raise ValueError(
                f"{batch.name} content must have shape ({batch_size}, {expected_width})"
            )
        if active.shape != (batch_size,):
            raise ValueError(f"{batch.name} active mask must have shape ({batch_size},)")
        if status.shape != (batch_size,):
            raise ValueError(f"{batch.name} status must have length {batch_size}")
        if quality.shape != (batch_size, len(self.spec.quality_features)):
            raise ValueError(
                f"{batch.name} quality must have shape "
                f"({batch_size}, {len(self.spec.quality_features)})"
            )
        unknown = sorted(set(status.astype(str)) - set(STATUS_LEVELS))
        if unknown:
            raise ValueError(f"unknown modality status values: {unknown}")
        if np.any(~np.isfinite(quality)) or np.any((quality < 0.0) | (quality > 1.0)):
            raise ValueError("quality features must be finite values in [0, 1]")
        if np.any(~np.isfinite(content[active])):
            raise ValueError("active modality content must be finite")
        return content, active, status.astype(str), quality

    def encode_modality(
        self, batch: ModalityBatch, batch_size: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Encode one modality while allowing non-finite placeholders only on inactive rows."""

        content, active, status, quality = self._validate_batch(batch, batch_size)
        safe_content = np.where(np.isfinite(content), content, 0.0)
        content_embedding = np.tanh(
            safe_content @ self.adapter_weights[batch.name] + self.adapter_biases[batch.name]
        )
        identity_index = MODALITY_ORDER.index(batch.name)
        status_indices = np.asarray([STATUS_LEVELS.index(value) for value in status], dtype=int)
        token = np.tanh(
            content_embedding
            + self.identity_embeddings[identity_index]
            + self.status_embeddings[status_indices]
            + quality @ self.quality_weights
        )
        return token, active

    def _phi(self, token: np.ndarray) -> np.ndarray:
        hidden = np.tanh(token @ self.phi_weight_1 + self.phi_bias_1)
        return np.tanh(hidden @ self.phi_weight_2 + self.phi_bias_2)

    def _rho(self, pooled: np.ndarray) -> np.ndarray:
        hidden = np.tanh(pooled @ self.rho_weight_1 + self.rho_bias_1)
        return (hidden @ self.rho_weight_2 + self.rho_bias_2).reshape(-1)

    def forward(
        self,
        clinical_score: Sequence[float],
        modalities: Sequence[ModalityBatch],
    ) -> DeepSetsForward:
        clinical = np.asarray(clinical_score, dtype=float)
        if clinical.ndim != 1 or clinical.size < 1 or np.any(~np.isfinite(clinical)):
            raise ValueError("clinical_score must be a finite non-empty one-dimensional array")
        names = [batch.name for batch in modalities]
        if len(names) != len(set(names)):
            raise ValueError("each modality may appear at most once")

        pooled_sum = np.zeros((clinical.size, self.spec.token_dimension), dtype=float)
        active_count = np.zeros(clinical.size, dtype=int)
        for batch in modalities:
            token, active = self.encode_modality(batch, clinical.size)
            encoded = self._phi(token)
            pooled_sum += encoded * active[:, None]
            active_count += active.astype(int)

        pooled = np.zeros_like(pooled_sum)
        has_evidence = active_count > 0
        pooled[has_evidence] = pooled_sum[has_evidence] / active_count[has_evidence, None]
        residual = np.zeros(clinical.size, dtype=float)
        residual[has_evidence] = self._rho(pooled[has_evidence])
        fused = clinical + residual
        return DeepSetsForward(
            clinical_score=clinical.copy(),
            residual_score=residual,
            fused_score=fused,
            active_token_count=active_count,
        )


def negative_cox_partial_log_likelihood(
    duration: Sequence[float], event: Sequence[int | bool], score: Sequence[float]
) -> float:
    """Mean negative Breslow Cox partial log likelihood for a structural smoke check."""

    time = np.asarray(duration, dtype=float)
    observed = np.asarray(event, dtype=bool)
    eta = np.asarray(score, dtype=float)
    if time.ndim != 1 or observed.shape != time.shape or eta.shape != time.shape:
        raise ValueError("duration, event, and score must be equal-length one-dimensional arrays")
    if time.size < 2 or np.any(~np.isfinite(time)) or np.any(time <= 0):
        raise ValueError("durations must be finite, positive, and contain at least two rows")
    if np.any(~np.isfinite(eta)):
        raise ValueError("scores must be finite")
    event_times = np.unique(time[observed])
    if event_times.size == 0:
        raise ValueError("at least one event is required")

    log_likelihood = 0.0
    event_count = 0
    for event_time in event_times:
        tied_events = observed & (time == event_time)
        risk_scores = eta[time >= event_time]
        maximum = float(np.max(risk_scores))
        log_risk_sum = maximum + math.log(float(np.exp(risk_scores - maximum).sum()))
        tied_count = int(tied_events.sum())
        log_likelihood += float(eta[tied_events].sum()) - tied_count * log_risk_sum
        event_count += tied_count
    return float(-log_likelihood / event_count)


def _synthetic_batches(spec: V1SmokeSpec, rows: int = 7) -> tuple[ModalityBatch, ...]:
    rng = np.random.default_rng(spec.seed + 1)
    masks = {
        "blood": np.asarray([True, True, False, True, False, True, False]),
        "icd": np.asarray([True, False, True, True, False, False, False]),
        "tma": np.asarray([True, True, True, False, False, True, False]),
    }
    statuses = {
        "blood": [
            ModalityStatus.USABLE_COMPLETE.value,
            ModalityStatus.USABLE_PARTIAL.value,
            ModalityStatus.ABSENT.value,
            ModalityStatus.USABLE_COMPLETE.value,
            ModalityStatus.ACQUIRED_UNUSABLE.value,
            ModalityStatus.USABLE_PARTIAL.value,
            ModalityStatus.ABSENT.value,
        ],
        "icd": [
            ModalityStatus.CONDITIONAL_PROVENANCE.value,
            ModalityStatus.ABSENT.value,
            ModalityStatus.CONDITIONAL_PROVENANCE.value,
            ModalityStatus.CONDITIONAL_PROVENANCE.value,
            ModalityStatus.ABSENT.value,
            ModalityStatus.ABSENT.value,
            ModalityStatus.ABSENT.value,
        ],
        "tma": [
            ModalityStatus.USABLE_COMPLETE.value,
            ModalityStatus.USABLE_PARTIAL.value,
            ModalityStatus.USABLE_COMPLETE.value,
            ModalityStatus.ABSENT.value,
            ModalityStatus.ABSENT.value,
            ModalityStatus.USABLE_PARTIAL.value,
            ModalityStatus.ABSENT.value,
        ],
    }
    batches: list[ModalityBatch] = []
    for name in MODALITY_ORDER:
        width = spec.modality_input_dimensions[name]
        content = rng.normal(size=(rows, width))
        content[~masks[name]] = np.nan
        missing_fraction = rng.uniform(0.0, 0.35, size=rows)
        missing_fraction[~masks[name]] = 1.0
        quality = np.column_stack([missing_fraction, 1.0 - missing_fraction])
        batches.append(
            ModalityBatch(
                name=name,
                content=content,
                active=masks[name],
                status=statuses[name],
                quality=quality,
            )
        )
    return tuple(batches)


def _minimum_pairwise_distance(matrix: np.ndarray) -> float:
    distances = [
        float(np.linalg.norm(matrix[left] - matrix[right]))
        for left in range(len(matrix))
        for right in range(left + 1, len(matrix))
    ]
    return min(distances)


def _contains_sensitive_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in SENSITIVE_KEYS or _contains_sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def run_structural_smoke(spec: V1SmokeSpec) -> dict[str, object]:
    """Run a deterministic aggregate-only structural smoke audit."""

    model = ClinicalResidualDeepSetsCox(spec)
    clinical = np.linspace(-0.8, 0.8, 7)
    batches = _synthetic_batches(spec)
    forward = model.forward(clinical, batches)
    permuted = model.forward(clinical, (batches[2], batches[0], batches[1]))

    inactive = tuple(
        ModalityBatch(
            name=batch.name,
            content=np.full_like(batch.content, np.nan),
            active=np.zeros_like(batch.active),
            status=[ModalityStatus.ABSENT.value] * clinical.size,
            quality=np.column_stack([np.ones(clinical.size), np.zeros(clinical.size)]),
        )
        for batch in batches
    )
    fallback = model.forward(clinical, inactive)
    subset = model.forward(clinical, (batches[0], batches[2]))

    changed_status = list(batches[0].status)
    changed_status[0] = ModalityStatus.USABLE_PARTIAL.value
    status_batch = ModalityBatch(
        name="blood",
        content=batches[0].content,
        active=batches[0].active,
        status=changed_status,
        quality=batches[0].quality,
    )
    status_changed = model.forward(clinical, (status_batch, batches[1], batches[2]))

    changed_quality = batches[0].quality.copy()
    changed_quality[0] = np.asarray([0.8, 0.2])
    quality_batch = ModalityBatch(
        name="blood",
        content=batches[0].content,
        active=batches[0].active,
        status=batches[0].status,
        quality=changed_quality,
    )
    quality_changed = model.forward(clinical, (quality_batch, batches[1], batches[2]))

    duration = np.asarray([5.0, 8.0, 9.0, 12.0, 15.0, 18.0, 21.0])
    event = np.asarray([1, 0, 1, 1, 0, 1, 0])
    loss = negative_cox_partial_log_likelihood(duration, event, forward.fused_score)
    shifted_loss = negative_cox_partial_log_likelihood(
        duration, event, forward.fused_score + 11.0
    )

    permutation_error = float(np.max(np.abs(forward.fused_score - permuted.fused_score)))
    fallback_residual_error = float(np.max(np.abs(fallback.residual_score)))
    fallback_fused_error = float(np.max(np.abs(fallback.fused_score - clinical)))
    status_sensitivity = float(
        np.max(np.abs(forward.fused_score - status_changed.fused_score))
    )
    quality_sensitivity = float(
        np.max(np.abs(forward.fused_score - quality_changed.fused_score))
    )
    cox_shift_error = abs(loss - shifted_loss)

    checks = {
        "permutation_invariance": permutation_error <= 1e-12,
        "exact_zero_residual_without_active_tokens": fallback_residual_error == 0.0,
        "exact_clinical_only_fallback": fallback_fused_error == 0.0,
        "arbitrary_subset_finite": bool(np.isfinite(subset.fused_score).all()),
        "identity_embeddings_distinct": _minimum_pairwise_distance(
            model.identity_embeddings
        ) > 0.0,
        "status_encoding_active": status_sensitivity > 0.0,
        "quality_encoding_active": quality_sensitivity > 0.0,
        "cox_loss_finite": math.isfinite(loss),
        "cox_loss_shift_invariant": cox_shift_error <= 1e-12,
        "parameter_ceiling": model.parameter_count <= spec.maximum_parameter_count,
    }
    result: dict[str, object] = {
        "schema_version": "0.1",
        "study_id": "pattern_surv_hn",
        "stage": "U1.3/V1 smoke implementation",
        "model_id": MODEL_ID,
        "model_name": MODEL_NAME,
        "scope": "synthetic_structural_smoke_only_no_training",
        "framework": "numpy_reference_no_new_dependency",
        "input_modalities": list(MODALITY_ORDER),
        "input_dimensions": dict(spec.modality_input_dimensions),
        "token_dimension": spec.token_dimension,
        "quality_features": list(spec.quality_features),
        "parameter_count": model.parameter_count,
        "maximum_parameter_count": spec.maximum_parameter_count,
        "synthetic_rows": int(clinical.size),
        "metrics": {
            "permutation_max_abs_error": permutation_error,
            "fallback_residual_max_abs_error": fallback_residual_error,
            "fallback_fused_max_abs_error": fallback_fused_error,
            "status_sensitivity_max_abs_change": status_sensitivity,
            "quality_sensitivity_max_abs_change": quality_sensitivity,
            "identity_embedding_min_pairwise_distance": _minimum_pairwise_distance(
                model.identity_embeddings
            ),
            "cox_negative_partial_log_likelihood": loss,
            "cox_shift_invariance_error": cox_shift_error,
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "patient_level_data_used": False,
        "patient_level_output_written": False,
        "outcomes_used": False,
        "official_test_accessed": False,
        "external_data_accessed": False,
        "model_training_performed": False,
        "formal_development_cv_performed": False,
        "router_or_calibrator_used": False,
        "limitations": [
            "Fixed deterministic reference weights; not a fitted prognostic model.",
            "Structural smoke results do not support performance or generalization claims.",
            "Trainable framework and optimizer remain subject to a separate dependency approval.",
        ],
    }
    if _contains_sensitive_key(result):
        raise RuntimeError("aggregate smoke audit contains an identifier-like key")
    if not result["all_checks_pass"]:
        raise RuntimeError("one or more V1 structural smoke checks failed")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    spec_path = args.spec or root / DEFAULT_SPEC_RELATIVE
    output_path = args.output or root / DEFAULT_AUDIT_RELATIVE
    spec = V1SmokeSpec.from_yaml(spec_path)
    result = run_structural_smoke(spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

