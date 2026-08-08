"""Phase 5 development-only stress tests, ablations, subgroup analysis, and freeze."""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.optimize import nnls
from scipy.stats import rankdata
from sksurv.ensemble import RandomSurvivalForest
from sksurv.linear_model import CoxnetSurvivalAnalysis

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from trust_hn.data.phase3_features import StudyData, load_phase3_study_data
from trust_hn.evaluation.phase3 import (
    NumericMatrixPreprocessor,
    _assert_aggregate_privacy,
    _infer_columns,
    _missingness_matrix,
    _sha256,
)
from trust_hn.evaluation.phase4 import RANK_SOURCE_COLUMNS, _cross_fitted_anchor_scores
from trust_hn.metrics.survival import (
    evaluate_survival_predictions,
    ipcw_binary_outcomes,
    structured_survival,
)
from trust_hn.models.residual_fusion import StackedResidualSurvivalModel
from trust_hn.models.survival_baselines import (
    SurvivalPrediction,
    TabularPreprocessor,
    _survival_risk_at_horizon,
)
from trust_hn.reliability.ablations import (
    CLINICAL_COMPONENTS,
    MODALITY_COMPONENTS,
    ablated_unreliability,
    component_matrix,
)
from trust_hn.reliability.gating import (
    TripleOODDetector,
    assign_actions,
    empirical_percentile,
    gated_risk,
    quantile_threshold,
)

matplotlib.rcParams["svg.hashsalt"] = "trust-hn-phase5"

GATE_VARIANTS = ("ood_only", "uncertainty_only", "full_equal_weight", "full_learned_nonnegative")
COMMON_SCENARIOS = (
    "clean",
    "random_cell_dropout_10pct",
    "random_cell_dropout_30pct",
    "measurement_noise_0.5sd",
    "location_shift_1sd",
    "row_permutation_negative_control",
    "complete_modality_dropout",
)
HANCOCK_SCENARIOS = (
    "blood_block_dropout_30pct_rows",
    "tma_block_dropout_30pct_rows",
    "blood_and_tma_dropout_30pct_rows",
    "oropharynx_targeted_tma_dropout",
)


@dataclass(frozen=True)
class FittedEstimator:
    model: object
    horizon: float

    def predict(self, values: np.ndarray) -> SurvivalPrediction:
        matrix = np.asarray(values, dtype=float)
        score = np.asarray(self.model.predict(matrix), dtype=float)
        risk = _survival_risk_at_horizon(self.model, matrix, self.horizon)
        return SurvivalPrediction(score, risk)


