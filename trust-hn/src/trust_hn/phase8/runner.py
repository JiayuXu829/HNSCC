"""Phase 8 pseudo-private overlap simulation for inner_hancock."""

from __future__ import annotations

import argparse
import json
import math
import os
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
    load_hancock_features,
    load_phase6_development_data,
)
from trust_hn.evaluation.phase3 import _infer_columns, _permuted
from trust_hn.evaluation.phase6 import (
    OutcomeData,
    Phase6StressSystem,
    gated_external_predictions,
    load_phase6_configuration,
    load_phase6_outcomes,
)
from trust_hn.metrics.survival import (
    evaluate_survival_predictions,
    ipcw_binary_outcomes,
    structured_survival,
)
from trust_hn.models.survival_baselines import TabularPreprocessor, fit_predict_survival_model
from trust_hn.phase7.models import Phase7FeaturePreprocessor, fit_predict_phase7_model
from trust_hn.phase7.runner import load_phase7_config, verify_phase6_frozen_files
from trust_hn.utils.hashing import sha256_file

matplotlib.rcParams["svg.hashsalt"] = "trust-hn-phase8-pseudo-private"
METHODS = ("B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "M0", "N0", "C1", "C2", "C3", "C4")
BOOT_METRICS = ("ipcw_brier", "harrell_c", "uno_c", "auc_horizon")


def _atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temp, index=False)
    os.replace(temp, path)


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temp, path)


def load_config(root: Path) -> dict[str, object]:
    path = Path(root) / "configs/phase8_pseudo_private_overlap_simulation.json"
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    if config.get("cohort_alias") != "inner_hancock":
        raise ValueError("cohort alias must remain inner_hancock")
    if config.get("independent_private_validation") is not False:
        raise ValueError("independent validation label is prohibited")
    if config.get("known_cohort_overlap") is not True:
        raise ValueError("overlap disclosure is required")
    if tuple(config.get("methods", [])) != METHODS:
        raise ValueError("method list changed")
    return config


def _norm(value: object) -> str:
    return str(value).strip().zfill(3)


def load_inner_hancock_features(root: Path) -> tuple[CohortFeatures, pd.DataFrame]:
    blocks, roles = [], []
    for role in ("train", "calibration", "sealed_test"):
        block = load_hancock_features(root, role=role)
        blocks.append(block)
        roles.extend([role] * len(block.ids))
    all_ids = np.concatenate([block.ids.astype(str) for block in blocks])
    clinical = pd.concat([block.clinical for block in blocks], ignore_index=True)
    modality = pd.concat([block.modality for block in blocks], ignore_index=True)
    lookup = {_norm(value): index for index, value in enumerate(all_ids)}
    target_path = (
        Path(root) / "data/sample/hancock_135/HANCOCK_MultimodalDataset/features/targets.csv"
    )
    target = pd.read_csv(target_path, dtype={"patient_id": "string"})
    wanted = target["patient_id"].map(_norm).tolist()
    if len(wanted) != 135 or len(set(wanted)) != 135:
        raise ValueError("expected 135 unique IDs")
    if set(wanted) - set(lookup):
        raise ValueError("some target IDs are absent from frozen features")
    indices = np.asarray([lookup[value] for value in wanted], dtype=int)
    provenance = pd.DataFrame(
        {"native_id": wanted, "source_partition": np.asarray(roles, dtype=object)[indices]}
    )
    features = CohortFeatures(
        "inner_hancock",
        "pseudo_private_overlap",
        np.asarray(wanted),
        clinical.iloc[indices].reset_index(drop=True),
        modality.iloc[indices].reset_index(drop=True),
    )
    return features, provenance


