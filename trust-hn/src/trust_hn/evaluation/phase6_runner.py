"""Reproducible Phase 6 pre-unseal prediction and locked evaluation workflow."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from trust_hn.data.phase6_data import (
    CohortFeatures,
    load_geo_features,
    load_hancock_features,
    load_phase6_development_data,
    load_radcure_features,
    verify_frozen_cohort_manifest,
)
from trust_hn.evaluation.phase3 import _assert_aggregate_privacy
from trust_hn.evaluation.phase6 import (
    OutcomeData,
    Phase6StressSystem,
    action_summary,
    aggregate_seed_predictions,
    decision_curve_rows,
    gated_external_predictions,
    load_phase6_configuration,
    load_phase6_outcomes,
    model_metrics,
    paired_bootstrap_metrics,
    paired_comparison_metrics,
    paired_prediction_set_bootstrap,
    percentile_intervals,
)
from trust_hn.governance import FreezeRecord, SealedTestError
from trust_hn.metrics.survival import evaluate_survival_predictions
from trust_hn.phase6_governance import (
    assert_token_absent_from_tracked_files,
    consume_phase6_authorization,
    register_phase6_authorization,
)
from trust_hn.utils.hashing import sha256_file

matplotlib.rcParams["svg.hashsalt"] = "trust-hn-phase6"

RADCURE_ASSAYS = ("original", "shuffled_full", "randomized_sampled_full")
PRIMARY_COHORTS = ("RADCURE", "HANCOCK", "GSE65858", "GSE41613")
METRIC_COLUMNS = ("ipcw_brier", "harrell_c", "uno_c", "auc_horizon")
DECISION_FILES = (
    "configs/phase6_evaluation.json",
    "configs/phase6_governance.json",
    "src/trust_hn/data/radcure_rds.py",
    "src/trust_hn/data/phase6_data.py",
    "src/trust_hn/evaluation/phase6.py",
    "src/trust_hn/evaluation/phase6_runner.py",
    "src/trust_hn/phase6_governance.py",
    "scripts/audit_radcure_rds.py",
    "scripts/run_phase6.py",
    "tests/test_radcure_rds.py",
    "tests/test_phase6_data.py",
    "tests/test_phase6_statistics.py",
    "tests/test_phase6_governance.py",
    "tests/test_phase6_runner.py",
    "pyproject.toml",
    "environment.yml",
)


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _profile_coverages(phase6: Mapping[str, object]) -> tuple[float, ...]:
    names = [str(phase6["primary_gate_profile"])] + [
        str(value) for value in phase6["sensitivity_gate_profiles"]  # type: ignore[index]
    ]
    values = sorted({float(name.rsplit("_", 1)[-1]) / 100.0 for name in names})
    return tuple(values)


def _profile_label(coverage: float) -> str:
    return str(round(float(coverage) * 100))


def _prediction_stem(cohort: str, assay: str = "original") -> str:
    return f"{cohort.lower()}__{assay}"


def prediction_path(
    project_root: Path,
    cohort: str,
    *,
    assay: str = "original",
    seed: int | None = None,
    profile: str | None = None,
) -> Path:
    stem = _prediction_stem(cohort, assay)
    if seed is not None:
        suffix = f"seed{seed}"
    elif profile is not None:
        suffix = f"aggregate{profile}"
    else:
        raise ValueError("seed or profile is required")
    return Path(project_root) / "results/predictions/phase6" / f"{stem}__{suffix}.csv"


def _assert_outcomes_unseen(project_root: Path) -> None:
    freeze = FreezeRecord.load(Path(project_root) / "configs/analysis_freeze.yaml")
    if freeze.payload.get("phase6_outcomes_seen") is not False:
        raise SealedTestError("pre-unseal prediction preparation is no longer permitted")


def _save_seed_frame(
    project_root: Path,
    cohort: CohortFeatures,
    frame: pd.DataFrame,
    *,
    assay: str,
    seed: int,
) -> Path:
    output = frame.copy()
    output.insert(0, "native_id", cohort.ids.astype(str))
    output.insert(1, "cohort", cohort.cohort)
    output.insert(2, "assay", assay)
    output.insert(3, "seed", int(seed))
    path = prediction_path(project_root, cohort.cohort, assay=assay, seed=seed)
    _atomic_csv(path, output)
    return path


def _aggregate_profiles(
    project_root: Path,
    cohort: CohortFeatures,
    frames: Sequence[pd.DataFrame],
    *,
    assay: str,
    coverages: Sequence[float],
) -> tuple[list[Path], list[dict[str, object]]]:
    paths: list[Path] = []
    summaries: list[dict[str, object]] = []
    for coverage in coverages:
        label = _profile_label(coverage)
        aggregate = aggregate_seed_predictions(frames, primary_profile=label)
        output = aggregate.copy()
        output.insert(0, "native_id", cohort.ids.astype(str))
        output.insert(1, "cohort", cohort.cohort)
        output.insert(2, "assay", assay)
        output.insert(3, "gate_profile", label)
        path = prediction_path(project_root, cohort.cohort, assay=assay, profile=label)
        _atomic_csv(path, output)
        paths.append(path)
        counts = aggregate["b7_action"].value_counts()
        summaries.append(
            {
                "cohort": cohort.cohort,
                "assay": assay,
                "gate_profile": label,
                "patient_count": len(cohort.ids),
                "augment_count": int(counts.get("AUGMENT", 0)),
                "fallback_count": int(counts.get("FALLBACK", 0)),
                "abstain_count": int(counts.get("ABSTAIN", 0)),
            }
        )
    return paths, summaries


def _fit_ecosystem(
    project_root: Path,
    development_study: str,
    external: Mapping[str, CohortFeatures],
    *,
    assay: str,
    seeds: Sequence[int],
    bootstrap_size: int,
    coverages: Sequence[float],
    model_config: Mapping[str, object],
) -> tuple[list[Path], list[dict[str, object]]]:
    development = load_phase6_development_data(
        project_root, development_study, assay=assay
    )
    by_cohort: dict[str, list[pd.DataFrame]] = {key: [] for key in external}
    paths: list[Path] = []
    for seed in seeds:
        system = Phase6StressSystem(
            development, model_config, int(seed), int(bootstrap_size)
        ).fit()
        for key, cohort in external.items():
            frame = gated_external_predictions(
                system, development, cohort, seed=int(seed), coverages=coverages
            )
            by_cohort[key].append(frame)
            paths.append(
                _save_seed_frame(
                    project_root, cohort, frame, assay=assay, seed=int(seed)
                )
            )
    summaries: list[dict[str, object]] = []
    for key, cohort in external.items():
        aggregate_paths, aggregate_summaries = _aggregate_profiles(
            project_root,
            cohort,
            by_cohort[key],
            assay=assay,
            coverages=coverages,
        )
        paths.extend(aggregate_paths)
        summaries.extend(aggregate_summaries)
    return paths, summaries


def prepare_phase6_predictions(
    project_root: Path,
    *,
    seeds: Sequence[int] | None = None,
    bootstrap_size: int | None = None,
) -> dict[str, object]:
    """Fit frozen systems and write outcome-free patient-level predictions."""
    root = Path(project_root).resolve()
    _assert_outcomes_unseen(root)
    cohorts = verify_frozen_cohort_manifest(root)
    phase6, model_config = load_phase6_configuration(root)
    configured_seeds = tuple(int(value) for value in phase6["seeds"])
    selected_seeds = tuple(int(value) for value in (seeds or configured_seeds))
    selected_bootstrap = int(
        bootstrap_size
        if bootstrap_size is not None
        else phase6["model_uncertainty_bootstrap_ensemble_size"]
    )
    coverages = _profile_coverages(phase6)
    paths: list[Path] = []
    summaries: list[dict[str, object]] = []

    for assay in RADCURE_ASSAYS:
        external = load_radcure_features(root, role="sealed_test", assay=assay)
        new_paths, new_summaries = _fit_ecosystem(
            root,
            "RADCURE",
            {"RADCURE": external},
            assay=assay,
            seeds=selected_seeds,
            bootstrap_size=selected_bootstrap,
            coverages=coverages,
            model_config=model_config,
        )
        paths.extend(new_paths)
        summaries.extend(new_summaries)

    hancock = load_hancock_features(root, role="sealed_test")
    new_paths, new_summaries = _fit_ecosystem(
        root,
        "HANCOCK",
        {"HANCOCK": hancock},
        assay="original",
        seeds=selected_seeds,
        bootstrap_size=selected_bootstrap,
        coverages=coverages,
        model_config=model_config,
    )
    paths.extend(new_paths)
    summaries.extend(new_summaries)

    geo = {
        "GSE65858": load_geo_features(root, "GSE65858", build_cache=True),
        "GSE41613": load_geo_features(root, "GSE41613", build_cache=True),
    }
    new_paths, new_summaries = _fit_ecosystem(
        root,
        "TCGA-HNSC",
        geo,
        assay="original",
        seeds=selected_seeds,
        bootstrap_size=selected_bootstrap,
        coverages=coverages,
        model_config=model_config,
    )
    paths.extend(new_paths)
    summaries.extend(new_summaries)

    production_complete = (
        selected_seeds == configured_seeds
        and selected_bootstrap
        == int(phase6["model_uncertainty_bootstrap_ensemble_size"])
    )
    receipt = {
        "schema_version": "1.0",
        "phase": "Phase 6 outcome-free pre-unseal prediction preparation",
        "completed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "status": "COMPLETE" if production_complete else "SMOKE_ONLY",
        "outcomes_loaded": False,
        "cohorts": cohorts,
        "seeds": list(selected_seeds),
        "bootstrap_ensemble_size": selected_bootstrap,
        "gate_profiles": [_profile_label(value) for value in coverages],
        "prediction_file_count": len(paths),
        "prediction_file_sha256": {
            str(path.relative_to(root)).replace("\\", "/"): sha256_file(path)
            for path in sorted(paths)
        },
        "aggregate_action_counts": summaries,
        "patient_level_outputs_git_ignored": True,
    }
    receipt_path = root / "results/manifests/phase6_preunseal_prediction_receipt.json"
    _atomic_json(receipt_path, receipt)
    return receipt


def _load_preflight_receipt(project_root: Path) -> dict[str, object]:
    path = Path(project_root) / "results/manifests/phase6_preunseal_prediction_receipt.json"
    if not path.is_file():
        raise SealedTestError("Phase 6 pre-unseal prediction receipt is missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "COMPLETE" or payload.get("outcomes_loaded") is not False:
        raise SealedTestError("Phase 6 production preflight is incomplete")
    for relative, expected in dict(payload["prediction_file_sha256"]).items():
        path = Path(project_root) / str(relative)
        if not path.is_file() or sha256_file(path) != str(expected):
            raise SealedTestError(f"pre-unseal prediction hash mismatch: {relative}")
    return payload


def register_authorization(project_root: Path, token_file: Path) -> dict[str, object]:
    """Create/read an ignored token and register only its hash."""
    root = Path(project_root).resolve()
    _assert_outcomes_unseen(root)
    _load_preflight_receipt(root)
    token_path = token_file if token_file.is_absolute() else root / token_file
    token_path.parent.mkdir(parents=True, exist_ok=True)
    if not token_path.exists():
        token_path.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise SealedTestError("approval token file is empty")
    assert_token_absent_from_tracked_files(root, token)
    payload = register_phase6_authorization(
        root,
        approval_token=token,
        decision_files=DECISION_FILES,
        approved_by="project owner via explicit Phase 6 instruction",
        approved_at="2026-08-08",
    )
    assert_token_absent_from_tracked_files(root, token)
    return {
        "status": "REGISTERED",
        "approval_token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
        "decision_file_count": len(DECISION_FILES),
        "phase6_outcomes_seen": payload["phase6_outcomes_seen"],
        "token_file_git_ignored": True,
    }


def _read_prediction(
    project_root: Path,
    cohort: str,
    expected_ids: Sequence[str],
    *,
    assay: str = "original",
    profile: str = "90",
) -> pd.DataFrame:
    path = prediction_path(project_root, cohort, assay=assay, profile=profile)
    frame = pd.read_csv(path, dtype={"native_id": "string"})
    observed = frame["native_id"].astype(str).to_numpy()
    expected = np.asarray(expected_ids, dtype=str)
    if not np.array_equal(observed, expected):
        raise ValueError(f"prediction ID alignment mismatch for {cohort}/{assay}/{profile}")
    return frame.drop(columns=["native_id", "cohort", "assay", "gate_profile"])


def _feature_bundle(project_root: Path, cohort: str) -> tuple[object, CohortFeatures]:
    if cohort == "RADCURE":
        return (
            load_phase6_development_data(project_root, "RADCURE"),
            load_radcure_features(project_root, role="sealed_test"),
        )
    if cohort == "HANCOCK":
        return (
            load_phase6_development_data(project_root, "HANCOCK"),
            load_hancock_features(project_root, role="sealed_test"),
        )
    return (
        load_phase6_development_data(project_root, "TCGA-HNSC"),
        load_geo_features(project_root, cohort, build_cache=True),
    )


def _paired_prediction_point_differences(
    development: object,
    outcomes: OutcomeData,
    reference: pd.DataFrame,
    controls: Mapping[str, pd.DataFrame],
    *,
    horizon: float,
    survival_floor: float,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for control_name, control in controls.items():
        for model in ("B4", "B5", "B6", "B7"):
            prefix = model.lower()
            ref_score = reference[f"{prefix}_score"].to_numpy(dtype=float)
            ref_risk = reference[f"{prefix}_risk"].to_numpy(dtype=float)
            ctl_score = control[f"{prefix}_score"].to_numpy(dtype=float)
            ctl_risk = control[f"{prefix}_risk"].to_numpy(dtype=float)
            finite = (
                np.isfinite(ref_score)
                & np.isfinite(ref_risk)
                & np.isfinite(ctl_score)
                & np.isfinite(ctl_risk)
            )
            left = evaluate_survival_predictions(
                development.train_event,
                development.train_time,
                outcomes.event[finite],
                outcomes.time[finite],
                ref_score[finite],
                ref_risk[finite],
                horizon,
                survival_floor=survival_floor,
            )
            right = evaluate_survival_predictions(
                development.train_event,
                development.train_time,
                outcomes.event[finite],
                outcomes.time[finite],
                ctl_score[finite],
                ctl_risk[finite],
                horizon,
                survival_floor=survival_floor,
            )
            for metric in METRIC_COLUMNS:
                rows.append(
                    {
                        "model": model,
                        "reference_assay": "original",
                        "control_assay": control_name,
                        "metric": f"difference_{metric}",
                        "point_estimate": left[metric] - right[metric],
                        "comparison_n": int(np.sum(finite)),
                    }
                )
    return pd.DataFrame(rows)


def _plot_outputs(
    metrics: pd.DataFrame,
    actions: pd.DataFrame,
    comparisons: pd.DataFrame,
    dca: pd.DataFrame,
    output_root: Path,
) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
    for axis, cohort in zip(axes.ravel(), PRIMARY_COHORTS, strict=True):
        subset = metrics.loc[metrics["cohort"].eq(cohort)]
        axis.bar(subset["model"], subset["ipcw_brier"], color="#4C78A8")
        axis.set_title(cohort)
        axis.set_ylabel("24-month IPCW Brier")
        axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path = output_root / "cohort_brier.svg"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    primary = actions.loc[actions["gate_profile"].eq("90")]
    pivot = primary.pivot(index="cohort", columns="action", values="rate").fillna(0.0)
    pivot = pivot.reindex(index=PRIMARY_COHORTS, columns=["AUGMENT", "FALLBACK", "ABSTAIN"])
    fig, axis = plt.subplots(figsize=(9, 5))
    bottom = np.zeros(len(pivot))
    colors = {"AUGMENT": "#59A14F", "FALLBACK": "#F28E2B", "ABSTAIN": "#E15759"}
    for action in pivot.columns:
        values = pivot[action].to_numpy(dtype=float)
        axis.bar(pivot.index, values, bottom=bottom, label=action, color=colors[action])
        bottom += values
    axis.set_ylim(0, 1)
    axis.set_ylabel("Proportion")
    axis.legend(frameon=False, ncol=3)
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    path = output_root / "action_distribution.svg"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    brier = comparisons.loc[comparisons["metric"].eq("difference_ipcw_brier")].copy()
    brier["label"] = brier["cohort"].astype(str) + " " + brier["comparison"].astype(str)
    fig, axis = plt.subplots(figsize=(9, max(4, len(brier) * 0.35)))
    y = np.arange(len(brier))
    axis.errorbar(
        brier["point_estimate"],
        y,
        xerr=np.vstack(
            [
                brier["point_estimate"] - brier["ci_lower_95"],
                brier["ci_upper_95"] - brier["point_estimate"],
            ]
        ),
        fmt="o",
        color="#4C78A8",
        ecolor="#9ECAE9",
        capsize=3,
    )
    axis.axvline(0.0, color="black", linewidth=1)
    axis.set_yticks(y, brier["label"])
    axis.set_xlabel("Brier difference (left - right; lower favors left)")
    axis.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = output_root / "paired_brier_differences.svg"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for axis, cohort in zip(axes.ravel(), PRIMARY_COHORTS, strict=True):
        subset = dca.loc[dca["cohort"].eq(cohort)]
        for model, group in subset.groupby("model", sort=True):
            axis.plot(group["threshold"], group["net_benefit_model"], label=model)
        if not subset.empty:
            base = subset.drop_duplicates("threshold")
            axis.plot(
                base["threshold"],
                base["net_benefit_all"],
                "--",
                color="grey",
                label="Treat all",
            )
            axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_title(cohort)
        axis.set_xlabel("Risk threshold")
        axis.set_ylabel("IPCW net benefit")
        axis.grid(alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    path = output_root / "decision_curve.svg"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)
    return paths


def _assert_consumed_or_consume(project_root: Path, token: str) -> bool:
    freeze_path = Path(project_root) / "configs/analysis_freeze.yaml"
    freeze = FreezeRecord.load(freeze_path)
    if freeze.payload.get("phase6_outcomes_seen") is False:
        consume_phase6_authorization(project_root, approval_token=token)
        return False
    unseal = freeze.payload.get("test_unseal") or {}
    expected = str(unseal.get("approval_token_sha256", "")) if isinstance(unseal, dict) else ""
    observed = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if not expected or observed != expected or unseal.get("consumed") is not True:
        raise SealedTestError("post-unseal reproduction authorization is invalid")
    freeze._assert_hashes(Path(project_root).resolve(), "config_sha256")
    freeze._assert_hashes(Path(project_root).resolve(), "sealed_manifest_sha256")
    verify_frozen_cohort_manifest(project_root)
    return True


def run_locked_evaluation(project_root: Path, token_file: Path) -> dict[str, object]:
    """Consume authorization, load outcomes, and write aggregate Phase 6 results."""
    root = Path(project_root).resolve()
    _load_preflight_receipt(root)
    token_path = token_file if token_file.is_absolute() else root / token_file
    token = token_path.read_text(encoding="utf-8").strip()
    assert_token_absent_from_tracked_files(root, token)
    reproduction = _assert_consumed_or_consume(root, token)

    phase6, model_config = load_phase6_configuration(root)
    horizon = float(phase6["horizon_days"])
    survival_floor = float(model_config.get("ipcw_survival_floor", 0.05))
    replicates = int(phase6["bootstrap_replicates"])
    primary_profile = str(phase6["primary_gate_profile"]).rsplit("_", 1)[-1]
    profiles = tuple(_profile_label(value) for value in _profile_coverages(phase6))
    random_states = {
        str(key): int(value)
        for key, value in dict(phase6["bootstrap_random_state_by_cohort"]).items()
    }
    thresholds = [float(value) for value in phase6["decision_curve_thresholds"]]

    metric_rows: list[dict[str, object]] = []
    bootstrap_models: list[pd.DataFrame] = []
    bootstrap_comparisons: list[pd.DataFrame] = []
    point_comparison_frames: list[pd.DataFrame] = []
    action_frames: list[pd.DataFrame] = []
    dca_frames: list[pd.DataFrame] = []
    bundles: dict[str, tuple[object, CohortFeatures, OutcomeData, pd.DataFrame]] = {}

    for cohort in PRIMARY_COHORTS:
        development, features = _feature_bundle(root, cohort)
        outcomes = load_phase6_outcomes(root, cohort, features.ids)
        predictions = _read_prediction(
            root, cohort, features.ids, profile=primary_profile
        )
        bundles[cohort] = (development, features, outcomes, predictions)
        metric_rows.extend(
            model_metrics(
                development,
                outcomes,
                predictions,
                horizon=horizon,
                survival_floor=survival_floor,
            )
        )
        model_boot, comparison_boot = paired_bootstrap_metrics(
            development,
            outcomes,
            predictions,
            replicates=replicates,
            random_state=random_states[cohort],
            horizon=horizon,
            survival_floor=survival_floor,
        )
        model_boot.insert(0, "cohort", cohort)
        comparison_boot.insert(0, "cohort", cohort)
        bootstrap_models.append(model_boot)
        bootstrap_comparisons.append(comparison_boot)
        point_comparison = paired_comparison_metrics(
            development, outcomes, predictions, horizon=horizon, survival_floor=survival_floor
        )
        point_comparison.insert(0, "cohort", cohort)
        point_comparison_frames.append(point_comparison)
        for profile in profiles:
            profile_predictions = _read_prediction(
                root, cohort, features.ids, profile=profile
            )
            summary = action_summary(cohort, profile_predictions)
            summary.insert(1, "gate_profile", profile)
            action_frames.append(summary)
        dca_frames.append(
            decision_curve_rows(
                development,
                outcomes,
                predictions,
                horizon=horizon,
                thresholds=thresholds,
                survival_floor=survival_floor,
            )
        )

    metrics = pd.DataFrame(metric_rows)
    model_bootstrap = pd.concat(bootstrap_models, ignore_index=True)
    comparison_bootstrap = pd.concat(bootstrap_comparisons, ignore_index=True)
    model_intervals = percentile_intervals(
        model_bootstrap,
        group_columns=["cohort", "model"],
        value_columns=list(METRIC_COLUMNS),
    )
    comparison_intervals = percentile_intervals(
        comparison_bootstrap,
        group_columns=["cohort", "comparison"],
        value_columns=[f"difference_{metric}" for metric in METRIC_COLUMNS],
    )
    point_wide = pd.concat(point_comparison_frames, ignore_index=True)
    point_long = point_wide.melt(
        id_vars=["cohort", "comparison", "n"],
        value_vars=[f"difference_{metric}" for metric in METRIC_COLUMNS],
        var_name="metric",
        value_name="point_estimate",
    )
    comparisons = point_long.merge(
        comparison_intervals,
        on=["cohort", "comparison", "metric"],
        how="left",
        validate="one_to_one",
    )
    actions = pd.concat(action_frames, ignore_index=True)
    dca = pd.concat(dca_frames, ignore_index=True)

    rad_development, rad_features, rad_outcomes, rad_reference = bundles["RADCURE"]
    controls = {
        assay: _read_prediction(
            root,
            "RADCURE",
            rad_features.ids,
            assay=assay,
            profile=primary_profile,
        )
        for assay in RADCURE_ASSAYS
        if assay != "original"
    }
    negative_metric_rows: list[dict[str, object]] = []
    for assay, predictions in {"original": rad_reference, **controls}.items():
        rows = model_metrics(
            rad_development,
            rad_outcomes,
            predictions,
            horizon=horizon,
            survival_floor=survival_floor,
        )
        for row in rows:
            negative_metric_rows.append({"row_type": "assay_metric", "assay": assay, **row})
    negative_bootstrap = paired_prediction_set_bootstrap(
        rad_development,
        rad_outcomes,
        rad_reference,
        controls,
        models=("B4", "B5", "B6", "B7"),
        replicates=replicates,
        random_state=random_states["RADCURE_NEGATIVE_CONTROLS"],
        horizon=horizon,
        survival_floor=survival_floor,
    )
    negative_intervals = percentile_intervals(
        negative_bootstrap,
        group_columns=["model", "reference_assay", "control_assay"],
        value_columns=[f"difference_{metric}" for metric in METRIC_COLUMNS],
    )
    negative_points = _paired_prediction_point_differences(
        rad_development,
        rad_outcomes,
        rad_reference,
        controls,
        horizon=horizon,
        survival_floor=survival_floor,
    )
    negative_differences = negative_points.merge(
        negative_intervals,
        on=["model", "reference_assay", "control_assay", "metric"],
        how="left",
        validate="one_to_one",
    )
    negative_differences.insert(0, "row_type", "paired_difference")
    negative_metrics = pd.concat(
        [pd.DataFrame(negative_metric_rows), negative_differences],
        ignore_index=True,
        sort=False,
    )

    output_root = root / "results/metrics/phase6"
    outputs = {
        "cohort_metrics.csv": metrics,
        "bootstrap_confidence_intervals.csv": model_intervals,
        "paired_comparisons.csv": comparisons,
        "action_summary.csv": actions,
        "radcure_negative_controls.csv": negative_metrics,
        "decision_curve.csv": dca,
    }
    output_paths: list[Path] = []
    for name, frame in outputs.items():
        path = output_root / name
        _atomic_csv(path, frame)
        output_paths.append(path)
    figure_paths = _plot_outputs(
        metrics,
        actions,
        comparisons,
        dca,
        root / "results/figures/phase6",
    )
    _assert_aggregate_privacy(output_paths + figure_paths)
    assert_token_absent_from_tracked_files(root, token)

    receipt_path = root / "results/manifests/phase6_locked_evaluation_receipt.json"
    existing = json.loads(receipt_path.read_text(encoding="utf-8"))
    final_receipt = {
        **existing,
        "evaluation_completed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "deterministic_reproduction_run": reproduction,
        "bootstrap_replicates": replicates,
        "primary_gate_profile": str(phase6["primary_gate_profile"]),
        "cohort_metric_rows": len(metrics),
        "paired_comparison_rows": len(comparisons),
        "negative_control_rows": len(negative_metrics),
        "aggregate_output_sha256": {
            str(path.relative_to(root)).replace("\\", "/"): sha256_file(path)
            for path in sorted(output_paths + figure_paths)
        },
        "patient_level_identifiers_in_tracked_outputs": False,
        "outcome_guided_retuning_performed": False,
    }
    _atomic_json(receipt_path, final_receipt)
    assert_token_absent_from_tracked_files(root, token)
    return {
        "status": "COMPLETE",
        "reproduction": reproduction,
        "cohorts": list(PRIMARY_COHORTS),
        "bootstrap_replicates": replicates,
        "aggregate_outputs": len(output_paths) + len(figure_paths),
        "receipt": str(receipt_path),
    }
