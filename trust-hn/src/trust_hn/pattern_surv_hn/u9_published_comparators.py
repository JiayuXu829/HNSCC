"""Post-hoc published-method benchmark for the PATTERN-Surv-HN estimand.

All methods use the exact U2/V1R outer-fold assignments, fold-bound preprocessing,
the same 610-patient development population, and the same 24-month survival metrics.
Patient-level predictions are written only under the git-ignored predictions tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torchtuples as tt
import yaml
from pycox.models import CoxPH as PycoxCoxPH
from pycox.models import DeepHitSingle
from sksurv.ensemble import GradientBoostingSurvivalAnalysis, RandomSurvivalForest
from sksurv.linear_model import CoxnetSurvivalAnalysis, CoxPHSurvivalAnalysis
from torch import Tensor, nn
from xgboost import XGBRegressor

from trust_hn.models.survival_baselines import _survival_risk_at_horizon
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
    _development_arrays,
    evaluate_predictions,
    structured_survival,
)
from trust_hn.pattern_surv_hn.v1_deep_sets_smoke import STATUS_LEVELS
from trust_hn.pattern_surv_hn.v1_development_cv import breslow_risk_at_horizon

METHODS = (
    "COXPH",
    "ENCOX",
    "RSF",
    "GBSA",
    "XGBCOX",
    "DEEPSURV",
    "DEEPHIT",
    "MULTISURV",
    "V1R",
)
MODALITIES = ("blood", "icd", "tma")
MODALITY_FEATURES = {
    "blood": BLOOD_FEATURES,
    "icd": ICD_FEATURES,
    "tma": TMA_FEATURES,
}
DEFAULT_SPEC = Path(
    "research_studies/01_pattern_surv_hn/core_backbone/"
    "U9_published_comparator_benchmark/frozen_u9_published_comparator_benchmark_spec.yaml"
)
DEFAULT_V1R_OOF = Path(
    "results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv"
)
DEFAULT_OUTPUT = Path("results/metrics/pattern_surv_hn/U9_published_comparator_benchmark")
DEFAULT_PREDICTIONS = Path("results/predictions/pattern_surv_hn/U9_published_comparators")


@dataclass(frozen=True)
class FoldFeatures:
    direct: np.ndarray
    clinical: np.ndarray
    modalities: tuple[np.ndarray, ...]
    active: np.ndarray


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _load_spec(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if payload.get("analysis_label") != "post_hoc_exploratory_published_method_benchmark":
        raise ValueError("U9 must remain explicitly post-hoc exploratory")
    if tuple(payload.get("methods", {})) != METHODS:
        raise ValueError("U9 method order differs from the frozen method list")
    governance = payload.get("governance", {})
    if governance.get("prespecified_confirmatory_comparison"):
        raise ValueError("U9 cannot be labelled confirmatory")
    if governance.get("confirmation_outcomes_used") or governance.get("retune_v1r"):
        raise ValueError("U9 governance permits a prohibited action")
    return payload


def _prepare_features(
    contract: HancockContract,
    metadata: pd.DataFrame,
    train_ids: Sequence[str],
    eval_ids: Sequence[str],
) -> tuple[FoldFeatures, FoldFeatures]:
    train_ids = tuple(str(value) for value in train_ids)
    eval_ids = tuple(str(value) for value in eval_ids)
    clinical_prep = FoldBoundMixedPreprocessor(
        numeric=ANCHOR_NUMERIC_FEATURES,
        categorical=ANCHOR_CATEGORICAL_FEATURES,
        allowed_fit_ids=set(train_ids),
    )
    train_clinical = clinical_prep.fit_transform(contract.anchor, train_ids).values
    eval_clinical = clinical_prep.transform(contract.anchor, eval_ids).values
    train_modalities: list[np.ndarray] = []
    eval_modalities: list[np.ndarray] = []
    train_active: list[np.ndarray] = []
    eval_active: list[np.ndarray] = []
    train_direct_blocks: list[np.ndarray] = [train_clinical]
    eval_direct_blocks: list[np.ndarray] = [eval_clinical]

    for name in MODALITIES:
        prep = FoldBoundBlockPreprocessor(
            MODALITY_FEATURES[name],
            add_missing_indicators=True,
            allowed_fit_ids=set(train_ids),
        )
        frame = getattr(contract, name).reindex(metadata.index)
        train_values = prep.fit_transform(frame, train_ids).values
        eval_values = prep.transform(frame, eval_ids).values
        train_meta = metadata.loc[list(train_ids)]
        eval_meta = metadata.loc[list(eval_ids)]
        tr_active = train_meta[f"{name}_usable"].to_numpy(dtype=bool)
        ev_active = eval_meta[f"{name}_usable"].to_numpy(dtype=bool)
        train_values = train_values * tr_active[:, None]
        eval_values = eval_values * ev_active[:, None]
        tr_status = np.zeros((len(train_ids), len(STATUS_LEVELS)), dtype=float)
        ev_status = np.zeros((len(eval_ids), len(STATUS_LEVELS)), dtype=float)
        for row, status in enumerate(train_meta[f"{name}_status"].astype(str)):
            tr_status[row, STATUS_LEVELS.index(status)] = 1.0
        for row, status in enumerate(eval_meta[f"{name}_status"].astype(str)):
            ev_status[row, STATUS_LEVELS.index(status)] = 1.0
        tr_missing = train_meta[f"{name}_missing_fraction"].to_numpy(float)[:, None]
        ev_missing = eval_meta[f"{name}_missing_fraction"].to_numpy(float)[:, None]
        train_aux = np.column_stack([tr_active.astype(float), tr_missing, 1.0 - tr_missing])
        eval_aux = np.column_stack([ev_active.astype(float), ev_missing, 1.0 - ev_missing])
        train_direct_blocks.append(np.column_stack([train_values, tr_status, train_aux]))
        eval_direct_blocks.append(np.column_stack([eval_values, ev_status, eval_aux]))
        train_modalities.append(train_values)
        eval_modalities.append(eval_values)
        train_active.append(tr_active)
        eval_active.append(ev_active)

    return (
        FoldFeatures(
            direct=np.column_stack(train_direct_blocks),
            clinical=train_clinical,
            modalities=tuple(train_modalities),
            active=np.column_stack(train_active),
        ),
        FoldFeatures(
            direct=np.column_stack(eval_direct_blocks),
            clinical=eval_clinical,
            modalities=tuple(eval_modalities),
            active=np.column_stack(eval_active),
        ),
    )


def _encode_xgb_labels(event: np.ndarray, duration: np.ndarray) -> np.ndarray:
    event_array = np.asarray(event, bool)
    duration_array = np.asarray(duration, float)
    return np.where(event_array, duration_array, -duration_array)


def _set_torch_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)


def _train_deepsurv(
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    _set_torch_seed(seed)
    x_train = np.asarray(train.direct, dtype="float32")
    x_eval = np.asarray(evaluation.direct, dtype="float32")
    net = tt.practical.MLPVanilla(
        x_train.shape[1],
        [int(value) for value in config["hidden_dims"]],
        1,
        batch_norm=True,
        dropout=float(config["dropout"]),
        output_bias=False,
    )
    model = PycoxCoxPH(
        net,
        tt.optim.Adam(
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
        ),
    )
    target = (np.asarray(duration, dtype="float32"), np.asarray(event, dtype="int64"))
    model.fit(
        x_train,
        target,
        batch_size=128,
        epochs=int(config["epochs"]),
        verbose=False,
        shuffle=True,
    )
    model.compute_baseline_hazards(x_train, target)
    survival = model.predict_surv_df(x_eval)
    eligible = survival.index.to_numpy(float) <= float(horizon)
    risk = 1.0 - survival.iloc[np.flatnonzero(eligible)[-1]].to_numpy(float)
    score = np.asarray(model.predict(x_eval), dtype=float).reshape(-1)
    return score, np.clip(risk, 0.0, 1.0)


def _time_grid(duration: np.ndarray, intervals: int) -> np.ndarray:
    quantiles = np.linspace(0.0, 1.0, int(intervals) + 1)[1:]
    edges = np.unique(np.quantile(np.asarray(duration, float), quantiles))
    if len(edges) < 3:
        raise ValueError("too few distinct time intervals")
    return edges


def _discrete_targets(duration: np.ndarray, edges: np.ndarray) -> np.ndarray:
    return np.minimum(np.searchsorted(edges, duration, side="left"), len(edges) - 1)


def _train_deephit(
    train: FoldFeatures,
    event: np.ndarray,
    duration: np.ndarray,
    evaluation: FoldFeatures,
    config: Mapping[str, object],
    seed: int,
    horizon: float,
) -> tuple[np.ndarray, np.ndarray]:
    _set_torch_seed(seed)
    x_train = np.asarray(train.direct, dtype="float32")
    x_eval = np.asarray(evaluation.direct, dtype="float32")
    labtrans = DeepHitSingle.label_transform(int(config["intervals"]))
    target = labtrans.fit_transform(np.asarray(duration, float), np.asarray(event, int))
    net = tt.practical.MLPVanilla(
        x_train.shape[1],
        [int(value) for value in config["hidden_dims"]],
        labtrans.out_features,
        batch_norm=True,
        dropout=float(config["dropout"]),
    )
    model = DeepHitSingle(
        net,
        tt.optim.Adam(
            lr=float(config["learning_rate"]),
            weight_decay=float(config["weight_decay"]),
        ),
        alpha=float(config["ranking_weight"]),
        sigma=float(config["ranking_temperature"]),
        duration_index=labtrans.cuts,
    )
    model.fit(
        x_train,
        target,
        batch_size=128,
        epochs=int(config["epochs"]),
        verbose=False,
        shuffle=True,
    )
    survival = model.predict_surv_df(x_eval)
    eligible = survival.index.to_numpy(float) <= float(horizon)
    risk = 1.0 - survival.iloc[np.flatnonzero(eligible)[-1]].to_numpy(float)
    score = -survival.sum(axis=0).to_numpy(float)
    return score, np.clip(risk, 0.0, 1.0)


class _MultiSurv(nn.Module):
    def __init__(self, dimensions: Sequence[int], representation_dim: int, intervals: int):
        super().__init__()
        self.encoders = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Linear(int(width), representation_dim),
                    nn.ReLU(),
                    nn.Linear(representation_dim, representation_dim),
                    nn.ReLU(),
                )
                for width in dimensions
            ]
        )
        self.head = nn.Sequential(
            nn.Linear(representation_dim, representation_dim),
            nn.ReLU(),
            nn.Linear(representation_dim, intervals),
        )
        self.double()

    def forward(
        self, clinical: Tensor, modalities: Sequence[Tensor], active: Tensor
    ) -> Tensor:
        encoded = [self.encoders[0](clinical)]
        for index, values in enumerate(modalities, start=1):
            token = self.encoders[index](values)
            mask = active[:, index - 1 : index]
            encoded.append(torch.where(mask, token, torch.full_like(token, -1e9)))
        fused = torch.stack(encoded, dim=1).amax(dim=1)
        return self.head(fused)


def _hazard_nll(logits: Tensor, bins: Tensor, event: Tensor) -> Tensor:
    log_hazard = torch.nn.functional.logsigmoid(logits)
    log_survival = torch.nn.functional.logsigmoid(-logits)
    positions = torch.arange(logits.shape[1], device=logits.device)[None, :]
    before = positions < bins[:, None]
    through = positions <= bins[:, None]
    event_ll = (log_survival * before).sum(dim=1) + log_hazard.gather(
        1, bins[:, None]
    ).squeeze(1)
    censored_ll = (log_survival * through).sum(dim=1)
    return -torch.where(event, event_ll, censored_ll).mean()


def _train_multisurv(
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
    train_clinical = torch.as_tensor(train.clinical, dtype=torch.float64)
    eval_clinical = torch.as_tensor(evaluation.clinical, dtype=torch.float64)
    train_modalities = tuple(
        torch.as_tensor(values, dtype=torch.float64) for values in train.modalities
    )
    eval_modalities = tuple(
        torch.as_tensor(values, dtype=torch.float64) for values in evaluation.modalities
    )
    train_active = torch.as_tensor(train.active, dtype=torch.bool)
    eval_active = torch.as_tensor(evaluation.active, dtype=torch.bool)
    model = _MultiSurv(
        [train.clinical.shape[1], *(values.shape[1] for values in train.modalities)],
        int(config["representation_dim"]),
        len(edges),
    )
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    for _ in range(int(config["epochs"])):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = model(train_clinical, train_modalities, train_active)
        loss = _hazard_nll(logits, bins, event_tensor)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
    model.eval()
    with torch.no_grad():
        hazards = torch.sigmoid(model(eval_clinical, eval_modalities, eval_active)).numpy()
    cumulative_risk = 1.0 - np.cumprod(1.0 - hazards, axis=1)
    horizon_bin = min(int(np.searchsorted(edges, horizon, side="left")), len(edges) - 1)
    return cumulative_risk[:, -1], np.clip(cumulative_risk[:, horizon_bin], 0.0, 1.0)


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
    outcome = structured_survival(event, duration)
    if method == "COXPH":
        model = CoxPHSurvivalAnalysis(alpha=float(config["alpha"]), n_iter=1000).fit(
            train.clinical, outcome
        )
        return model.predict(evaluation.clinical), _survival_risk_at_horizon(
            model, evaluation.clinical, horizon
        )
    if method == "ENCOX":
        model = CoxnetSurvivalAnalysis(
            alphas=[float(config["alpha"])],
            l1_ratio=float(config["l1_ratio"]),
            max_iter=int(config["max_iter"]),
            fit_baseline_model=True,
            normalize=False,
        ).fit(train.direct, outcome)
        return model.predict(evaluation.direct), _survival_risk_at_horizon(
            model, evaluation.direct, horizon
        )
    if method == "RSF":
        model = RandomSurvivalForest(
            n_estimators=int(config["n_estimators"]),
            min_samples_leaf=int(config["min_samples_leaf"]),
            max_features=str(config["max_features"]),
            n_jobs=1,
            random_state=seed,
        ).fit(train.direct, outcome)
        score = model.predict(evaluation.direct)
        risk = _survival_risk_at_horizon(model, evaluation.direct, horizon)
        return score, risk
    if method == "GBSA":
        model = GradientBoostingSurvivalAnalysis(
            loss="coxph",
            n_estimators=int(config["n_estimators"]),
            learning_rate=float(config["learning_rate"]),
            max_depth=int(config["max_depth"]),
            min_samples_leaf=int(config["min_samples_leaf"]),
            max_features=str(config["max_features"]),
            random_state=seed,
        ).fit(train.direct, outcome)
        return model.predict(evaluation.direct), _survival_risk_at_horizon(
            model, evaluation.direct, horizon
        )
    if method == "XGBCOX":
        model = XGBRegressor(
            objective="survival:cox",
            n_estimators=int(config["n_estimators"]),
            learning_rate=float(config["learning_rate"]),
            max_depth=int(config["max_depth"]),
            min_child_weight=float(config["min_child_weight"]),
            subsample=float(config["subsample"]),
            colsample_bytree=float(config["colsample_bytree"]),
            reg_alpha=float(config["reg_alpha"]),
            reg_lambda=float(config["reg_lambda"]),
            tree_method="hist",
            n_jobs=1,
            random_state=seed,
        ).fit(train.direct, _encode_xgb_labels(event, duration), verbose=False)
        train_score = model.predict(train.direct, output_margin=True)
        eval_score = model.predict(evaluation.direct, output_margin=True)
        risk = breslow_risk_at_horizon(duration, event, train_score, eval_score, horizon)
        return eval_score, risk
    if method == "DEEPSURV":
        return _train_deepsurv(train, event, duration, evaluation, config, seed, horizon)
    if method == "DEEPHIT":
        return _train_deephit(train, event, duration, evaluation, config, seed, horizon)
    if method == "MULTISURV":
        return _train_multisurv(train, event, duration, evaluation, config, seed, horizon)
    raise ValueError(f"unsupported U9 method: {method}")


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
        row: dict[str, object] = {
            "method": method,
            "label": methods[method]["label"],
            "citation_key": methods[method].get("citation_key"),
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
    expected_rows = len(ids) * len(seeds)
    if len(v1r) != expected_rows:
        raise ValueError(f"V1R OOF row count {len(v1r)} differs from {expected_rows}")
    prediction_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    output_dir = root / DEFAULT_OUTPUT
    prediction_dir = root / DEFAULT_PREDICTIONS
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_dir.mkdir(parents=True, exist_ok=True)

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
            {
                "method": "V1R",
                "seed": seed,
                "runtime_seconds": math.nan,
                **v1r_values,
            }
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
        pd.DataFrame(metric_rows).to_csv(output_dir / "u9_metrics_checkpoint.csv", index=False)
        pd.DataFrame(prediction_rows).to_csv(
            prediction_dir / "u9_predictions_checkpoint.csv", index=False
        )

    metric_frame = pd.DataFrame(metric_rows)
    summary = _summary(metric_frame, methods)
    per_seed_path = output_dir / "u9_metrics_by_seed.csv"
    summary_path = output_dir / "u9_main_table_summary.csv"
    prediction_path = prediction_dir / "u9_repeated_oof_predictions.csv"
    metric_frame.to_csv(per_seed_path, index=False)
    summary.to_csv(summary_path, index=False)
    pd.DataFrame(prediction_rows).to_csv(prediction_path, index=False)
    payload = {
        "schema_version": "0.1",
        "stage_id": "U9_PUBLISHED_COMPARATOR_BENCHMARK",
        "analysis_label": spec["analysis_label"],
        "estimand": {
            "cohort": "HANCOCK_official_training",
            "n": len(ids),
            "events": int(event.sum()),
            "horizon_days": horizon,
        },
        "methods": list(METHODS),
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
    audit_path = output_dir / "aggregate_u9_published_comparator_benchmark_audit.json"
    audit_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "u9_metrics_checkpoint.csv").unlink(missing_ok=True)
    (prediction_dir / "u9_predictions_checkpoint.csv").unlink(missing_ok=True)
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