def _aggregate_phase6(frames: Sequence[pd.DataFrame], profile: str) -> pd.DataFrame:
    if not frames or len({len(frame) for frame in frames}) != 1:
        raise ValueError("seed frames are absent or misaligned")
    result = pd.DataFrame(index=np.arange(len(frames[0])))
    for model in ("b2", "b3", "b4", "b5", "b6", "m0"):
        for suffix in ("score", "risk"):
            column = f"{model}_{suffix}"
            if all(column in frame for frame in frames):
                result[column] = np.mean(
                    np.vstack([frame[column].to_numpy(float) for frame in frames]), axis=0
                )
    actions = np.vstack([frame[f"b7_action_{profile}"].astype(str).to_numpy() for frame in frames])
    majority = len(frames) // 2 + 1
    consensus = np.full(actions.shape[1], "AUGMENT", dtype="U8")
    consensus[np.sum(actions == "FALLBACK", axis=0) >= majority] = "FALLBACK"
    consensus[np.sum(actions == "ABSTAIN", axis=0) >= majority] = "ABSTAIN"
    risks = np.vstack([frame[f"b7_risk_{profile}"].to_numpy(float) for frame in frames])
    count = np.sum(np.isfinite(risks), axis=0)
    b7 = np.divide(
        np.nansum(risks, axis=0), count, out=np.full(risks.shape[1], np.nan), where=count > 0
    )
    b7[consensus == "FALLBACK"] = result.loc[consensus == "FALLBACK", "b2_risk"]
    b7[consensus == "ABSTAIN"] = np.nan
    result["b7_action"], result["b7_score"], result["b7_risk"] = consensus, b7, b7
    result["non_abstaining_seed_count"] = count
    return result