@dataclass
class StressSystem:
    data: StudyData
    config: Mapping[str, object]
    seed: int
    bootstrap_size: int
    representation: str = "gene_level"
    clinical_prep: TabularPreprocessor | None = None
    modality_prep: TabularPreprocessor | NumericMatrixPreprocessor | None = None
    clinical_train_matrix: np.ndarray | None = None
    clinical_eval_matrix: np.ndarray | None = None
    modality_train_matrix: np.ndarray | None = None
    b2: FittedEstimator | None = None
    b3: FittedEstimator | None = None
    b4: FittedEstimator | None = None
    b5: FittedEstimator | None = None
    b6: StackedResidualSurvivalModel | None = None
    clinical_detector: TripleOODDetector | None = None
    modality_detector: TripleOODDetector | None = None
    clinical_bootstrap: list[FittedEstimator] | None = None
    fusion_bootstrap: list[StackedResidualSurvivalModel] | None = None
    anchor_training_score: np.ndarray | None = None
    m0: FittedEstimator | None = None
    m0_variable: np.ndarray | None = None

    @staticmethod
    def _rank_frame(frame: pd.DataFrame) -> pd.DataFrame:
        matrix = frame.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        medians = np.nanmedian(matrix, axis=0)
        filled = np.where(np.isnan(matrix), np.where(np.isfinite(medians), medians, 0.0), matrix)
        ranked = rankdata(filled, axis=1, method="average") / float(filled.shape[1])
        return pd.DataFrame(ranked, columns=frame.columns, index=frame.index)

    def _representation_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        return (
            self._rank_frame(frame) if self.representation == "within_sample_rank" else frame.copy()
        )

    def _fit_preprocessors(self) -> None:
        clinical_train = self.data.clinical_train
        numeric, categorical = _infer_columns(clinical_train, self.data.study)
        self.clinical_prep = TabularPreprocessor(numeric, categorical).fit(clinical_train)
        self.clinical_train_matrix = self.clinical_prep.transform(clinical_train)
        self.clinical_eval_matrix = self.clinical_prep.transform(self.data.clinical_calibration)
        assert self.data.modality_train is not None
        modality_train = self._representation_frame(self.data.modality_train)
        if self.data.study == "TCGA-HNSC" or self.representation == "median_no_indicator":
            top_k = (
                int(self.config.get("tcga_expression_foldwise_variance_top_k", 500))
                if self.data.study == "TCGA-HNSC"
                else None
            )
            self.modality_prep = NumericMatrixPreprocessor(top_k=top_k).fit(modality_train)
        else:
            numeric, categorical = _infer_columns(modality_train, self.data.study)
            self.modality_prep = TabularPreprocessor(numeric, categorical).fit(modality_train)
        self.modality_train_matrix = self.modality_prep.transform(modality_train)

    def _fit_estimator(
        self, model_id: str, x: np.ndarray, rows: np.ndarray | None = None
    ) -> FittedEstimator:
        event = self.data.train_event if rows is None else self.data.train_event[rows]
        time = self.data.train_time if rows is None else self.data.train_time[rows]
        values = x if rows is None else x[rows]
        if model_id == "B3":
            model = RandomSurvivalForest(
                n_estimators=int(self.config.get("rsf_n_estimators", 200)),
                min_samples_leaf=int(self.config.get("rsf_min_samples_leaf", 10)),
                max_features=self.config.get("rsf_max_features", "sqrt"),
                n_jobs=1,
                random_state=self.seed + 103,
            )
        else:
            model = CoxnetSurvivalAnalysis(
                alphas=[float(self.config.get("coxnet_alpha", 0.05))],
                l1_ratio=float(self.config.get("coxnet_l1_ratio", 0.5)),
                max_iter=int(self.config.get("coxnet_max_iter", 100000)),
                fit_baseline_model=True,
                normalize=False,
            )
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*coefficients are zero.*")
            warnings.filterwarnings("ignore", message=".*did not converge.*")
            model.fit(values, structured_survival(event, time))
        return FittedEstimator(model, float(self.config["horizon_days"]))

    def _bootstrap_indices(self, count: int, offset: int) -> list[np.ndarray]:
        if count == 0:
            return []
        rng = np.random.default_rng(self.seed + offset)
        n = len(self.data.train_event)
        minimum_unique = max(
            2, math.ceil(float(self.config.get("bootstrap_min_unique_fraction", 0.5)) * n)
        )
        samples: list[np.ndarray] = []
        attempts = 0
        while len(samples) < count and attempts < max(100, count * 40):
            attempts += 1
            sample = rng.integers(0, n, size=n)
            event = self.data.train_event[sample]
            if np.unique(sample).size < minimum_unique or event.all() or not event.any():
                continue
            samples.append(sample)
        if len(samples) != count:
            raise RuntimeError(f"bootstrap sampling incomplete: {len(samples)}/{count}")
        return samples

    def fit(self) -> StressSystem:
        if self.data.modality_train is None or self.data.modality_calibration is None:
            raise ValueError(self.data.modality_blocker or "additional modality unavailable")
        self._fit_preprocessors()
        assert self.clinical_train_matrix is not None and self.modality_train_matrix is not None
        horizon = float(self.config["horizon_days"])
        self.b2 = self._fit_estimator("B2", self.clinical_train_matrix)
        self.b3 = self._fit_estimator("B3", self.clinical_train_matrix)
        self.b4 = self._fit_estimator("B4", self.modality_train_matrix)
        self.b5 = self._fit_estimator(
            "B5", np.column_stack([self.clinical_train_matrix, self.modality_train_matrix])
        )
        self.anchor_training_score = _cross_fitted_anchor_scores(
            self.data.clinical_train,
            self.data.train_event,
            self.data.train_time,
            study=self.data.study,
            folds=int(self.config.get("cv_folds", 5)),
            horizon=horizon,
            random_state=self.seed + 13,
            config=self.config,
        )
        outcome = structured_survival(self.data.train_event, self.data.train_time)
        self.b6 = StackedResidualSurvivalModel(self.config).fit(
            self.anchor_training_score, self.modality_train_matrix, outcome, horizon=horizon
        )
        detector_args = dict(
            n_neighbors=int(self.config.get("knn_neighbors", 10)),
            isolation_estimators=int(self.config.get("isolation_forest_estimators", 200)),
            max_features=int(self.config.get("ood_embedding_max_features", 50)),
        )
        self.clinical_detector = TripleOODDetector(
            **detector_args, random_state=self.seed + 113
        ).fit(self.clinical_train_matrix)
        self.modality_detector = TripleOODDetector(
            **detector_args, random_state=self.seed + 127
        ).fit(self.modality_train_matrix)
        full_train = pd.concat([self.data.clinical_train, self.data.modality_train], axis=1)
        missing = _missingness_matrix(full_train)
        self.m0_variable = np.var(missing, axis=0) > 1e-12
        if self.m0_variable.any():
            self.m0 = self._fit_estimator("M0", missing[:, self.m0_variable])
        candidate_count = self.bootstrap_size * 20
        self.clinical_bootstrap = []
        for sample in self._bootstrap_indices(candidate_count, 131):
            try:
                self.clinical_bootstrap.append(
                    self._fit_estimator("B2", self.clinical_train_matrix, sample)
                )
            except Exception:
                continue
            if len(self.clinical_bootstrap) == self.bootstrap_size:
                break
        if len(self.clinical_bootstrap) != self.bootstrap_size:
            raise RuntimeError(
                "clinical bootstrap fitting incomplete: "
                f"{len(self.clinical_bootstrap)}/{self.bootstrap_size}"
            )
        self.fusion_bootstrap = []
        for sample in self._bootstrap_indices(candidate_count, 137):
            try:
                self.fusion_bootstrap.append(
                    StackedResidualSurvivalModel(self.config).fit(
                        self.anchor_training_score[sample],
                        self.modality_train_matrix[sample],
                        outcome[sample],
                        horizon=horizon,
                    )
                )
            except Exception:
                continue
            if len(self.fusion_bootstrap) == self.bootstrap_size:
                break
        if len(self.fusion_bootstrap) != self.bootstrap_size:
            raise RuntimeError(
                "fusion bootstrap fitting incomplete: "
                f"{len(self.fusion_bootstrap)}/{self.bootstrap_size}"
            )
        return self

    @staticmethod
    def _ensemble_summary(predictions: Sequence[np.ndarray], n: int) -> tuple[np.ndarray, ...]:
        if not predictions:
            z = np.zeros(n, dtype=float)
            return z, z, z, z, z
        matrix = np.vstack(predictions)
        lower, upper = np.quantile(matrix, [0.025, 0.975], axis=0)
        sd = np.std(matrix, axis=0, ddof=1) if len(matrix) > 1 else np.zeros(n)
        return np.median(matrix, axis=0), sd, lower, upper, upper - lower

    def predict(self, modality_eval_raw: pd.DataFrame, scenario_seed: int) -> pd.DataFrame:
        required = (
            self.modality_prep,
            self.clinical_eval_matrix,
            self.b2,
            self.b3,
            self.b4,
            self.b5,
            self.b6,
            self.clinical_detector,
            self.modality_detector,
            self.clinical_bootstrap,
            self.fusion_bootstrap,
        )
        if any(item is None for item in required):
            raise RuntimeError("stress system must be fitted")
        modality_eval = self._representation_frame(modality_eval_raw)
        x_modality = self.modality_prep.transform(modality_eval)  # type: ignore[union-attr]
        x_clinical = self.clinical_eval_matrix
        assert x_clinical is not None
        b2 = self.b2.predict(x_clinical)  # type: ignore[union-attr]
        b3 = self.b3.predict(x_clinical)  # type: ignore[union-attr]
        b4 = self.b4.predict(x_modality)  # type: ignore[union-attr]
        b5 = self.b5.predict(np.column_stack([x_clinical, x_modality]))  # type: ignore[union-attr]
        b6 = self.b6.predict(b2.risk_score, x_modality)  # type: ignore[union-attr]
        permutation = np.random.default_rng(scenario_seed + 109).permutation(len(x_modality))
        perturbed = self.b6.predict(b2.risk_score, x_modality[permutation])  # type: ignore[union-attr]
        clinical_ood = self.clinical_detector.score(x_clinical)  # type: ignore[union-attr]
        modality_ood = self.modality_detector.score(x_modality)  # type: ignore[union-attr]
        clinical_ensemble = [
            model.predict(x_clinical).risk_horizon for model in self.clinical_bootstrap or []
        ]
        fusion_ensemble = [
            model.predict(b2.risk_score, x_modality).risk_horizon
            for model in self.fusion_bootstrap or []
        ]
        clinical_summary = self._ensemble_summary(clinical_ensemble, len(x_clinical))
        fusion_summary = self._ensemble_summary(fusion_ensemble, len(x_clinical))
        missingness = _missingness_matrix(modality_eval_raw)
        missing_fraction = (
            missingness.mean(axis=1) if missingness.shape[1] else np.zeros(len(x_clinical))
        )
        frame = pd.DataFrame(
            {
                "b2_score": b2.risk_score,
                "b2_risk": b2.risk_horizon,
                "b3_score": b3.risk_score,
                "b3_risk": b3.risk_horizon,
                "b4_score": b4.risk_score,
                "b4_risk": b4.risk_horizon,
                "b5_score": b5.risk_score,
                "b5_risk": b5.risk_horizon,
                "b6_score": b6.risk_score,
                "b6_risk": b6.risk_horizon,
                "clinical_uncertainty_median": clinical_summary[0],
                "clinical_uncertainty_sd": clinical_summary[1],
                "clinical_uncertainty_lower95": clinical_summary[2],
                "clinical_uncertainty_upper95": clinical_summary[3],
                "clinical_uncertainty_width95": clinical_summary[4],
                "clinical_model_disagreement": np.abs(b2.risk_horizon - b3.risk_horizon),
                "fusion_uncertainty_median": fusion_summary[0],
                "fusion_uncertainty_sd": fusion_summary[1],
                "fusion_uncertainty_lower95": fusion_summary[2],
                "fusion_uncertainty_upper95": fusion_summary[3],
                "fusion_uncertainty_width95": fusion_summary[4],
                "perturbation_sensitivity": np.abs(b6.risk_horizon - perturbed.risk_horizon),
                "modality_missingness": missing_fraction,
                "modality_missing": missing_fraction >= 1.0 - 1e-12,
                "fusion_disagreement": np.abs(b6.risk_horizon - b5.risk_horizon),
                "clinical_ood_mahalanobis": clinical_ood.mahalanobis,
                "clinical_ood_knn": clinical_ood.knn,
                "clinical_ood_isolation_forest": clinical_ood.isolation_forest,
                "modality_ood_mahalanobis": modality_ood.mahalanobis,
                "modality_ood_knn": modality_ood.knn,
                "modality_ood_isolation_forest": modality_ood.isolation_forest,
            }
        )
        if self.m0 is not None and self.m0_variable is not None:
            full_eval = pd.concat(
                [self.data.clinical_calibration, modality_eval_raw.reset_index(drop=True)], axis=1
            )
            m0 = self.m0.predict(_missingness_matrix(full_eval)[:, self.m0_variable])
            frame["m0_score"], frame["m0_risk"] = m0.risk_score, m0.risk_horizon
        return frame


