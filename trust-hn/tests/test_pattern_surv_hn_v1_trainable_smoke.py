from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import torch

from trust_hn.pattern_surv_hn.hancock_contract import (
    BLOOD_FEATURES,
    ICD_FEATURES,
    TMA_FEATURES,
)
from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import MODALITY_ORDER, STATUS_LEVELS, V1SmokeSpec
from trust_hn.pattern_surv_hn.v1_trainable_smoke import (
    TorchModalityBatch,
    TrainableClinicalResidualDeepSetsCox,
    V1TrainableSmokeSpec,
    make_synthetic_survival_batch,
    negative_breslow_cox_loss,
    run_trainable_smoke,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_SPEC_PATH = (
    ROOT
    / "research_studies/01_pattern_surv_hn/core_backbone/U1_3_V1_smoke/"
    "frozen_v1_smoke_spec.yaml"
)
TRAINING_SPEC_PATH = (
    ROOT
    / "research_studies/01_pattern_surv_hn/core_backbone/U1_4_V1_trainable_smoke/"
    "frozen_v1_trainable_smoke_spec.yaml"
)


@pytest.fixture(scope="module")
def architecture() -> V1SmokeSpec:
    return V1SmokeSpec.from_yaml(ARCHITECTURE_SPEC_PATH)


@pytest.fixture(scope="module")
def training() -> V1TrainableSmokeSpec:
    return V1TrainableSmokeSpec.from_yaml(TRAINING_SPEC_PATH)


@pytest.fixture(scope="module")
def synthetic_batch(architecture, training):
    return make_synthetic_survival_batch(architecture, training)


@pytest.fixture(scope="module")
def audit_pair(architecture, training):
    return run_trainable_smoke(architecture, training), run_trainable_smoke(
        architecture, training
    )


def test_trainable_architecture_inherits_frozen_dimensions_and_parameter_count(architecture):
    model = TrainableClinicalResidualDeepSetsCox(architecture)
    assert architecture.modality_input_dimensions == {
        "blood": 2 * len(BLOOD_FEATURES),
        "icd": 2 * len(ICD_FEATURES),
        "tma": 2 * len(TMA_FEATURES),
    }
    assert model.parameter_count == 3225
    assert model.parameter_count <= architecture.maximum_parameter_count
    assert all(parameter.dtype == torch.float64 for parameter in model.parameters())


def test_trainable_forward_is_permutation_invariant(architecture, synthetic_batch):
    clinical, batches, _, _ = synthetic_batch
    model = TrainableClinicalResidualDeepSetsCox(architecture)
    canonical = model(clinical, batches)
    permuted = model(clinical, (batches[2], batches[0], batches[1]))
    torch.testing.assert_close(canonical.fused_score, permuted.fused_score, atol=1e-12, rtol=0)
    assert torch.equal(canonical.active_token_count, permuted.active_token_count)


def test_exact_clinical_fallback_ignores_inactive_nan_placeholders(
    architecture, synthetic_batch
):
    clinical, batches, _, _ = synthetic_batch
    model = TrainableClinicalResidualDeepSetsCox(architecture)
    absent = tuple(
        TorchModalityBatch(
            name=batch.name,
            content=torch.full_like(batch.content, torch.nan),
            active=torch.zeros_like(batch.active),
            status_index=torch.full_like(batch.status_index, STATUS_LEVELS.index("absent")),
            quality=torch.column_stack(
                [torch.ones(clinical.numel()), torch.zeros(clinical.numel())]
            ).to(torch.float64),
        )
        for batch in batches
    )
    result = model(clinical, absent)
    assert torch.equal(result.residual_score, torch.zeros_like(clinical))
    assert torch.equal(result.fused_score, clinical)
    assert torch.equal(result.active_token_count, torch.zeros_like(result.active_token_count))


def test_active_nonfinite_content_is_rejected(architecture, synthetic_batch):
    clinical, batches, _, _ = synthetic_batch
    model = TrainableClinicalResidualDeepSetsCox(architecture)
    batch = batches[0]
    active_row = int(torch.nonzero(batch.active, as_tuple=False)[0].item())
    broken_content = batch.content.clone()
    broken_content[active_row, 0] = torch.nan
    broken = replace(batch, content=broken_content)
    with pytest.raises(ValueError, match="active modality content must be finite"):
        model(clinical, (broken, *batches[1:]))


def test_gradient_reaches_trainable_parameters(architecture, synthetic_batch):
    clinical, batches, duration, event = synthetic_batch
    model = TrainableClinicalResidualDeepSetsCox(architecture)
    loss = negative_breslow_cox_loss(duration, event, model(clinical, batches).fused_score)
    loss.backward()
    gradients = [
        parameter.grad
        for parameter in model.parameters()
        if parameter.grad is not None
    ]
    assert gradients
    assert all(bool(torch.all(torch.isfinite(gradient))) for gradient in gradients)
    assert any(float(torch.linalg.vector_norm(gradient).item()) > 0 for gradient in gradients)


def test_differentiable_breslow_loss_is_finite_and_shift_invariant():
    duration = torch.tensor([2.0, 4.0, 5.0, 8.0, 10.0], dtype=torch.float64)
    event = torch.tensor([1, 0, 1, 1, 0], dtype=torch.bool)
    score = torch.tensor([0.7, -0.2, 0.4, -0.1, -0.5], dtype=torch.float64, requires_grad=True)
    loss = negative_breslow_cox_loss(duration, event, score)
    shifted = negative_breslow_cox_loss(duration, event, score + 19.0)
    assert bool(torch.isfinite(loss))
    assert float(shifted.item()) == pytest.approx(float(loss.item()), abs=1e-12)
    loss.backward()
    assert score.grad is not None
    assert bool(torch.all(torch.isfinite(score.grad)))


def test_synthetic_optimization_audit_is_deterministic_and_aggregate_only(
    training, audit_pair
):
    first, second = audit_pair
    assert first == second
    assert first["all_checks_pass"] is True
    assert first["metrics"]["relative_loss_reduction"] >= (
        training.minimum_relative_loss_reduction
    )
    assert first["checks"]["finite_nonzero_gradient"] is True
    assert first["checks"]["parameters_updated"] is True
    assert first["checks"]["posttrain_permutation_invariance"] is True
    assert first["checks"]["exact_clinical_only_fallback"] is True
    assert first["patient_level_data_used"] is False
    assert first["patient_level_output_written"] is False
    assert first["patient_model_checkpoint_written"] is False
    assert first["outcomes_used"] is False
    assert first["official_test_accessed"] is False
    assert first["external_data_accessed"] is False
    assert first["formal_development_cv_performed"] is False
    assert first["router_or_calibrator_used"] is False
    text = json.dumps(first).lower()
    for key in ("native_id", "patient_id", "case_id", "submitter_id"):
        assert key not in text
    assert tuple(MODALITY_ORDER) == ("blood", "icd", "tma")