def _basic_predictions(
    root: Path, development, features: CohortFeatures, seeds: Sequence[int]
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    _, cfg = load_phase6_configuration(root)
    horizon = float(cfg["horizon_days"])
    outcome = structured_survival(development.train_event, development.train_time)
    b0 = fit_predict_survival_model(
        "B0",
        np.zeros((len(outcome), 0)),
        outcome,
        np.zeros((len(features.ids), 0)),
        horizon,
        seeds[0],
        cfg,
    )
    numeric, categorical = _infer_columns(development.clinical_train, development.study)
    clinical = TabularPreprocessor(numeric, categorical).fit(development.clinical_train)
    b1 = fit_predict_survival_model(
        "B1",
        clinical.transform(development.clinical_train),
        outcome,
        clinical.transform(features.clinical),
        horizon,
        seeds[0],
        cfg,
    )
    scores, risks = [], []
    for seed in seeds:
        train = _permuted(development.modality_train, seed * 2003 + 31)
        evaluation = _permuted(features.modality, seed * 2011 + 37)
        numeric, categorical = _infer_columns(train, development.study)
        prep = TabularPreprocessor(numeric, categorical).fit(train)
        pred = fit_predict_survival_model(
            "N0", prep.transform(train), outcome, prep.transform(evaluation), horizon, seed, cfg
        )
        scores.append(pred.risk_score)
        risks.append(pred.risk_horizon)
    return {
        "B0": (b0.risk_score, b0.risk_horizon),
        "B1": (b1.risk_score, b1.risk_horizon),
        "N0": (np.mean(scores, axis=0), np.mean(risks, axis=0)),
    }


def generate_predictions(
    root: Path, *, seeds: Sequence[int] | None = None, ensemble_size: int | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    root, config = Path(root), load_config(root)
    seeds = [int(value) for value in (seeds or config["seeds"])]
    ensemble = int(
        ensemble_size
        if ensemble_size is not None
        else config["model_uncertainty_bootstrap_ensemble_size"]
    )
    features, provenance = load_inner_hancock_features(root)
    development = load_phase6_development_data(root, "HANCOCK")
    _, model_config = load_phase6_configuration(root)
    frames, saved = [], []
    for seed in seeds:
        system = Phase6StressSystem(development, model_config, seed, ensemble).fit()
        frame = gated_external_predictions(
            system, development, features, seed=seed, coverages=tuple(config["gate_coverages"])
        )
        frames.append(frame)
        keep = [
            column
            for column in frame
            if column.endswith(("_score", "_risk")) or column.startswith("b7_action_")
        ]
        local = frame[keep].copy()
        local.insert(0, "native_id", features.ids)
        local.insert(1, "cohort", "inner_hancock")
        local.insert(2, "seed", seed)
        saved.append(local)
    aggregate = _aggregate_phase6(frames, str(config["primary_gate_profile"]))
    for model, (score, risk) in _basic_predictions(root, development, features, seeds).items():
        aggregate[f"{model.lower()}_score"], aggregate[f"{model.lower()}_risk"] = score, risk
    if "m0_score" not in aggregate:
        aggregate["m0_score"], aggregate["m0_risk"] = aggregate["b0_score"], aggregate["b0_risk"]
    phase7 = load_phase7_config(root)
    cfg = dict(phase7["hyperparameters"])
    cfg["cv_folds"] = int(phase7["cv_folds"])
    outcome = structured_survival(development.train_event, development.train_time)
    comparator = {model: [] for model in ("C1", "C2", "C3", "C4")}
    for seed in seeds:
        prep = Phase7FeaturePreprocessor(
            development.study, top_k=int(cfg.get("numeric_modality_top_k", 500))
        ).fit(development.clinical_train, development.modality_train)
        train = prep.transform(development.clinical_train, development.modality_train)
        evaluation = prep.transform(features.clinical, features.modality)
        for model in comparator:
            pred = fit_predict_phase7_model(
                model, train, outcome, evaluation, float(config["horizon_days"]), seed, cfg
            )
            comparator[model].append((pred.risk_score, pred.risk_horizon))
    for model, values in comparator.items():
        aggregate[f"{model.lower()}_score"] = np.mean([value[0] for value in values], axis=0)
        aggregate[f"{model.lower()}_risk"] = np.mean([value[1] for value in values], axis=0)
    aggregate.insert(0, "native_id", features.ids)
    aggregate.insert(1, "cohort", "inner_hancock")
    aggregate = aggregate.merge(provenance, on="native_id", validate="one_to_one")
    output = root / "results/predictions/phase8_pseudo_private"
    _atomic_csv(
        output / "inner_hancock_predictions_by_seed.csv", pd.concat(saved, ignore_index=True)
    )
    _atomic_csv(output / "inner_hancock_predictions_aggregate.csv", aggregate)
    return aggregate, provenance


def _outcomes(root: Path, ids: Sequence[str]) -> OutcomeData:
    source = load_phase6_outcomes(root, "HANCOCK", ids)
    return OutcomeData("inner_hancock", source.ids, source.event, source.time)


def evaluate_predictions(
    root: Path, predictions: pd.DataFrame, *, bootstrap_replicates: int | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    root, config = Path(root), load_config(root)
    development = load_phase6_development_data(root, "HANCOCK")
    outcomes = _outcomes(root, predictions["native_id"].astype(str).tolist())
    horizon, floor = float(config["horizon_days"]), 0.05
    rows, arrays = [], {}
    for model in METHODS:
        score = predictions[f"{model.lower()}_score"].to_numpy(float)
        risk = predictions[f"{model.lower()}_risk"].to_numpy(float)
        arrays[model] = (score, risk)
        finite = np.isfinite(score) & np.isfinite(risk)
        values = evaluate_survival_predictions(
            development.train_event,
            development.train_time,
            outcomes.event[finite],
            outcomes.time[finite],
            score[finite],
            risk[finite],
            horizon,
            survival_floor=floor,
        )
        rows.append(
            {
                "analysis_label": config["analysis_label"],
                "cohort": "inner_hancock",
                "model": model,
                "parent_n": len(outcomes.ids),
                "coverage": float(np.mean(finite)),
                **values,
            }
        )
    metrics = pd.DataFrame(rows)
    reps = int(
        bootstrap_replicates
        if bootstrap_replicates is not None
        else config["metric_bootstrap_replicates"]
    )
    rng, boot, n = (
        np.random.default_rng(int(config["bootstrap_random_state"])),
        [],
        len(outcomes.ids),
    )
    for replicate in range(reps):
        sample = rng.integers(0, n, size=n)
        for model in METHODS:
            score, risk = arrays[model][0][sample], arrays[model][1][sample]
            event, time = outcomes.event[sample], outcomes.time[sample]
            finite = np.isfinite(score) & np.isfinite(risk)
            if finite.sum() < 5:
                continue
            values = evaluate_survival_predictions(
                development.train_event,
                development.train_time,
                event[finite],
                time[finite],
                score[finite],
                risk[finite],
                horizon,
                survival_floor=floor,
            )
            boot.append(
                {
                    "replicate": replicate,
                    "model": model,
                    **{key: values[key] for key in BOOT_METRICS},
                }
            )
    bootstrap = pd.DataFrame(boot)
    rows = []
    for model in METHODS:
        point = metrics.loc[metrics["model"].eq(model)].iloc[0]
        local = bootstrap.loc[bootstrap["model"].eq(model)]
        for metric in BOOT_METRICS:
            values = pd.to_numeric(local[metric], errors="coerce").dropna().to_numpy(float)
            lower, median, upper = (
                np.quantile(values, [0.025, 0.5, 0.975])
                if len(values)
                else (math.nan, math.nan, math.nan)
            )
            rows.append(
                {
                    "model": model,
                    "metric": metric,
                    "point_estimate": float(point[metric]),
                    "bootstrap_median": float(median),
                    "ci_lower_95": float(lower),
                    "ci_upper_95": float(upper),
                    "valid_replicates": len(values),
                }
            )
    intervals = pd.DataFrame(rows)
    rows = []
    pairs = (
        ("B7", "B6"),
        ("B7", "B2"),
        ("B6", "B5"),
        ("C1", "B6"),
        ("C2", "B6"),
        ("C3", "B6"),
        ("C4", "B6"),
    )
    paired_rng = np.random.default_rng(int(config["bootstrap_random_state"]) + 991)
    paired_samples = [paired_rng.integers(0, n, size=n) for _ in range(reps)]
    for left, right in pairs:
        left_score, left_risk = arrays[left]
        right_score, right_risk = arrays[right]
        common = (
            np.isfinite(left_score)
            & np.isfinite(left_risk)
            & np.isfinite(right_score)
            & np.isfinite(right_risk)
        )
        eligible = np.flatnonzero(common)
        left_point = evaluate_survival_predictions(
            development.train_event,
            development.train_time,
            outcomes.event[eligible],
            outcomes.time[eligible],
            left_score[eligible],
            left_risk[eligible],
            horizon,
            survival_floor=floor,
        )
        right_point = evaluate_survival_predictions(
            development.train_event,
            development.train_time,
            outcomes.event[eligible],
            outcomes.time[eligible],
            right_score[eligible],
            right_risk[eligible],
            horizon,
            survival_floor=floor,
        )
        differences = {metric: [] for metric in BOOT_METRICS}
        for sample in paired_samples:
            local = sample[common[sample]]
            if len(local) < 5:
                continue
            left_values = evaluate_survival_predictions(
                development.train_event,
                development.train_time,
                outcomes.event[local],
                outcomes.time[local],
                left_score[local],
                left_risk[local],
                horizon,
                survival_floor=floor,
            )
            right_values = evaluate_survival_predictions(
                development.train_event,
                development.train_time,
                outcomes.event[local],
                outcomes.time[local],
                right_score[local],
                right_risk[local],
                horizon,
                survival_floor=floor,
            )
            for metric in BOOT_METRICS:
                difference = left_values[metric] - right_values[metric]
                if np.isfinite(difference):
                    differences[metric].append(difference)
        for metric in BOOT_METRICS:
            values = np.asarray(differences[metric], dtype=float)
            lower, upper = (
                np.quantile(values, [0.025, 0.975]) if len(values) else (math.nan, math.nan)
            )
            rows.append(
                {
                    "comparison": f"{left}_vs_{right}",
                    "metric": metric,
                    "common_subset_n": len(eligible),
                    "point_difference": float(left_point[metric] - right_point[metric]),
                    "ci_lower_95": float(lower),
                    "ci_upper_95": float(upper),
                    "valid_replicates": len(values),
                }
            )
    comparisons = pd.DataFrame(rows)
    counts = predictions["b7_action"].value_counts()
    coverage = float(np.mean(predictions["b7_action"] != "ABSTAIN"))
    actions = pd.DataFrame(
        [
            {
                "cohort": "inner_hancock",
                "action": action,
                "count": int(counts.get(action, 0)),
                "rate": float(counts.get(action, 0) / len(predictions)),
                "non_abstention_coverage": coverage,
            }
            for action in ("AUGMENT", "FALLBACK", "ABSTAIN")
        ]
    )
    output = root / "results/metrics/phase8_pseudo_private"
    _atomic_csv(output / "model_metrics.csv", metrics)
    _atomic_csv(output / "bootstrap_confidence_intervals.csv", intervals)
    _atomic_csv(output / "paired_comparisons.csv", comparisons)
    _atomic_csv(output / "action_summary.csv", actions)
    return metrics, intervals, comparisons, actions


def _plot_results(
    root: Path, predictions: pd.DataFrame, metrics: pd.DataFrame, actions: pd.DataFrame
) -> None:
    output = Path(root) / "results/figures/phase8_pseudo_private"
    output.mkdir(parents=True, exist_ok=True)
    local = metrics.set_index("model").reindex(METHODS)
    colors = ["#C00000" if model in {"B6", "B7"} else "#4472C4" for model in METHODS]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].bar(METHODS, local["ipcw_brier"], color=colors)
    axes[0].set_ylabel("24-month IPCW Brier")
    axes[1].bar(METHODS, local["harrell_c"], color=colors)
    axes[1].set_ylabel("Harrell C-index")
    for axis in axes:
        axis.tick_params(axis="x", rotation=45)
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle("inner_hancock pseudo-private overlap simulation")
    fig.tight_layout()
    fig.savefig(output / "model_comparison.svg", bbox_inches="tight")
    plt.close(fig)
    outcomes = _outcomes(Path(root), predictions["native_id"].astype(str).tolist())
    development = load_phase6_development_data(Path(root), "HANCOCK")
    observed, weight = ipcw_binary_outcomes(
        development.train_event, development.train_time, outcomes.event, outcomes.time, 730.5
    )
    fig, axis = plt.subplots(figsize=(7, 6))
    for model, color in {
        "B2": "#70AD47",
        "B6": "#4472C4",
        "B7": "#C00000",
        "C2": "#7030A0",
    }.items():
        risk = predictions[f"{model.lower()}_risk"].to_numpy(float)
        finite = np.isfinite(risk) & (weight > 0)
        table = pd.DataFrame(
            {"risk": risk[finite], "outcome": observed[finite], "weight": weight[finite]}
        )
        table["bin"] = pd.qcut(
            table["risk"], q=min(5, max(2, table["risk"].nunique())), duplicates="drop"
        )
        points = [
            {
                "predicted": np.average(group["risk"], weights=group["weight"]),
                "observed": np.average(group["outcome"], weights=group["weight"]),
            }
            for _, group in table.groupby("bin", observed=True)
        ]
        points = pd.DataFrame(points)
        axis.plot(points["predicted"], points["observed"], "o-", label=model, color=color)
    axis.plot([0, 1], [0, 1], "--", color="black")
    axis.set_xlabel("Mean predicted 24-month risk")
    axis.set_ylabel("IPCW observed mortality")
    axis.set_title("Calibration overview")
    axis.legend()
    axis.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "calibration.svg", bbox_inches="tight")
    plt.close(fig)
    fig, axis = plt.subplots(figsize=(7, 5))
    axis.bar(actions["action"], actions["rate"], color=["#4472C4", "#FFC000", "#C00000"])
    axis.set_ylim(0, 1)
    axis.set_ylabel("Proportion")
    axis.set_title("B7 gate actions")
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "action_distribution.svg", bbox_inches="tight")
    plt.close(fig)
    selected = predictions[["b2_risk", "b4_risk", "b6_risk", "c2_risk"]]
    fig, axis = plt.subplots(figsize=(9, 5))
    axis.boxplot(
        [selected[column].dropna() for column in selected],
        tick_labels=["Clinical B2", "Modality B4", "Fusion B6", "XGBoost C2"],
        showfliers=False,
    )
    axis.set_ylabel("Predicted 24-month risk")
    axis.set_title("Clinical, modality and fusion risk distributions")
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "modality_risk_distributions.svg", bbox_inches="tight")
    plt.close(fig)