def apply_modality_perturbation(
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
    *,
    study: str,
    scenario: str,
    seed: int,
    clinical: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Apply an outcome-free deterministic calibration-predictor perturbation."""
    result = evaluation.copy(deep=True)
    salt = int(hashlib.sha256(scenario.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed + salt)
    if scenario == "clean":
        return result
    if scenario.startswith("random_cell_dropout_"):
        fraction = 0.10 if "10pct" in scenario else 0.30
        return result.mask(rng.random(result.shape) < fraction)
    if scenario == "measurement_noise_0.5sd":
        train_numeric = train.apply(pd.to_numeric, errors="coerce")
        values = result.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        scales = train_numeric.std(axis=0, ddof=0).replace(0, 1).fillna(1).to_numpy(dtype=float)
        noise = rng.normal(0.0, 0.5, size=result.shape) * scales
        values = np.where(np.isnan(values), np.nan, values + noise)
        return pd.DataFrame(values, columns=result.columns, index=result.index)
    if scenario == "location_shift_1sd":
        numeric = result.apply(pd.to_numeric, errors="coerce")
        scales = (
            train.apply(pd.to_numeric, errors="coerce").std(axis=0, ddof=0).replace(0, 1).fillna(1)
        )
        count = max(1, math.ceil(0.30 * result.shape[1]))
        for index in rng.choice(result.shape[1], size=count, replace=False):
            numeric.iloc[:, index] = numeric.iloc[:, index] + float(scales.iloc[index])
        return numeric
    if scenario == "row_permutation_negative_control":
        return result.iloc[rng.permutation(len(result))].reset_index(drop=True)
    if scenario == "complete_modality_dropout":
        return result.mask(np.ones(result.shape, dtype=bool))
    if study != "HANCOCK":
        raise ValueError(f"scenario {scenario} is not available for {study}")
    tma_columns = [column for column in result.columns if re.search(r"^(cd3|cd8)_", column, re.I)]
    blood_columns = [column for column in result.columns if column not in tma_columns]
    selected_rows = rng.choice(
        len(result), size=max(1, math.ceil(0.30 * len(result))), replace=False
    )
    if scenario == "blood_block_dropout_30pct_rows":
        result.loc[result.index[selected_rows], blood_columns] = np.nan
    elif scenario == "tma_block_dropout_30pct_rows":
        result.loc[result.index[selected_rows], tma_columns] = np.nan
    elif scenario == "blood_and_tma_dropout_30pct_rows":
        result.loc[result.index[selected_rows], :] = np.nan
    elif scenario == "oropharynx_targeted_tma_dropout":
        if clinical is None:
            raise ValueError("targeted shortcut perturbation requires clinical predictors")
        site_column = "primary_tumor_site" if "primary_tumor_site" in clinical else "site"
        rows = (
            clinical.get(site_column, pd.Series("", index=clinical.index))
            .astype("string")
            .str.contains("oroph", case=False, na=False)
        )
        result.loc[rows.to_numpy(), tma_columns] = np.nan
    else:
        raise ValueError(f"unsupported perturbation scenario: {scenario}")
    return result


def learned_nonnegative_weights(values: np.ndarray, target: np.ndarray) -> np.ndarray:
    matrix, outcome = np.asarray(values, dtype=float), np.asarray(target, dtype=float)
    finite = np.isfinite(matrix).all(axis=1) & np.isfinite(outcome)
    if finite.sum() < matrix.shape[1] + 2 or float(np.sum(outcome[finite])) <= 1e-12:
        return np.full(matrix.shape[1], 1.0 / matrix.shape[1])
    weights, _ = nnls(matrix[finite], outcome[finite])
    return (
        weights / weights.sum()
        if float(weights.sum()) > 1e-12
        else np.full(matrix.shape[1], 1.0 / matrix.shape[1])
    )


def _learned_weights_from_oof(
    root: Path, data: StudyData, seed: int, horizon: float
) -> dict[str, np.ndarray]:
    slug = data.study.lower().replace("-", "_")
    frame = pd.read_csv(root / "results" / "predictions" / "phase4" / f"{slug}_seed{seed}_oof.csv")
    event = frame["event"].astype(bool).to_numpy()
    time = frame["duration_days"].to_numpy(dtype=float)
    outcome, ipcw = ipcw_binary_outcomes(event, time, event, time, horizon)
    clinical_error = ipcw * (outcome - frame["b2_risk"].to_numpy(dtype=float)) ** 2
    fusion_error = ipcw * (outcome - frame["b6_risk"].to_numpy(dtype=float)) ** 2
    return {
        "clinical": learned_nonnegative_weights(
            component_matrix(frame, CLINICAL_COMPONENTS), clinical_error
        ),
        "modality": learned_nonnegative_weights(
            component_matrix(frame, MODALITY_COMPONENTS),
            np.maximum(fusion_error - clinical_error, 0.0),
        ),
    }


def _rank_reliability(frame: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in RANK_SOURCE_COLUMNS:
        result[f"rank_{column}"] = empirical_percentile(
            result[column].to_numpy(dtype=float), reference[column].to_numpy(dtype=float)
        )
    result["clinical_ood_rank"] = result[
        [
            "rank_clinical_ood_mahalanobis",
            "rank_clinical_ood_knn",
            "rank_clinical_ood_isolation_forest",
        ]
    ].mean(axis=1)
    result["modality_ood_rank"] = result[
        [
            "rank_modality_ood_mahalanobis",
            "rank_modality_ood_knn",
            "rank_modality_ood_isolation_forest",
        ]
    ].mean(axis=1)
    result["clinical_unreliability"] = component_matrix(result, CLINICAL_COMPONENTS).mean(axis=1)
    result["modality_unreliability"] = component_matrix(result, MODALITY_COMPONENTS).mean(axis=1)
    return result


def _profile_label(coverage: float) -> str:
    return str(round(coverage * 100))


def _metric(
    data: StudyData,
    *,
    seed: int,
    scenario: str,
    model: str,
    risk_score: np.ndarray,
    risk_horizon: np.ndarray,
    horizon: float,
    survival_floor: float,
    gate_variant: str = "none",
    profile: str = "full",
    reference_predictions: Mapping[str, tuple[np.ndarray, np.ndarray]] | None = None,
) -> dict[str, object]:
    finite = np.isfinite(risk_score) & np.isfinite(risk_horizon)
    base = {
        "study": data.study,
        "seed": seed,
        "scenario": scenario,
        "model": model,
        "gate_variant": gate_variant,
        "profile": profile,
        "coverage": float(finite.mean()),
    }
    if not finite.any():
        return {**base, "n": 0.0, "events": 0.0, "ipcw_brier": math.nan}
    metrics = evaluate_survival_predictions(
        data.train_event,
        data.train_time,
        data.calibration_event[finite],
        data.calibration_time[finite],
        np.asarray(risk_score)[finite],
        np.asarray(risk_horizon)[finite],
        horizon,
        survival_floor=survival_floor,
    )
    result = {**base, **metrics}
    for name, (reference_score, reference_risk) in (reference_predictions or {}).items():
        reference_score = np.asarray(reference_score, dtype=float)
        reference_risk = np.asarray(reference_risk, dtype=float)
        if not (
            np.isfinite(reference_score[finite]).all() and np.isfinite(reference_risk[finite]).all()
        ):
            result[f"{name.lower()}_subset_ipcw_brier"] = math.nan
            continue
        reference_metrics = evaluate_survival_predictions(
            data.train_event,
            data.train_time,
            data.calibration_event[finite],
            data.calibration_time[finite],
            reference_score[finite],
            reference_risk[finite],
            horizon,
            survival_floor=survival_floor,
        )
        result[f"{name.lower()}_subset_ipcw_brier"] = reference_metrics["ipcw_brier"]
    return result


def subgroup_labels(
    clinical: pd.DataFrame, natural_missing: np.ndarray, *, study: str
) -> dict[str, pd.Series]:
    if study == "HANCOCK":
        age = pd.to_numeric(clinical.get("age_at_initial_diagnosis"), errors="coerce")
        site = clinical.get("primary_tumor_site", pd.Series("Unknown", index=clinical.index))
        stage = clinical.get("pT_stage", pd.Series("Unknown", index=clinical.index))
        hpv = clinical.get("hpv_association_p16", pd.Series("Unknown", index=clinical.index))
    else:
        age = pd.to_numeric(clinical.get("age"), errors="coerce")
        site = clinical.get("site", pd.Series("Unknown", index=clinical.index))
        stage = clinical.get("stage", pd.Series("Unknown", index=clinical.index))
        hpv = clinical.get("hpv", pd.Series("Unknown", index=clinical.index))
    sex = clinical.get("sex", pd.Series("Unknown", index=clinical.index)).astype("string")
    site_text, stage_text, hpv_text = (
        site.astype("string"),
        stage.astype("string").str.upper(),
        hpv.astype("string").str.casefold(),
    )
    early = stage_text.str.match(r"^(I|II)([^I]|$)", na=False)
    advanced = stage_text.str.contains(r"III|IV", regex=True, na=False)
    return {
        "sex": sex.fillna("Unknown").str.strip().str.casefold(),
        "age_group": pd.Series(
            np.where(age.isna(), "unknown", np.where(age < 65, "<65", ">=65")), index=clinical.index
        ),
        "site_group": pd.Series(
            np.where(site_text.str.contains("oroph", case=False, na=False), "oropharynx", "other"),
            index=clinical.index,
        ),
        "stage_group": pd.Series(
            np.where(early, "early", np.where(advanced, "advanced", "unknown")),
            index=clinical.index,
        ),
        "hpv_group": pd.Series(
            np.where(
                hpv_text.str.contains("pos|positive|associated|16", regex=True, na=False),
                "positive",
                np.where(
                    hpv_text.str.contains("neg|negative", regex=True, na=False),
                    "negative",
                    "unknown",
                ),
            ),
            index=clinical.index,
        ),
        "natural_modality_missingness": pd.Series(
            np.where(np.asarray(natural_missing, dtype=bool), "missing", "complete"),
            index=clinical.index,
        ),
    }


def _subgroup_rows(
    data: StudyData,
    frame: pd.DataFrame,
    actions: np.ndarray,
    *,
    seed: int,
    horizon: float,
    survival_floor: float,
    minimum_n: int,
    minimum_events: int,
) -> list[dict[str, object]]:
    assert data.modality_calibration is not None
    labels = subgroup_labels(
        data.clinical_calibration,
        _missingness_matrix(data.modality_calibration).any(axis=1),
        study=data.study,
    )
    final = gated_risk(frame["b2_risk"].to_numpy(), frame["b6_risk"].to_numpy(), actions)
    models = {
        "B2": (frame["b2_score"].to_numpy(), frame["b2_risk"].to_numpy()),
        "B6": (frame["b6_score"].to_numpy(), frame["b6_risk"].to_numpy()),
        "B7_full_equal_weight_90": (final, final),
    }
    rows: list[dict[str, object]] = []
    for variable, groups in labels.items():
        for value in sorted(groups.astype(str).unique()):
            base_mask = groups.astype(str).eq(value).to_numpy()
            if (
                int(base_mask.sum()) < minimum_n
                or int(data.calibration_event[base_mask].sum()) < minimum_events
            ):
                continue
            for model, (score, risk) in models.items():
                finite = base_mask & np.isfinite(score) & np.isfinite(risk)
                if (
                    int(finite.sum()) < minimum_n
                    or int(data.calibration_event[finite].sum()) < minimum_events
                ):
                    continue
                metrics = evaluate_survival_predictions(
                    data.train_event,
                    data.train_time,
                    data.calibration_event[finite],
                    data.calibration_time[finite],
                    score[finite],
                    risk[finite],
                    horizon,
                    survival_floor=survival_floor,
                )
                rows.append(
                    {
                        "study": data.study,
                        "seed": seed,
                        "subgroup_variable": variable,
                        "subgroup": value,
                        "model": model,
                        "parent_n": int(base_mask.sum()),
                        "coverage": float(finite.sum() / base_mask.sum()),
                        **metrics,
                    }
                )
    return rows


def build_sealed_cohort_manifest(
    source: Path, *, cohort: str, split_roles: set[str]
) -> dict[str, object]:
    frame = pd.read_csv(source, dtype={"native_id": "string"}, usecols=["native_id", "split_role"])
    ids = sorted(
        frame.loc[frame["split_role"].isin(split_roles), "native_id"]
        .astype(str)
        .str.strip()
        .tolist()
    )
    return {
        "cohort": cohort,
        "split_roles": sorted(split_roles),
        "patient_count": len(ids),
        "ordered_id_set_sha256": hashlib.sha256("\0".join(ids).encode("utf-8")).hexdigest(),
        "source_adapter_sha256": _sha256(source),
        "contains_patient_level_identifiers": False,
        "contains_outcomes": False,
    }


def _write_sealed_manifest(base: Path) -> Path:
    cohorts = [
        ("RADCURE challenge test", "radcure", {"sealed_test"}),
        ("HANCOCK OOD test", "hancock", {"sealed_test"}),
        ("GSE65858 external test", "gse65858", {"external_test"}),
        ("GSE41613 sensitivity", "gse41613", {"sensitivity"}),
    ]
    payload = {
        "schema_version": "1.0",
        "created_on": "2026-08-07",
        "purpose": "Aggregate set digests for Phase 6 integrity checks; no patient IDs or outcomes",
        "cohorts": [
            build_sealed_cohort_manifest(
                base / "data" / "interim" / "phase2" / slug / "adapter_records.csv",
                cohort=name,
                split_roles=roles,
            )
            for name, slug, roles in cohorts
        ],
    }
    path = base / "data" / "manifests" / "sealed" / "phase6_cohort_set_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _git_head(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root.parent, text=True
        ).strip()
    except Exception:
        return None


def _write_freeze(base: Path, sealed_manifest: Path) -> Path:
    decision_files = [
        "configs/base.yaml",
        "configs/hancock.yaml",
        "configs/tcga_geo.yaml",
        "configs/radcure.yaml",
        "configs/phase3_baselines.json",
        "configs/phase3_governance.json",
        "configs/phase4_trust_hn.json",
        "configs/phase4_governance.json",
        "configs/phase5_stress_tests.json",
        "configs/phase5_governance.json",
        "src/trust_hn/models/residual_fusion.py",
        "src/trust_hn/reliability/gating.py",
        "src/trust_hn/reliability/ablations.py",
        "src/trust_hn/evaluation/phase4.py",
        "src/trust_hn/evaluation/phase5.py",
        "scripts/run_phase5.py",
    ]
    payload = {
        "schema_version": "2.0",
        "status": "FROZEN",
        "frozen_at": "2026-08-07",
        "git_commit": _git_head(base),
        "config_sha256": {path: _sha256(base / path) for path in decision_files},
        "sealed_manifest_sha256": {
            sealed_manifest.relative_to(base).as_posix(): _sha256(sealed_manifest)
        },
        "primary_hypotheses_frozen": True,
        "models_frozen": True,
        "thresholds_frozen": True,
        "primary_gate": "full_equal_weight_90",
        "sensitivity_profiles": ["full_equal_weight_80", "full_equal_weight_100"],
        "phase6_outcomes_seen": False,
        "test_unseal": {
            "approved": False,
            "approved_by": None,
            "approved_at": None,
            "approval_token_sha256": None,
            "reason": "Phase 6 requires separate explicit user authorization after Phase 5 review",
        },
        "notes": (
            "Phase 5 freeze records exact file hashes. Locked/external evaluation remains refused."
        ),
    }
    path = base / "configs" / "analysis_freeze.yaml"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _plot_stress(metrics: pd.DataFrame, path: Path) -> None:
    local = metrics.loc[
        metrics["model"].isin(["B2", "B5", "B6", "B7"])
        & metrics["gate_variant"].isin(["none", "full_equal_weight"])
        & metrics["profile"].isin(["full", "90"])
    ]
    summary = local.groupby(["study", "scenario", "model"], as_index=False)["ipcw_brier"].mean()
    studies = list(summary["study"].unique())
    fig, axes = plt.subplots(len(studies), 1, figsize=(12, 5 * len(studies)), squeeze=False)
    for axis, study in zip(axes[:, 0], studies, strict=False):
        summary.loc[summary["study"].eq(study)].pivot(
            index="scenario", columns="model", values="ipcw_brier"
        ).plot(kind="bar", ax=axis)
        axis.set_title(f"{study}: development stress-test IPCW Brier")
        axis.set_ylabel("IPCW Brier")
        axis.tick_params(axis="x", labelrotation=45)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, metadata={"Date": "2026-08-07"})
    plt.close(fig)


def _plot_actions(actions: pd.DataFrame, path: Path) -> None:
    local = actions.loc[
        actions["gate_variant"].eq("full_equal_weight") & actions["profile"].eq("90")
    ]
    summary = local.groupby(["study", "scenario", "action"], as_index=False)["rate"].mean()
    studies = list(summary["study"].unique())
    fig, axes = plt.subplots(len(studies), 1, figsize=(12, 5 * len(studies)), squeeze=False)
    for axis, study in zip(axes[:, 0], studies, strict=False):
        summary.loc[summary["study"].eq(study)].pivot(
            index="scenario", columns="action", values="rate"
        ).plot(kind="bar", stacked=True, ax=axis)
        axis.set_title(f"{study}: primary gate action distribution")
        axis.set_ylabel("Rate")
        axis.tick_params(axis="x", labelrotation=45)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, metadata={"Date": "2026-08-07"})
    plt.close(fig)


def _acceptance_checks(
    metrics: pd.DataFrame, actions: pd.DataFrame, margin: Mapping[str, float], seed_count: int
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for study in sorted(metrics["study"].unique()):
        local = metrics.loc[metrics["study"].eq(study)]
        clean_b7 = local.loc[
            local["scenario"].eq("clean")
            & local["model"].eq("B7")
            & local["gate_variant"].eq("full_equal_weight")
            & local["profile"].eq("90"),
            "ipcw_brier",
        ]
        clean_b6 = local.loc[
            local["scenario"].eq("clean")
            & local["model"].eq("B7")
            & local["gate_variant"].eq("full_equal_weight")
            & local["profile"].eq("90"),
            "b6_subset_ipcw_brier",
        ]
        value = float(clean_b7.mean() - clean_b6.mean())
        threshold = float(margin["clean_b7_vs_b6_brier_noninferiority"])
        rows.append(
            {
                "study": study,
                "check": "clean_primary_b7_vs_b6_brier",
                "value": value,
                "criterion": f"<= {threshold}",
                "passed": value <= threshold,
            }
        )
        dropout_b7 = local.loc[
            local["scenario"].eq("complete_modality_dropout")
            & local["model"].eq("B7")
            & local["gate_variant"].eq("full_equal_weight")
            & local["profile"].eq("100"),
            "ipcw_brier",
        ]
        dropout_b2 = local.loc[
            local["scenario"].eq("complete_modality_dropout")
            & local["model"].eq("B7")
            & local["gate_variant"].eq("full_equal_weight")
            & local["profile"].eq("100"),
            "b2_subset_ipcw_brier",
        ]
        value = float(dropout_b7.mean() - dropout_b2.mean())
        threshold = float(margin["complete_dropout_b7_100_vs_b2_brier_noninferiority"])
        rows.append(
            {
                "study": study,
                "check": "complete_dropout_b7_100_vs_b2_brier",
                "value": value,
                "criterion": f"<= {threshold}",
                "passed": value <= threshold,
            }
        )
        fallback = actions.loc[
            actions["study"].eq(study)
            & actions["scenario"].eq("complete_modality_dropout")
            & actions["gate_variant"].eq("full_equal_weight")
            & actions["profile"].eq("100")
            & actions["action"].eq("FALLBACK"),
            "rate",
        ].mean()
        threshold = float(margin["complete_dropout_fallback_rate_minimum"])
        rows.append(
            {
                "study": study,
                "check": "complete_dropout_fallback_rate",
                "value": float(fallback),
                "criterion": f">= {threshold}",
                "passed": float(fallback) >= threshold,
            }
        )
        primary = actions.loc[
            actions["study"].eq(study)
            & actions["gate_variant"].eq("full_equal_weight")
            & actions["profile"].eq("90")
        ]
        clean_response = (
            primary.loc[
                primary["scenario"].eq("clean") & primary["action"].isin(["FALLBACK", "ABSTAIN"])
            ]
            .groupby(["seed", "scenario"])["rate"]
            .sum()
            .mean()
        )
        severe = (
            primary.loc[
                primary["scenario"].isin(["location_shift_1sd", "complete_modality_dropout"])
                & primary["action"].isin(["FALLBACK", "ABSTAIN"])
            ]
            .groupby(["seed", "scenario"])["rate"]
            .sum()
            .mean()
        )
        value = float(severe - clean_response)
        threshold = float(margin["severe_shift_action_response_increase_minimum"])
        rows.append(
            {
                "study": study,
                "check": "severe_shift_action_response_increase",
                "value": value,
                "criterion": f">= {threshold}",
                "passed": value >= threshold,
            }
        )
    return pd.DataFrame(rows)


def _representation_sensitivity(
    data: StudyData, config: Mapping[str, object], seed: int, horizon: float, survival_floor: float
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if data.study == "TCGA-HNSC":
        system = StressSystem(data, config, seed, 0, representation="within_sample_rank").fit()
        prediction = system.predict(data.modality_calibration, seed + 7000)  # type: ignore[arg-type]
        representation, scenarios = "within_sample_rank", [("clean", prediction)]
    else:
        system = StressSystem(data, config, seed, 0, representation="median_no_indicator").fit()
        scenarios = []
        for scenario in ("clean", "random_cell_dropout_30pct"):
            perturbed = apply_modality_perturbation(
                data.modality_train,
                data.modality_calibration,
                study=data.study,
                scenario=scenario,
                seed=seed + 9000,
            )  # type: ignore[arg-type]
            scenarios.append((scenario, system.predict(perturbed, seed + 9000)))
        representation = "median_no_missing_indicator"
    for scenario, prediction in scenarios:
        for model in ("B4", "B5", "B6"):
            row = _metric(
                data,
                seed=seed,
                scenario=scenario,
                model=model,
                risk_score=prediction[f"{model.lower()}_score"].to_numpy(),
                risk_horizon=prediction[f"{model.lower()}_risk"].to_numpy(),
                horizon=horizon,
                survival_floor=survival_floor,
            )
            rows.append({"representation": representation, **row})
    return rows


def run(
    project_root: Path,
    *,
    studies: Sequence[str] | None = None,
    seeds: Sequence[int] | None = None,
    bootstrap_size: int | None = None,
    output_root: Path | None = None,
    write_freeze: bool = True,
) -> dict[str, object]:
    root = Path(project_root).resolve()
    base = Path(output_root).resolve() if output_root else root
    config_path = root / "configs" / "phase5_stress_tests.json"
    governance_path = root / "configs" / "phase5_governance.json"
    phase4_path = root / "configs" / "phase4_trust_hn.json"
    phase5_config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    governance = json.loads(governance_path.read_text(encoding="utf-8-sig"))
    phase4 = json.loads(phase4_path.read_text(encoding="utf-8-sig"))
    if phase5_config.get("status") != "FROZEN_FOR_PHASE5_DEVELOPMENT":
        raise PermissionError("Phase 5 configuration is not frozen for development")
    if governance.get("phase6_unseal_allowed") is not False:
        raise PermissionError("Phase 5 governance must refuse Phase 6 unsealing")
    selected_studies = list(studies or ["HANCOCK", "TCGA-HNSC"])
    selected_seeds = [int(value) for value in (seeds or phase5_config["seeds"])]
    ensemble = int(
        bootstrap_size if bootstrap_size is not None else phase5_config["bootstrap_ensemble_size"]
    )
    config = {
        **phase4.get("hyperparameters", {}),
        "horizon_days": float(phase5_config["horizon_days"]),
        "cv_folds": int(phase5_config["cv_folds"]),
    }
    horizon = float(config["horizon_days"])
    survival_floor = float(config.get("ipcw_survival_floor", 0.05))
    coverages = [float(value) for value in phase5_config["coverage_profiles"]]

    metrics_root, figure_root = base / "results/metrics/phase5", base / "results/figures/phase5"
    prediction_root, audit_root = base / "results/predictions/phase5", base / "docs/audits/phase5"
    for path in (metrics_root, figure_root, prediction_root, audit_root):
        path.mkdir(parents=True, exist_ok=True)
    metric_rows: list[dict[str, object]] = []
    action_rows: list[dict[str, object]] = []
    detection_rows: list[dict[str, object]] = []
    subgroup_rows: list[dict[str, object]] = []
    representation_rows: list[dict[str, object]] = []
    weight_rows: list[dict[str, object]] = []
    status_rows: list[dict[str, object]] = []
    if studies is None:
        status_rows.append(
            {
                "study": "RADCURE",
                "seed": "",
                "status": "blocked",
                "reason": phase5_config["blocked_or_deferred"]["RADCURE"],
            }
        )

    for study in selected_studies:
        data = load_phase3_study_data(root, study)
        if data.modality is None:
            status_rows.append(
                {"study": study, "seed": -1, "status": "blocked", "reason": data.modality_blocker}
            )
            continue
        scenarios = list(COMMON_SCENARIOS) + (list(HANCOCK_SCENARIOS) if study == "HANCOCK" else [])
        for seed in selected_seeds:
            try:
                system = StressSystem(data, config, seed, ensemble).fit()
                learned = _learned_weights_from_oof(root, data, seed, horizon)
                for domain, names in (
                    ("clinical", CLINICAL_COMPONENTS),
                    ("modality", MODALITY_COMPONENTS),
                ):
                    for name, value in zip(names, learned[domain], strict=True):
                        weight_rows.append(
                            {
                                "study": study,
                                "seed": seed,
                                "domain": domain,
                                "component": name,
                                "weight": float(value),
                            }
                        )
                clean_raw = system.predict(data.modality_calibration, seed)  # type: ignore[arg-type]
                clean = _rank_reliability(clean_raw, clean_raw)
                thresholds: dict[tuple[str, str], tuple[float, float]] = {}
                for variant in GATE_VARIANTS:
                    clinical_score, modality_score = ablated_unreliability(clean, variant, learned)
                    for coverage in coverages:
                        label = _profile_label(coverage)
                        thresholds[(variant, label)] = (
                            quantile_threshold(clinical_score, coverage),
                            quantile_threshold(modality_score, coverage),
                        )
                traces: list[pd.DataFrame] = []
                for scenario_index, scenario in enumerate(scenarios):
                    perturbed = apply_modality_perturbation(
                        data.modality_train,
                        data.modality_calibration,
                        study=study,
                        scenario=scenario,
                        seed=seed,
                        clinical=data.clinical_calibration,
                    )  # type: ignore[arg-type]
                    raw = (
                        clean_raw
                        if scenario == "clean"
                        else system.predict(perturbed, seed * 100 + scenario_index)
                    )
                    ranked = (
                        clean.copy() if scenario == "clean" else _rank_reliability(raw, clean_raw)
                    )
                    for model in ("B2", "B3", "B4", "B5", "B6", "M0"):
                        score_column, risk_column = (
                            f"{model.lower()}_score",
                            f"{model.lower()}_risk",
                        )
                        if score_column in ranked:
                            metric_rows.append(
                                _metric(
                                    data,
                                    seed=seed,
                                    scenario=scenario,
                                    model=model,
                                    risk_score=ranked[score_column].to_numpy(),
                                    risk_horizon=ranked[risk_column].to_numpy(),
                                    horizon=horizon,
                                    survival_floor=survival_floor,
                                )
                            )
                    for variant in GATE_VARIANTS:
                        clinical_score, modality_score = ablated_unreliability(
                            ranked, variant, learned
                        )
                        for coverage in coverages:
                            label = _profile_label(coverage)
                            clinical_threshold, modality_threshold = thresholds[(variant, label)]
                            actions, reasons = assign_actions(
                                clinical_score,
                                modality_score,
                                ranked["modality_missing"].to_numpy(dtype=bool),
                                clinical_threshold=clinical_threshold,
                                modality_threshold=modality_threshold,
                            )
                            final = gated_risk(
                                ranked["b2_risk"].to_numpy(), ranked["b6_risk"].to_numpy(), actions
                            )
                            metric_rows.append(
                                _metric(
                                    data,
                                    seed=seed,
                                    scenario=scenario,
                                    model="B7",
                                    risk_score=final,
                                    risk_horizon=final,
                                    horizon=horizon,
                                    survival_floor=survival_floor,
                                    gate_variant=variant,
                                    profile=label,
                                    reference_predictions={
                                        "B2": (
                                            ranked["b2_score"].to_numpy(),
                                            ranked["b2_risk"].to_numpy(),
                                        ),
                                        "B6": (
                                            ranked["b6_score"].to_numpy(),
                                            ranked["b6_risk"].to_numpy(),
                                        ),
                                    },
                                )
                            )
                            counts = pd.Series(actions).value_counts()
                            for action in ("AUGMENT", "FALLBACK", "ABSTAIN"):
                                action_rows.append(
                                    {
                                        "study": study,
                                        "seed": seed,
                                        "scenario": scenario,
                                        "gate_variant": variant,
                                        "profile": label,
                                        "action": action,
                                        "count": int(counts.get(action, 0)),
                                        "rate": float(counts.get(action, 0) / len(actions)),
                                        "non_abstention_coverage": float(
                                            np.mean(actions != "ABSTAIN")
                                        ),
                                    }
                                )
                            if variant == "full_equal_weight" and label == "90":
                                (
                                    ranked["primary_action"],
                                    ranked["primary_reason"],
                                    ranked["primary_risk"],
                                ) = actions, reasons, final
                                if scenario == "clean":
                                    subgroup_rows.extend(
                                        _subgroup_rows(
                                            data,
                                            ranked,
                                            actions,
                                            seed=seed,
                                            horizon=horizon,
                                            survival_floor=survival_floor,
                                            minimum_n=int(phase5_config["subgroups"]["minimum_n"]),
                                            minimum_events=int(
                                                phase5_config["subgroups"]["minimum_events"]
                                            ),
                                        )
                                    )
                    detection_rows.append(
                        {
                            "study": study,
                            "seed": seed,
                            "scenario": scenario,
                            "mean_clinical_unreliability": float(
                                ranked["clinical_unreliability"].mean()
                            ),
                            "mean_modality_unreliability": float(
                                ranked["modality_unreliability"].mean()
                            ),
                            "median_modality_ood_rank": float(ranked["modality_ood_rank"].median()),
                            "mean_modality_missingness": float(
                                ranked["modality_missingness"].mean()
                            ),
                            "mean_perturbation_sensitivity_rank": float(
                                ranked["rank_perturbation_sensitivity"].mean()
                            ),
                        }
                    )
                    trace = ranked.copy()
                    for name, values in reversed(
                        [
                            ("study", [study] * len(trace)),
                            ("seed", [seed] * len(trace)),
                            ("scenario", [scenario] * len(trace)),
                            ("patient_id", data.calibration_ids),
                            ("event", data.calibration_event.astype(int)),
                            ("duration_days", data.calibration_time),
                        ]
                    ):
                        trace.insert(0, name, values)
                    traces.append(trace)
                pd.concat(traces, ignore_index=True).to_csv(
                    prediction_root / f"{study.lower().replace('-', '_')}_seed{seed}_stress.csv",
                    index=False,
                )
                representation_rows.extend(
                    _representation_sensitivity(data, config, seed, horizon, survival_floor)
                )
                status_rows.append(
                    {"study": study, "seed": seed, "status": "complete", "reason": ""}
                )
            except Exception as exc:
                status_rows.append(
                    {"study": study, "seed": seed, "status": "failed", "reason": str(exc)}
                )

    frames = {
        "stress_metrics": pd.DataFrame(metric_rows),
        "action_summary": pd.DataFrame(action_rows),
        "detection_summary": pd.DataFrame(detection_rows),
        "subgroup_metrics": pd.DataFrame(subgroup_rows),
        "representation_metrics": pd.DataFrame(representation_rows),
        "learned_gate_weights": pd.DataFrame(weight_rows),
        "model_status": pd.DataFrame(status_rows),
    }
    if not frames["subgroup_metrics"].empty:
        subgroup = frames["subgroup_metrics"]
        frames["worst_group_summary"] = (
            subgroup.groupby(["study", "seed", "subgroup_variable", "model"], as_index=False)
            .agg(
                worst_ipcw_brier=("ipcw_brier", "max"),
                best_ipcw_brier=("ipcw_brier", "min"),
                worst_group_coverage=("coverage", "min"),
            )
            .assign(brier_range=lambda x: x["worst_ipcw_brier"] - x["best_ipcw_brier"])
        )
        keys = ["study", "seed", "subgroup_variable", "subgroup"]
        reference = subgroup.loc[subgroup["model"].eq("B2"), [*keys, "ipcw_brier"]].rename(
            columns={"ipcw_brier": "b2_ipcw_brier"}
        )
        primary = subgroup.loc[
            subgroup["model"].eq("B7_full_equal_weight_90"),
            [*keys, "parent_n", "coverage", "ipcw_brier"],
        ].rename(columns={"ipcw_brier": "b7_ipcw_brier"})
        regret = primary.merge(reference, on=keys, how="inner")
        regret["brier_regret_vs_b2"] = regret["b7_ipcw_brier"] - regret["b2_ipcw_brier"]
        regret["flag_threshold"] = float(
            phase5_config["acceptance_margins"]["worst_group_brier_regret_vs_b2_exploratory"]
        )
        regret["flagged"] = regret["brier_regret_vs_b2"] > regret["flag_threshold"]
        frames["worst_group_regret"] = regret.sort_values(
            ["study", "seed", "subgroup_variable", "brier_regret_vs_b2"],
            ascending=[True, True, True, False],
        )
    else:
        frames["worst_group_summary"] = pd.DataFrame()
        frames["worst_group_regret"] = pd.DataFrame()
    if frames["stress_metrics"].empty or frames["action_summary"].empty:
        frames["acceptance_checks"] = pd.DataFrame(
            columns=["study", "check", "value", "criterion", "passed"]
        )
    else:
        frames["acceptance_checks"] = _acceptance_checks(
            frames["stress_metrics"],
            frames["action_summary"],
            phase5_config["acceptance_margins"],
            len(selected_seeds),
        )

    outputs: list[Path] = []
    for name, frame in frames.items():
        path = metrics_root / f"{name}.csv"
        frame.to_csv(path, index=False)
        outputs.append(path)
    if not frames["stress_metrics"].empty:
        stress_figure = figure_root / "stress_brier.svg"
        _plot_stress(frames["stress_metrics"], stress_figure)
        outputs.append(stress_figure)
    if not frames["action_summary"].empty:
        action_figure = figure_root / "stress_actions.svg"
        _plot_actions(frames["action_summary"], action_figure)
        outputs.append(action_figure)

    successful = int(frames["model_status"]["status"].eq("complete").sum())
    failed = int(frames["model_status"]["status"].eq("failed").sum())
    blocked = int(frames["model_status"]["status"].eq("blocked").sum())
    audit_text = (
        "# Phase 5 leakage and sealed-outcome audit\n\n"
        f"- Successful study/seed runs: {successful}\n"
        f"- Failed runs: {failed}\n"
        f"- Blocked entries: {blocked}\n"
        "- Stress perturbations were applied to calibration predictors "
        "after training-only fitting.\n"
        "- Learned reliability weights used training OOF prediction errors only.\n"
        "- Calibration outcomes were used for evaluation, not threshold optimization.\n"
        "- RADCURE challenge-test, HANCOCK OOD-test, GSE65858, "
        "and GSE41613 outcomes were not loaded.\n"
        "- Patient-level stress traces remain in Git-ignored results/predictions/phase5/.\n"
        "- Intended tracked outputs are aggregate-only.\n"
    )
    audit_path = audit_root / "leakage_audit.md"
    audit_path.write_text(audit_text, encoding="utf-8")
    outputs.append(audit_path)
    sealed_manifest = _write_sealed_manifest(root) if write_freeze else None
    freeze_path = _write_freeze(root, sealed_manifest) if write_freeze and sealed_manifest else None
    if sealed_manifest is not None:
        outputs.append(sealed_manifest)
    if freeze_path is not None:
        outputs.append(freeze_path)
    _assert_aggregate_privacy(outputs)

    receipt = {
        "schema_version": "5.0",
        "generated_on": "2026-08-07",
        "phase": "Phase 5 development stress tests and analysis freeze",
        "studies": selected_studies,
        "seeds": selected_seeds,
        "bootstrap_ensemble_size": ensemble,
        "successful_runs": successful,
        "failed_runs": failed,
        "blocked_entries": blocked,
        "blocked_studies": frames["model_status"]
        .loc[frames["model_status"]["status"].eq("blocked"), "study"]
        .astype(str)
        .tolist(),
        "sealed_or_external_outcomes_used": False,
        "phase6_authorized": False,
        "analysis_frozen": bool(freeze_path),
        "patient_prediction_directory": prediction_root.relative_to(base).as_posix()
        + " (Git-ignored)",
        "config_sha256": {
            config_path.relative_to(root).as_posix(): _sha256(config_path),
            governance_path.relative_to(root).as_posix(): _sha256(governance_path),
        },
        "aggregate_output_sha256": {
            path.relative_to(base if path.is_relative_to(base) else root).as_posix(): _sha256(path)
            for path in outputs
            if path.is_file()
        },
    }
    receipt_path = base / "results" / "manifests" / "phase5_stress_freeze_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    receipt["receipt"] = receipt_path.relative_to(base).as_posix()
    return receipt
