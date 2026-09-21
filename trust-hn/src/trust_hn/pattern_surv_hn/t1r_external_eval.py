"""Post-hoc external characterization of the frozen T1R transcriptome mode

Fits a single T1R model on the full TCGA development cohort (with the anchor candidate and
residual shrinkage selected via development-only inner CV), then applies it without refitting
to the GEO cohorts GSE65858 and GSE41613. No external outcome is used for fitting or tuning;
this is descriptive characterization, not external validation.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from trust_hn.evaluation.phase3 import NumericMatrixPreprocessor
from trust_hn.evaluation.phase6 import load_phase6_outcomes
from trust_hn.pattern_surv_hn.hancock_contract import FoldBoundMixedPreprocessor
from trust_hn.pattern_surv_hn.t1r_development_cv import (
    T1RSpec,
    _active_for,
    _fit_t1r,
    _inner_select_t1r,
    _predict_model,
    _select_anchor,
    _to_tensor_inputs,
)
from trust_hn.pattern_surv_hn.t1r_model import TrainableClinicalResidualTranscriptomeCox
from trust_hn.pattern_surv_hn.transcriptome_contract import (
    ANCHOR_CATEGORICAL_FEATURES,
    ANCHOR_NUMERIC_FEATURES,
    TranscriptomeContract,
)
from trust_hn.pattern_surv_hn.v0_clinical_anchor import (
    CoxnetCandidate,
    FittedAnchor,
    _fit_anchor,
    _predict_anchor,
    assert_aggregate_only,
    evaluate_predictions,
    structured_survival,
)
from trust_hn.pattern_surv_hn.v1_development_cv import (
    _json_safe,
    _sha256,
    breslow_risk_at_horizon,
)

ANALYSIS_DATE = "2026-09-20"
STAGE_ID = "U8E_T1R_EXTERNAL_CHARACTERIZATION"
DEFAULT_SPEC_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U8_T1R_transcriptome_residual_shrinkage/frozen_t1r_transcriptome_spec.yaml"
)
DEFAULT_AUDIT_RELATIVE = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U8E_T1R_external_characterization/aggregate_t1r_external_characterization_audit.json"
)
DEFAULT_PATIENT_OUTPUT_RELATIVE = Path("results/predictions/pattern_surv_hn/U8_T1R_external")
EXTERNAL_COHORTS = ("GSE65858", "GSE41613")


@dataclass(frozen=True)
class FittedT1RApplication:
    anchor_candidate: CoxnetCandidate
    selected: object
    anchor_prep: FoldBoundMixedPreprocessor
    anchor_fitted: FittedAnchor
    modality_prep: NumericMatrixPreprocessor
    model: TrainableClinicalResidualTranscriptomeCox
    dev_time: np.ndarray
    dev_event: np.ndarray
    dev_fused_score: np.ndarray


def fit_full_development_t1r(
    contract: TranscriptomeContract, spec: T1RSpec, seed: int
) -> FittedT1RApplication:
    ids, event, time = contract.development_arrays()
    anchor_spec = spec.anchor_spec
    anchor_candidate = _select_anchor(contract, ids, event, time, anchor_spec, seed)
    selected, _ = _inner_select_t1r(
        contract, ids, event, time, anchor_candidate, anchor_spec, spec, seed
    )
    anchor_prep = FoldBoundMixedPreprocessor(
        numeric=ANCHOR_NUMERIC_FEATURES,
        categorical=ANCHOR_CATEGORICAL_FEATURES,
        allowed_fit_ids=set(ids.tolist()),
    )
    anchor_train = anchor_prep.fit_transform(contract.anchor, ids.tolist())
    y = structured_survival(event, time)
    anchor_fitted = _fit_anchor(
        anchor_train.values, y, anchor_candidate, anchor_spec, anchor_train.feature_names
    )
    modality_prep = NumericMatrixPreprocessor(top_k=spec.top_k)
    modality_train = modality_prep.fit_transform(contract.modality)
    train_inputs = _to_tensor_inputs(
        anchor_fitted.model.predict(anchor_train.values),
        modality_train,
        _active_for(contract, ids),
        time,
        event,
    )
    fitted = _fit_t1r(spec.top_k, spec.residual_hidden_dim, seed, train_inputs, spec, selected)
    fused, residual = _predict_model(fitted.model, train_inputs)
    if selected.residual_scale != 1.0:
        fused = fused - residual + selected.residual_scale * residual
    return FittedT1RApplication(
        anchor_candidate, selected, anchor_prep, anchor_fitted, modality_prep,
        fitted.model, time, event, fused,
    )


def _external_scores(
    application: FittedT1RApplication, contract: TranscriptomeContract, spec: T1RSpec
):
    ids = contract.native_ids
    anchor_block = application.anchor_prep.transform(contract.anchor, ids.tolist())
    anchor_score, anchor_risk = _predict_anchor(
        application.anchor_fitted, anchor_block.values, spec.horizon_days
    )
    modality_matrix = application.modality_prep.transform(contract.modality)
    application.model.eval()
    with torch.no_grad():
        forward = application.model(
            torch.as_tensor(anchor_score, dtype=torch.float64),
            torch.as_tensor(modality_matrix, dtype=torch.float64),
            torch.as_tensor(_active_for(contract, ids), dtype=torch.bool),
        )
    fused = forward.fused_score.numpy()
    residual = forward.residual_score.numpy()
    if application.selected.residual_scale != 1.0:
        residual = application.selected.residual_scale * residual
        fused = anchor_score + residual
    t1r_risk = breslow_risk_at_horizon(
        application.dev_time, application.dev_event, application.dev_fused_score,
        fused, spec.horizon_days,
    )
    return anchor_score, anchor_risk, fused, residual, t1r_risk


def characterize_external(
    root: Path,
    cohort: str,
    spec: T1RSpec,
    application: FittedT1RApplication,
    *,
    patient_output_dir: Path | None = None,
) -> dict:
    contract = TranscriptomeContract.from_external(root, cohort)
    outcomes = load_phase6_outcomes(root, cohort, contract.native_ids)
    if tuple(outcomes.ids.astype(str)) != tuple(contract.native_ids):
        raise ValueError(
            "external outcome IDs must align with the frozen transcriptome contract"
        )
    anchor_score, anchor_risk, fused, residual, t1r_risk = _external_scores(
        application, contract, spec
    )
    dev_y = structured_survival(application.dev_event, application.dev_time)
    ext_y = structured_survival(outcomes.event, outcomes.time)
    anchor_metrics = evaluate_predictions(
        dev_y, ext_y, anchor_score, anchor_risk, spec.horizon_days
    )
    t1r_metrics = evaluate_predictions(
        dev_y, ext_y, fused, t1r_risk, spec.horizon_days
    )
    metric_names = (
        "ipcw_brier_24m", "harrell_c", "uno_c_24m", "auc_24m",
        "calibration_in_the_large_24m", "calibration_slope_24m",
        "mean_predicted_risk_24m",
    )
    delta = {name: float(t1r_metrics[name] - anchor_metrics[name]) for name in metric_names}
    rows = []
    for local, native_id in enumerate(contract.native_ids):
        rows.append({
            "native_id": str(native_id),
            "duration_days": float(outcomes.time[local]),
            "event": int(outcomes.event[local]),
            "transcriptome_active": int(contract.active[local]),
            "v0_risk_score": float(anchor_score[local]),
            "v0_risk_24m": float(anchor_risk[local]),
            "t1r_residual_score": float(residual[local]),
            "t1r_risk_score": float(fused[local]),
            "t1r_risk_24m": float(t1r_risk[local]),
            "t1r_survival_24m": float(1.0 - t1r_risk[local]),
        })
    if patient_output_dir is not None:
        patient_output_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(
            patient_output_dir / f"t1r_{cohort.casefold()}_external_predictions.csv",
            index=False,
        )
    return {
        "cohort": cohort,
        "role": contract.role,
        "n": len(outcomes.ids),
        "events": int(outcomes.event.sum()),
        "selected_anchor_alpha": application.anchor_candidate.alpha,
        "selected_anchor_l1_ratio": application.anchor_candidate.l1_ratio,
        "selected_residual_penalty": application.selected.residual_penalty,
        "selected_optimization_steps": application.selected.optimization_steps,
        "selected_residual_scale": application.selected.residual_scale,
        "V0_metrics": anchor_metrics,
        "T1R_metrics": t1r_metrics,
        "delta_T1R_minus_V0": delta,
    }


def run_t1r_external_eval(
    project_root: Path,
    *,
    spec_path: Path | None = None,
    patient_output_dir: Path | None = None,
    aggregate_audit_path: Path | None = None,
    external_seed: int = 20260907,
    verbose: bool = False,
):
    root = Path(project_root).resolve()
    spec_path = Path(spec_path or root / DEFAULT_SPEC_RELATIVE).resolve()
    patient_output_dir = Path(
        patient_output_dir or root / DEFAULT_PATIENT_OUTPUT_RELATIVE
    ).resolve()
    aggregate_audit_path = Path(
        aggregate_audit_path or root / DEFAULT_AUDIT_RELATIVE
    ).resolve()
    allowed_patient_root = (root / "results/predictions/pattern_surv_hn").resolve()
    if allowed_patient_root not in patient_output_dir.parents:
        raise ValueError(
            "patient-level outputs must remain under results/predictions/pattern_surv_hn"
        )

    spec = T1RSpec.from_yaml(spec_path)
    torch.use_deterministic_algorithms(spec.deterministic_algorithms)
    torch.set_num_threads(1)
    contract = TranscriptomeContract.from_development(root)
    application = fit_full_development_t1r(contract, spec, external_seed)
    cohort_results = []
    for cohort in EXTERNAL_COHORTS:
        result = characterize_external(
            root, cohort, spec, application, patient_output_dir=patient_output_dir
        )
        cohort_results.append(result)
        if verbose:
            print(
                f"cohort={cohort} n={result['n']} events={result['events']} "
                f"delta_brier={result['delta_T1R_minus_V0']['ipcw_brier_24m']:.6f}",
                flush=True,
            )

    payload = {
        "schema_version": "0.1", "study_id": "pattern_surv_hn",
        "stage_id": STAGE_ID, "analysis_label": "post_hoc_exploratory_characterization",
        "completed_on": ANALYSIS_DATE,
        "model": {
            "id": "T1R",
            "name": "Clinical_Residual_Transcriptome_Cox_inner_selected_shrinkage",
            "fitted_on": "TCGA-HNSC_full_development",
            "external_seed": external_seed,
            "selected_anchor_alpha": application.anchor_candidate.alpha,
            "selected_anchor_l1_ratio": application.anchor_candidate.l1_ratio,
            "selected_residual_penalty": application.selected.residual_penalty,
            "selected_optimization_steps": application.selected.optimization_steps,
            "selected_residual_scale": application.selected.residual_scale,

            "parameter_count": application.model.parameter_count,
        },
        "cohorts": cohort_results,
        "governance": {
            "post_hoc_exploratory": True,
            "outcomes_already_consumed": True,
            "external_outcomes_used_for_fitting_or_tuning": False,
            "external_validation_claim_allowed": False,
            "confirmatory_claim_allowed": False,
            "phase6_outputs_overwritten": False,
            "tracked_artifacts_aggregate_only": True,
            "patient_level_predictions_git_ignored": True,
        },
        "artifacts": {
            "frozen_spec": spec_path.relative_to(root).as_posix(),
            "frozen_spec_sha256": _sha256(spec_path),
            "patient_output_relative_path": patient_output_dir.relative_to(root).as_posix(),
            "patient_predictions": [
                {
                    "cohort": cohort,
                    "relative_path": (
                        patient_output_dir / f"t1r_{cohort.casefold()}_external_predictions.csv"
                    ).relative_to(root).as_posix(),
                    "sha256": _sha256(
                        patient_output_dir / f"t1r_{cohort.casefold()}_external_predictions.csv"
                    ),
                    "tracked": False,
                }
                for cohort in EXTERNAL_COHORTS
            ],
        },
        "limitations": [
            "Descriptive external characterization only; not external validation.",
            "GEO outcomes were previously consumed during Phase 6.",
            "A single T1R fit on full TCGA development is applied without external refitting.",
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
    parser.add_argument("--patient-output-dir", type=Path)
    parser.add_argument("--aggregate-audit", type=Path)
    parser.add_argument("--external-seed", type=int, default=20260907)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    result = run_t1r_external_eval(
        args.project_root, spec_path=args.spec,
        patient_output_dir=args.patient_output_dir,
        aggregate_audit_path=args.aggregate_audit, external_seed=args.external_seed,
        verbose=args.verbose,
    )
    print(json.dumps(result["cohorts"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