def _markdown_table(metrics: pd.DataFrame) -> str:
    columns = ("model", "coverage", "ipcw_brier", "harrell_c", "uno_c", "auc_horizon")
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in metrics[list(columns)].itertuples(index=False, name=None):
        lines.append(
            "| " + " | ".join([str(row[0])] + [f"{float(value):.4f}" for value in row[1:]]) + " |"
        )
    return "\n".join(lines)


def _write_reports(
    root: Path, metrics: pd.DataFrame, actions: pd.DataFrame, seeds: Sequence[int], reps: int
) -> None:
    root = Path(root)
    best = metrics.sort_values("ipcw_brier").iloc[0]
    b7 = metrics.loc[metrics["model"].eq("B7")].iloc[0]
    values = {
        "seeds": list(seeds),
        "bootstrap_replicates": reps,
        "table": _markdown_table(metrics),
        "best_model": best["model"],
        "best_brier": f"{best['ipcw_brier']:.4f}",
        "best_harrell": f"{best['harrell_c']:.4f}",
        "best_auc": f"{best['auc_horizon']:.4f}",
        "b7_coverage": f"{b7['coverage']:.1%}",
        "action_text": ", ".join(
            f"{row.action}={int(row['count'])} ({row.rate:.1%})" for _, row in actions.iterrows()
        ),
    }
    for language in ("zh-CN", "en"):
        template = (
            root / "docs/work_stage_reports/templates" / f"phase8_pseudo_private_{language}.md"
        ).read_text(encoding="utf-8-sig")
        output = (
            root
            / "docs/work_stage_reports"
            / language
            / "2026-08-11_phase8_pseudo_private_overlap_simulation_report.md"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(template.format(**values), encoding="utf-8")


def finalize_receipt(
    root: Path,
    config: Mapping[str, object],
    provenance: pd.DataFrame,
    seeds: Sequence[int],
    reps: int,
    ensemble: int,
) -> dict[str, object]:
    root = Path(root)
    verification = verify_phase6_frozen_files(root)
    if not verification["all_match"]:
        raise RuntimeError("Phase 6 registered files changed")
    paths = []
    for directory in (
        root / "results/metrics/phase8_pseudo_private",
        root / "results/figures/phase8_pseudo_private",
    ):
        paths.extend(path for path in sorted(directory.rglob("*")) if path.is_file())
    paths.extend(
        [
            root
            / "docs/work_stage_reports/zh-CN"
            / "2026-08-11_phase8_pseudo_private_overlap_simulation_report.md",
            root
            / "docs/work_stage_reports/en"
            / "2026-08-11_phase8_pseudo_private_overlap_simulation_report.md",
        ]
    )
    payload = {
        "schema_version": "1.0",
        "phase": "Phase 8 pseudo-private overlap simulation",
        "analysis_label": config["analysis_label"],
        "cohort_alias": "inner_hancock",
        "completed_at": datetime.now(UTC).isoformat(),
        "status": "COMPLETE",
        "patient_count": 135,
        "source_partition_composition": provenance["source_partition"].value_counts().to_dict(),
        "methods": list(METHODS),
        "seeds": list(seeds),
        "model_uncertainty_bootstrap_ensemble_size": ensemble,
        "metric_bootstrap_replicates": reps,
        "independent_private_validation": False,
        "known_cohort_overlap": True,
        "manuscript_claim_allowed": False,
        "external_validation_claim_allowed": False,
        "prospective_validation_claim_allowed": False,
        "clinical_utility_claim_allowed": False,
        "phase6_frozen_file_verification": verification,
        "phase6_outputs_overwritten": False,
        "phase7_outputs_overwritten": False,
        "patient_level_outputs_git_ignored": True,
        "config_sha256": sha256_file(
            root / "configs/phase8_pseudo_private_overlap_simulation.json"
        ),
        "tracked_output_sha256": {
            path.relative_to(root).as_posix(): sha256_file(path) for path in paths if path.exists()
        },
    }
    _atomic_json(root / "results/manifests/phase8_pseudo_private_simulation_receipt.json", payload)
    return payload


def run_all(
    root: Path,
    *,
    seeds: Sequence[int] | None = None,
    ensemble_size: int | None = None,
    bootstrap_replicates: int | None = None,
) -> dict[str, object]:
    root, config = Path(root), load_config(root)
    seeds = [int(value) for value in (seeds or config["seeds"])]
    ensemble = int(
        ensemble_size
        if ensemble_size is not None
        else config["model_uncertainty_bootstrap_ensemble_size"]
    )
    reps = int(
        bootstrap_replicates
        if bootstrap_replicates is not None
        else config["metric_bootstrap_replicates"]
    )
    predictions, provenance = generate_predictions(root, seeds=seeds, ensemble_size=ensemble)
    metrics, intervals, comparisons, actions = evaluate_predictions(
        root, predictions, bootstrap_replicates=reps
    )
    _plot_results(root, predictions, metrics, actions)
    _write_reports(root, metrics, actions, seeds, reps)
    receipt = finalize_receipt(root, config, provenance, seeds, reps, ensemble)
    return {
        "metrics": metrics,
        "intervals": intervals,
        "comparisons": comparisons,
        "actions": actions,
        "receipt": receipt,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    result = (
        run_all(args.project_root, seeds=[17], ensemble_size=2, bootstrap_replicates=20)
        if args.smoke
        else run_all(args.project_root)
    )
    print(result["metrics"].to_string(index=False))
    print(json.dumps(result["receipt"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
