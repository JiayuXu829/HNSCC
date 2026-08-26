"""Locked pre-unseal and post-unseal V0 versus V1R confirmation runner.

The pre-unseal stage never reads official-test outcomes. It refits the frozen matched
25-member ensemble on development partitions, creates patient-level predictions in the
ignored results tree, and writes only aggregate/provenance receipts to the tracked
confirmation-protocol directory. The post-unseal stage is deliberately separate and
requires a sealed pre-unseal receipt before reading confirmation outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

from trust_hn.pattern_surv_hn.hancock_contract import (
    HancockContractBuilder,
    derive_postoperative_endpoint,
)
from trust_hn.pattern_surv_hn.v0_clinical_anchor import (
    CoxnetCandidate,
    V0Spec,
    _development_arrays,
    _event_stratified_splits,
    evaluate_predictions,
    structured_survival,
)
from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import V1SmokeSpec
from trust_hn.pattern_surv_hn.v1_development_cv import (
    MODALITY_FEATURES,
    _fit_anchor_for_split,
    _fit_modality_preprocessors,
    _fit_v1,
    _predict_model,
    _to_tensor_inputs,
    breslow_risk_at_horizon,
)
from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import STATUS_LEVELS

PROTOCOL_REL = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U2_V1R_confirmation_protocol"
)
RESCUE_REL = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U2_V1R_residual_shrinkage_rescue"
)
V0_REL = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U1_2_V0_clinical_anchor/frozen_v0_spec.yaml"
)
ARCH_REL = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U1_3_V1_smoke/frozen_v1_smoke_spec.yaml"
)
V0_OOF_REL = Path("results/predictions/pattern_surv_hn/U1_2_V0/v0_repeated_nested_oof_predictions.csv")
PRED_REL = Path("results/predictions/pattern_surv_hn/U2_V1R_confirmation")
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20260825
HORIZON = 730.5


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def json_safe(value):
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def load_rescue_folds(path: Path) -> dict[tuple[int, int], dict[str, float | int]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    folds = payload["results"]["folds"]
    if len(folds) != 25:
        raise RuntimeError(f"expected 25 frozen rescue fold records, found {len(folds)}")
    result = {}
    for row in folds:
        key = (int(row["repetition_seed"]), int(row["outer_fold"]))
        if key in result:
            raise RuntimeError(f"duplicate rescue fold record: {key}")
        result[key] = {
            "alpha": float(row["selected_anchor_alpha"]),
            "l1_ratio": float(row["selected_anchor_l1_ratio"]),
            "residual_penalty": float(row["selected_residual_penalty"]),
            "optimization_steps": int(row["selected_optimization_steps"]),
            "residual_scale": float(row["selected_residual_scale"]),
        }
    return result


def _validate_preconditions(root: Path) -> tuple[dict, dict, V0Spec, V1SmokeSpec, object, dict]:
    protocol_path = root / PROTOCOL_REL / "frozen_confirmation_protocol.yaml"
    protocol = load_yaml(protocol_path)
    if protocol["status"] != "FROZEN_READY_FOR_LOCKED_VALIDATION":
        raise RuntimeError("confirmation protocol is not in frozen executable state")
    if protocol["confirmation_population"]["official_hancock_test"] != (
        "eligible_by_researcher_outcome_untouched_confirmation_on_2026_08_26"
    ):
        raise RuntimeError("researcher-confirmed outcome-untouched cohort designation is missing")
    v0_path = root / V0_REL
    arch_path = root / ARCH_REL
    v0_spec = V0Spec.from_yaml(v0_path)
    architecture = V1SmokeSpec.from_yaml(arch_path)
    rescue_spec_path = root / RESCUE_REL / "frozen_v1r_rescue_spec.yaml"
    rescue_gate_path = root / RESCUE_REL / "frozen_v1r_exploratory_gate.yaml"
    rescue_spec = load_yaml(rescue_spec_path)
    rescue_gate = load_yaml(rescue_gate_path)
    if sha256_file(rescue_spec_path) != protocol["locked_model_artifacts"]["candidate"]["source_spec_sha256"]:
        raise RuntimeError("frozen V1R rescue spec hash differs from confirmation protocol")
    if sha256_file(rescue_gate_path) != protocol["locked_model_artifacts"]["candidate"]["source_gate_sha256"]:
        raise RuntimeError("frozen V1R rescue gate hash differs from confirmation protocol")
    if v0_spec.horizon_days != HORIZON:
        raise RuntimeError("V0 horizon differs from confirmation horizon")
    contract = HancockContractBuilder(root).build()
    metadata = contract.patient_frame().set_index("native_id")
    test = metadata[(metadata["official_partition"] == "test") & metadata["eligible"]]
    if len(test) != 152 or not test["outcome_sealed"].all():
        raise RuntimeError("HANCOCK OOD confirmation cohort is not the frozen 152-row sealed cohort")
    if test["duration_days"].notna().any() or test["event"].notna().any():
        raise RuntimeError("confirmation outcomes were exposed before pre-unseal prediction generation")
    return protocol, rescue_spec, v0_spec, architecture, contract, rescue_gate


def run_pre_unseal(root: Path) -> dict:
    protocol, rescue_spec, v0_spec, architecture, contract, rescue_gate = _validate_preconditions(root)
    rescue_folds = load_rescue_folds(root / RESCUE_REL / "aggregate_u2_v1r_rescue_audit.json")
    _, dev_ids, dev_event, dev_time, _ = _development_arrays(contract)
    metadata = contract.patient_frame().set_index("native_id")
    test_ids = metadata[(metadata["official_partition"] == "test") & metadata["eligible"]].index.to_numpy(dtype=str)
    test_frame = metadata.loc[test_ids]
    out_dir = root / PRED_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    members_dir = out_dir / "member_models"
    members_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    member_audit: list[dict[str, object]] = []
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)

    for repetition_seed in (17, 29, 43, 71, 101):
        splits = _event_stratified_splits(dev_event, 5, repetition_seed)
        for outer_fold, (train_idx, _) in enumerate(splits):
            key = (repetition_seed, outer_fold)
            selected = rescue_folds[key]
            train_ids = dev_ids[train_idx]
            train_events = dev_event[train_idx]
            train_times = dev_time[train_idx]
            candidate = CoxnetCandidate(selected["alpha"], selected["l1_ratio"])
            train_clinical, test_clinical, test_v0_risk, anchor_audit = _fit_anchor_for_split(
                contract, train_ids, test_ids, train_events, train_times, candidate, v0_spec
            )
            train_modalities, test_modalities, modality_audit = _fit_modality_preprocessors(
                contract, metadata, train_ids.tolist(), test_ids.tolist()
            )
            train_inputs = _to_tensor_inputs(train_clinical, train_modalities, train_times, train_events)
            # These are tensor-container placeholders only. The model forward path never reads
            # confirmation duration/event; the sealed contract has already asserted both are absent.
            test_inputs = _to_tensor_inputs(
                test_clinical, test_modalities, np.ones(len(test_ids), dtype=float),
                np.zeros(len(test_ids), dtype=bool),
            )
            fitted = _fit_v1(
                architecture,
                train_inputs,
                type("FrozenV1Spec", (), {
                    "learning_rate": float(rescue_spec["optimization"]["learning_rate"]),
                    "weight_decay": float(rescue_spec["optimization"]["weight_decay"]),
                    "gradient_clip_norm": float(rescue_spec["optimization"]["gradient_clip_norm"]),
                })(),
                type("FrozenCandidate", (), {
                    "residual_penalty": selected["residual_penalty"],
                    "optimization_steps": selected["optimization_steps"],
                    "residual_scale": selected["residual_scale"],
                })(),
            )
            train_fused, train_residual, _ = _predict_model(fitted.model, train_inputs)
            test_fused, test_residual, active_count = _predict_model(fitted.model, test_inputs)
            scale = selected["residual_scale"]
            if scale != 1.0:
                train_fused = train_fused - train_residual + scale * train_residual
                test_fused = test_clinical + scale * test_residual
            test_v1_risk = breslow_risk_at_horizon(
                train_times, train_events, train_fused, test_fused, HORIZON
            )
            model_path = members_dir / f"member_seed{repetition_seed}_fold{outer_fold}.pt"
            torch.save({
                "repetition_seed": repetition_seed,
                "outer_fold": outer_fold,
                "selected": selected,
                "state_dict": fitted.model.state_dict(),
                "train_breslow_duration": train_times,
                "train_breslow_event": train_events,
                "train_breslow_score": train_fused,
            }, model_path)
            for idx, native_id in enumerate(test_ids):
                rows.append({
                    "native_id": str(native_id),
                    "repetition_seed": repetition_seed,
                    "outer_fold": outer_fold,
                    "v0_score": float(test_clinical[idx]),
                    "v0_risk_24m": float(test_v0_risk[idx]),
                    "v1r_score": float(test_fused[idx]),
                    "v1r_risk_24m": float(test_v1_risk[idx]),
                    "active_modality_count": int(active_count[idx]),
                    "acquisition_pattern": str(test_frame.loc[str(native_id), "acquisition_pattern"]),
                    "usable_pattern": str(test_frame.loc[str(native_id), "usable_pattern"]),
                })
            member_audit.append({
                "repetition_seed": repetition_seed,
                "outer_fold": outer_fold,
                "train_n": int(len(train_ids)),
                "train_events": int(train_events.sum()),
                "test_n": int(len(test_ids)),
                "selected": selected,
                "clinical_preprocessing": anchor_audit,
                "modality_preprocessing": modality_audit,
                "model_parameter_count": int(fitted.model.parameter_count),
                "initial_training_cox_loss": fitted.initial_cox_loss,
                "final_training_cox_loss": fitted.final_cox_loss,
                "model_artifact": model_path.name,
            })

    raw = pd.DataFrame(rows).sort_values(["repetition_seed", "outer_fold", "native_id"]).reset_index(drop=True)
    expected_rows = 25 * 152
    if len(raw) != expected_rows or raw["native_id"].nunique() != 152:
        raise RuntimeError("locked prediction coverage is not exactly 25 x 152")
    aggregate = raw.groupby("native_id", sort=True).agg(
        v0_score=("v0_score", "mean"), v0_risk_24m=("v0_risk_24m", "mean"),
        v1r_score=("v1r_score", "mean"), v1r_risk_24m=("v1r_risk_24m", "mean"),
        member_count=("v1r_score", "size"), acquisition_pattern=("acquisition_pattern", "first"),
        usable_pattern=("usable_pattern", "first"),
    ).reset_index()
    if not (aggregate["member_count"] == 25).all():
        raise RuntimeError("patient-level aggregate member coverage is incomplete")
    raw_path = out_dir / "locked_member_predictions.csv"
    aggregate_path = out_dir / "locked_aggregate_predictions.csv"
    audit_path = out_dir / "member_audit.json"
    raw.to_csv(raw_path, index=False)
    aggregate.to_csv(aggregate_path, index=False)
    audit_path.write_text(json.dumps(json_safe({"members": member_audit}), indent=2) + "\n", encoding="utf-8")

    source_hashes = {key: sha256_file(path) for key, path in contract.source_paths.items()}
    input_manifest = {
        "schema_version": "0.1",
        "cohort_id": "HANCOCK_OOD_TEST",
        "cohort_role": "researcher_confirmed_outcome_untouched",
        "n_test_eligible": int(len(test_ids)),
        "all_test_patterns": sorted(set(test_frame["acquisition_pattern"])),
        "all_test_usable_patterns": sorted(set(test_frame["usable_pattern"])),
        "outcomes_present_in_contract": False,
        "source_sha256": source_hashes,
        "contract_aggregate_summary": contract.aggregate_summary(),
    }
    manifest_path = root / PROTOCOL_REL / "input_manifest.json"
    manifest_path.write_text(json.dumps(json_safe(input_manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_hash = sha256_file(manifest_path)
    (root / PROTOCOL_REL / "input_manifest.sha256").write_text(manifest_hash + "  input_manifest.json\n", encoding="utf-8")

    code_paths = [
        root / "src/trust_hn/pattern_surv_hn/hancock_contract.py",
        root / "src/trust_hn/pattern_surv_hn/v0_clinical_anchor.py",
        root / "src/trust_hn/pattern_surv_hn/v1_deep_sets_smoke.py",
        root / "src/trust_hn/pattern_surv_hn/v1_trainable_smoke.py",
        root / "src/trust_hn/pattern_surv_hn/v1_development_cv.py",
        root / "scripts/run_v1r_confirmation.py",
    ]
    code_hashes = {path.relative_to(root).as_posix(): sha256_file(path) for path in code_paths}
    dependency_path = root / "requirements-lock-confirmation.txt"
    dependency_path.write_text(
        "python==3.11\nnumpy==2.3.2\npandas==2.3.1\nPyYAML==6.0.2\n"
        "scikit-learn==1.7.1\nscikit-survival==0.25.0\nscipy==1.16.1\n"
        "torch==2.12.1+cpu\n", encoding="utf-8"
    )
    dependency_hash = sha256_file(dependency_path)
    prediction_hash_payload = b"".join(path.read_bytes() for path in (raw_path, aggregate_path, audit_path))
    prediction_hash = sha256_bytes(prediction_hash_payload)
    (root / PROTOCOL_REL / "locked_prediction_artifact.sha256").write_text(
        prediction_hash + "  locked_member_predictions.csv+locked_aggregate_predictions.csv+member_audit.json\n",
        encoding="utf-8",
    )
    receipt = {
        "schema_version": "0.1",
        "stage_id": "U2_V1R_LOCKED_PREDICTION_GENERATION",
        "status": "PREDICTIONS_SEALED_PRE_UNSEAL",
        "sealed_on": "2026-08-26",
        "cohort_id": "HANCOCK_OOD_TEST",
        "outcomes_read": False,
        "outcome_fields_in_prediction_inputs": False,
        "n_test": 152,
        "members": 25,
        "coverage": 1.0,
        "risk_aggregation": "arithmetic_mean_member_specific_24m_risk",
        "ranking_aggregation": "arithmetic_mean_member_specific_linear_predictor",
        "protocol_sha256": sha256_file(root / PROTOCOL_REL / "frozen_confirmation_protocol.yaml"),
        "input_manifest_sha256": manifest_hash,
        "v0_spec_sha256": sha256_file(root / V0_REL),
        "v1r_spec_sha256": sha256_file(root / RESCUE_REL / "frozen_v1r_rescue_spec.yaml"),
        "v1r_gate_sha256": sha256_file(root / RESCUE_REL / "frozen_v1r_exploratory_gate.yaml"),
        "architecture_spec_sha256": sha256_file(root / ARCH_REL),
        "development_v0_reference_oof_sha256": sha256_file(root / V0_OOF_REL),
        "source_code_sha256": code_hashes,
        "dependency_lock_sha256": dependency_hash,
        "locked_prediction_artifact_sha256": prediction_hash,
        "patient_level_outputs": "git_ignored",
        "tracked_artifacts_aggregate_only": True,
        "rescue_gate_reused_without_confirmation_reselection": True,
        "no_calibration_or_router": True,
        "no_post_unseal_refit": True,
    }
    receipt_path = root / PROTOCOL_REL / "pre_unseal_prediction_receipt.json"
    receipt_path.write_text(json.dumps(json_safe(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def _read_unsealed_test_outcomes(root: Path, test_ids: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
    builder = HancockContractBuilder(root)
    clinical_rows = json.loads(builder.source_paths["clinical"].read_text(encoding="utf-8-sig"))
    by_id = {str(row["patient_id"]): row for row in clinical_rows}
    duration, event = [], []
    for native_id in test_ids:
        row = by_id[str(native_id)]
        d, e = derive_postoperative_endpoint(
            row["days_to_last_information"], row["days_to_first_treatment"], row["survival_status"]
        )
        if not np.isfinite(d) or d <= 0:
            raise RuntimeError("outcome-unsealed test cohort contains nonpositive endpoint")
        duration.append(d)
        event.append(e)
    return np.asarray(duration, dtype=float), np.asarray(event, dtype=bool)


def summarize_delta(v0: dict, v1: dict) -> dict:
    keys = ["ipcw_brier_24m", "harrell_c", "uno_c_24m", "auc_24m", "calibration_in_the_large_24m", "calibration_slope_24m", "mean_predicted_risk_24m"]
    return {key: float(v1[key] - v0[key]) if np.isfinite(v0[key]) and np.isfinite(v1[key]) else None for key in keys}


def run_after_unseal(root: Path) -> dict:
    protocol_dir = root / PROTOCOL_REL
    receipt_path = protocol_dir / "pre_unseal_prediction_receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError("cannot unseal outcomes before pre-unseal prediction receipt exists")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    if receipt["status"] != "PREDICTIONS_SEALED_PRE_UNSEAL" or receipt["outcomes_read"]:
        raise RuntimeError("pre-unseal receipt does not authorize one-time locked evaluation")
    if receipt["protocol_sha256"] != sha256_file(protocol_dir / "frozen_confirmation_protocol.yaml"):
        raise RuntimeError("frozen confirmation protocol changed after prediction sealing")
    pred_path = root / PRED_REL / "locked_aggregate_predictions.csv"
    raw_path = root / PRED_REL / "locked_member_predictions.csv"
    pred = pd.read_csv(pred_path, dtype={"native_id": str})
    if sha256_bytes((root / PRED_REL / "locked_member_predictions.csv").read_bytes() + pred_path.read_bytes() + (root / PRED_REL / "member_audit.json").read_bytes()) != receipt["locked_prediction_artifact_sha256"]:
        raise RuntimeError("locked prediction artifact hash mismatch")
    test_ids = pred["native_id"].astype(str).to_numpy()
    duration, event = _read_unsealed_test_outcomes(root, test_ids)
    if len(pred) != 152 or int(event.sum()) < 1:
        raise RuntimeError("invalid unsealed confirmation outcome shape")
    eval_y = structured_survival(event, duration)
    metrics_v0 = evaluate_predictions(eval_y, eval_y, pred["v0_score"], pred["v0_risk_24m"], HORIZON)
    metrics_v1 = evaluate_predictions(eval_y, eval_y, pred["v1r_score"], pred["v1r_risk_24m"], HORIZON)
    delta = summarize_delta(metrics_v0, metrics_v1)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    bootstrap_deltas = {key: [] for key in ["ipcw_brier_24m", "uno_c_24m", "harrell_c", "auc_24m"]}
    event_idx = np.flatnonzero(event)
    censor_idx = np.flatnonzero(~event)
    for _ in range(BOOTSTRAP_REPS):
        sample = np.concatenate([
            rng.choice(event_idx, size=len(event_idx), replace=True),
            rng.choice(censor_idx, size=len(censor_idx), replace=True),
        ])
        rng.shuffle(sample)
        boot_y = structured_survival(event[sample], duration[sample])
        b0 = evaluate_predictions(boot_y, boot_y, pred["v0_score"].to_numpy()[sample], pred["v0_risk_24m"].to_numpy()[sample], HORIZON)
        b1 = evaluate_predictions(boot_y, boot_y, pred["v1r_score"].to_numpy()[sample], pred["v1r_risk_24m"].to_numpy()[sample], HORIZON)
        for key in bootstrap_deltas:
            if np.isfinite(b0[key]) and np.isfinite(b1[key]):
                bootstrap_deltas[key].append(float(b1[key] - b0[key]))
    bootstrap_summary = {}
    for key, values in bootstrap_deltas.items():
        arr = np.asarray(values, dtype=float)
        bootstrap_summary[key] = {
            "replicates": int(len(arr)),
            "mean": float(np.mean(arr)) if len(arr) else None,
            "ci95_lower": float(np.quantile(arr, 0.025)) if len(arr) else None,
            "ci95_upper": float(np.quantile(arr, 0.975)) if len(arr) else None,
        }
    result = {
        "schema_version": "0.1",
        "stage_id": "U2_V1R_LOCKED_CONFIRMATION_EVALUATION",
        "evaluated_on": "2026-08-26",
        "cohort_id": "HANCOCK_OOD_TEST",
        "outcomes_unsealed_after_prediction_seal": True,
        "n": int(len(pred)),
        "events": int(event.sum()),
        "horizon_days": HORIZON,
        "V0": metrics_v0,
        "V1R": metrics_v1,
        "delta_V1R_minus_V0": delta,
        "bootstrap": {"method": "patient_level_stratified_bootstrap", "replicates": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED, "summary": bootstrap_summary},
        "predeclared_boundaries": {
            "delta_ipcw_brier_no_harm_maximum": 0.005,
            "supported_pattern_worst_brier_regret_maximum": 0.020,
            "full_coverage_required": True,
        },
        "coverage": 1.0,
        "pattern_summary": pred.groupby("acquisition_pattern").size().to_dict(),
        "governance": {
            "post_unseal_refit": False,
            "calibration_bridge_trained": False,
            "router_trained": False,
            "selective_patient_removal": False,
            "patient_level_results_tracked": False,
            "historical_phase6_discrepancy_rewritten": False,
        },
    }
    result_path = protocol_dir / "aggregate_confirmation_results.json"
    result_path.write_text(json.dumps(json_safe(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit = (
        "# U2/V1R locked confirmation audit\n\n"
        "- The researcher-confirmed HANCOCK OOD cohort was designated outcome-untouched before prediction generation.\n"
        "- Twenty-five matched V0/V1R members were fit only on development training partitions.\n"
        "- Prediction, code, dependency, input and protocol hashes were sealed before outcomes were read.\n"
        "- Confirmation outcomes were then unsealed once, and the frozen estimands plus 2,000 stratified patient bootstraps were run without refitting, calibration, routing or patient removal.\n"
        "- This result is confirmation evidence for the frozen V1R rescue protocol; it does not convert the original V1 decision into a preregistered pass or establish clinical utility.\n"
    )
    (protocol_dir / "confirmation_audit.md").write_text(audit, encoding="utf-8")
    report = "# U2/V1R locked confirmation stage report\n\n" + json.dumps(json_safe({"stage": result["stage_id"], "n": result["n"], "events": result["events"], "delta_V1R_minus_V0": result["delta_V1R_minus_V0"], "bootstrap": result["bootstrap"]}), indent=2) + "\n"
    (protocol_dir / "stage_report.md").write_text(report, encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--pre-unseal", action="store_true")
    parser.add_argument("--evaluate-after-unseal", action="store_true")
    args = parser.parse_args(argv)
    if args.pre_unseal == args.evaluate_after_unseal:
        parser.error("choose exactly one of --pre-unseal or --evaluate-after-unseal")
    root = args.project_root.resolve()
    result = run_pre_unseal(root) if args.pre_unseal else run_after_unseal(root)
    print(json.dumps(json_safe(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
