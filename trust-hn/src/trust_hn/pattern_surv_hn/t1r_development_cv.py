"""Development nested cross-validation for the T1R transcriptome method port.

T1R is the faithful single-modality reduction of the V1R shrinkage-controlled residual
fusion: a fixed cross-fitted clinical anchor (elastic-net Cox on TCGA's seven clinical
variables) plus a nonlinear transcriptome residual head, with the residual shrinkage scale
selected inside each outer fold's inner CV.

Every learned transform is fold-bound; patient OOF output is git-ignored. This is a
post-hoc exploratory method-replication study (Phase 6 TCGA outcomes were already consumed),
so it is frozen and labelled as such and never overwrites Phase 6/7/8 output.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from torch import Tensor

from trust_hn.evaluation.phase3 import NumericMatrixPreprocessor
from trust_hn.pattern_surv_hn.hancock_contract import FoldBoundMixedPreprocessor
from trust_hn.pattern_surv_hn.t1r_model import (
    TrainableClinicalResidualTranscriptomeCox,
)
from trust_hn.pattern_surv_hn.transcriptome_contract import (
    ANCHOR_CATEGORICAL_FEATURES,
    ANCHOR_NUMERIC_FEATURES,
    TranscriptomeContract,
)
from trust_hn.pattern_surv_hn.v0_clinical_anchor import (
    CoxnetCandidate,
    PreparedFold,
    V0Spec,
    _event_stratified_splits,
    _fit_anchor,
    _predict_anchor,
    _select_candidate,
    evaluate_predictions,
    structured_survival,
)
from trust_hn.pattern_surv_hn.v1_development_cv import (
    _make_cox_loss_plan,
    _negative_breslow_cox_loss,
    breslow_risk_at_horizon,
)

ANALYSIS_DATE = "2026-09-07"
MODEL_ID = "T1R"
MODEL_NAME = "Clinical_Residual_Transcriptome_Cox_inner_selected_shrinkage"


@dataclass(frozen=True)
class T1RSpec:
    horizon_days: float
    outer_folds: int
    outer_repetition_seeds: tuple[int, ...]
    inner_folds: int
    top_k: int
    residual_hidden_dim: int
    anchor_alpha_grid: tuple[float, ...]
    anchor_l1_ratio_grid: tuple[float, ...]
    anchor_max_iter: int
    anchor_tolerance: float
    residual_penalty_grid: tuple[float, ...]
    checkpoint_steps: tuple[int, ...]
    residual_scale_grid: tuple[float, ...]
    learning_rate: float
    weight_decay: float
    gradient_clip_norm: float
    pattern_minimum_n: int
    pattern_minimum_events: int
    expected_n: int
    expected_events: int
    deterministic_algorithms: bool

    @classmethod
    def from_yaml(cls, path: Path) -> T1RSpec:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
        cross = payload["cross_fitting"]
        anchor = payload["anchor"]
        select = payload["inner_selection"]
        optim = payload["optimization"]
        support = payload["evaluation"]["pattern_metric_support"]
        population = payload["population"]
        spec = cls(
            float(payload["endpoint"]["horizon_days"]),
            int(cross["outer_folds"]),
            tuple(int(v) for v in cross["outer_repetition_seeds"]),
            int(cross["inner_folds"]),
            int(payload["modality"]["top_k"]),
            int(payload["modality"]["residual_hidden_dim"]),
            tuple(float(v) for v in anchor["alpha_grid"]),
            tuple(float(v) for v in anchor["l1_ratio_grid"]),
            int(anchor["max_iter"]),
            float(anchor["tolerance"]),
            tuple(float(v) for v in select["residual_penalty_grid"]),
            tuple(int(v) for v in select["checkpoint_steps"]),
            tuple(float(v) for v in select.get("residual_scale_grid", [1.0])),
            float(optim["learning_rate"]),
            float(optim["weight_decay"]),
            float(optim["gradient_clip_norm"]),
            int(support["minimum_n"]),
            int(support["minimum_events"]),
            int(population["expected_n"]),
            int(population["expected_events"]),
            bool(optim["deterministic_algorithms"]),
        )
        spec.validate()
        return spec

    @property
    def anchor_spec(self) -> V0Spec:
        return V0Spec(
            horizon_days=self.horizon_days,
            outer_folds=self.outer_folds,
            outer_repetition_seeds=self.outer_repetition_seeds,
            inner_folds=self.inner_folds,
            alpha_grid=self.anchor_alpha_grid,
            l1_ratio_grid=self.anchor_l1_ratio_grid,
            max_iter=self.anchor_max_iter,
            tolerance=self.anchor_tolerance,
            pattern_minimum_n=self.pattern_minimum_n,
            pattern_minimum_events=self.pattern_minimum_events,
        )

    def validate(self) -> None:
        if self.horizon_days <= 0 or self.outer_folds < 2 or self.inner_folds < 2:
            raise ValueError("invalid T1R horizon/fold specification")
        if not self.outer_repetition_seeds:
            raise ValueError("T1R requires outer repetition seeds")
        if self.top_k < 1 or self.residual_hidden_dim < 1:
            raise ValueError("T1R requires positive top_k and residual_hidden_dim")
        if not self.anchor_alpha_grid or any(v <= 0 for v in self.anchor_alpha_grid):
            raise ValueError("anchor alpha_grid must contain positive values")
        if not self.anchor_l1_ratio_grid or any(
            not 0 < v <= 1 for v in self.anchor_l1_ratio_grid
        ):
            raise ValueError("anchor l1_ratio_grid values must be in (0, 1]")
        if any(v < 0 for v in self.residual_penalty_grid):
            raise ValueError("residual penalties must be nonnegative")
        if not self.checkpoint_steps or self.checkpoint_steps[0] != 0:
            raise ValueError("checkpoint_steps must start at zero")
        if tuple(sorted(set(self.checkpoint_steps))) != self.checkpoint_steps:
            raise ValueError("checkpoint_steps must be unique and increasing")
        if not self.residual_scale_grid or any(
            scale <= 0 or scale > 1 for scale in self.residual_scale_grid
        ):
            raise ValueError("residual scales must be in (0, 1]")
        if self.learning_rate <= 0 or self.weight_decay < 0 or self.gradient_clip_norm <= 0:
            raise ValueError("invalid optimizer settings")


@dataclass(frozen=True)
class T1RFoldInputs:
    clinical_score: Tensor
    transcriptome: Tensor
    active: Tensor
    duration: Tensor
    event: Tensor


@dataclass(frozen=True)
class SelectedT1RCandidate:
    residual_penalty: float
    optimization_steps: int
    residual_scale: float = 1.0


@dataclass(frozen=True)
class FittedT1R:
    model: TrainableClinicalResidualTranscriptomeCox
    initial_cox_loss: float
    final_cox_loss: float
    final_total_loss: float


def _active_for(contract: TranscriptomeContract, ids: np.ndarray) -> np.ndarray:
    order = {
        native_id: bool(flag)
        for native_id, flag in zip(contract.native_ids, contract.active, strict=True)
    }
    return np.asarray([order[str(value)] for value in ids], dtype=bool)


def _to_tensor_inputs(
    clinical, transcriptome, active, duration, event
) -> T1RFoldInputs:
    return T1RFoldInputs(
        torch.as_tensor(clinical, dtype=torch.float64),
        torch.as_tensor(transcriptome, dtype=torch.float64),
        torch.as_tensor(active, dtype=torch.bool),
        torch.as_tensor(duration, dtype=torch.float64),
        torch.as_tensor(event, dtype=torch.bool),
    )


def _new_model(
    input_dim: int, hidden_dim: int, seed: int
) -> TrainableClinicalResidualTranscriptomeCox:
    model = TrainableClinicalResidualTranscriptomeCox(input_dim, hidden_dim, seed=seed)
    with torch.no_grad():
        model.residual_head[-1].weight.zero_()
        model.residual_head[-1].bias.zero_()
    return model


def _prepare_t1r_anchor_inner_folds(
    contract: TranscriptomeContract,
    ids: np.ndarray,
    event: np.ndarray,
    time: np.ndarray,
    anchor_spec: V0Spec,
    seed: int,
) -> tuple[PreparedFold, ...]:
    folds: list[PreparedFold] = []
    for train_idx, valid_idx in _event_stratified_splits(event, anchor_spec.inner_folds, seed):
        train_ids = ids[train_idx].tolist()
        valid_ids = ids[valid_idx].tolist()
        prep = FoldBoundMixedPreprocessor(
            numeric=ANCHOR_NUMERIC_FEATURES,
            categorical=ANCHOR_CATEGORICAL_FEATURES,
            allowed_fit_ids=set(train_ids),
        )
        train_block = prep.fit_transform(contract.anchor, train_ids)
        valid_block = prep.transform(contract.anchor, valid_ids)
        folds.append(
            PreparedFold(
                x_train=train_block.values,
                y_train=structured_survival(event[train_idx], time[train_idx]),
                x_valid=valid_block.values,
                y_valid=structured_survival(event[valid_idx], time[valid_idx]),
            )
        )
    return tuple(folds)


def _select_anchor(
    contract: TranscriptomeContract,
    ids: np.ndarray,
    event: np.ndarray,
    time: np.ndarray,
    anchor_spec: V0Spec,
    seed: int,
) -> CoxnetCandidate:
    prepared = _prepare_t1r_anchor_inner_folds(contract, ids, event, time, anchor_spec, seed)
    selected, _ = _select_candidate(prepared, anchor_spec)
    return selected


def _fit_anchor_for_split(
    contract: TranscriptomeContract,
    train_ids: np.ndarray,
    valid_ids: np.ndarray,
    train_event: np.ndarray,
    train_time: np.ndarray,
    candidate: CoxnetCandidate,
    anchor_spec: V0Spec,
):
    prep = FoldBoundMixedPreprocessor(
        numeric=ANCHOR_NUMERIC_FEATURES,
        categorical=ANCHOR_CATEGORICAL_FEATURES,
        allowed_fit_ids=set(train_ids.tolist()),
    )
    train_block = prep.fit_transform(contract.anchor, train_ids.tolist())
    valid_block = prep.transform(contract.anchor, valid_ids.tolist())
    if tuple(prep.fit_ids_) != tuple(train_ids.tolist()):
        raise RuntimeError("clinical preprocessor fit-ID audit failed")
    y_train = structured_survival(train_event, train_time)
    fitted = _fit_anchor(
        train_block.values, y_train, candidate, anchor_spec, train_block.feature_names
    )
    train_score = np.asarray(fitted.model.predict(train_block.values), dtype=float)
    valid_score, valid_risk = _predict_anchor(fitted, valid_block.values, anchor_spec.horizon_days)
    return train_score, valid_score, valid_risk, {
        "clinical_fit_n": len(prep.fit_ids_),
        "clinical_encoded_feature_count": int(train_block.values.shape[1]),
    }


def _fit_modality_preprocessors(
    contract: TranscriptomeContract, train_ids: np.ndarray, valid_ids: np.ndarray, top_k: int
):
    train_frame = contract.modality.loc[list(train_ids.astype(str))]
    valid_frame = contract.modality.loc[list(valid_ids.astype(str))]
    prep = NumericMatrixPreprocessor(top_k=top_k)
    train_matrix = prep.fit_transform(train_frame)
    valid_matrix = prep.transform(valid_frame)
    if valid_matrix.shape[1] != top_k:
        raise RuntimeError(f"transcriptome top-k width differs from spec: {valid_matrix.shape[1]}")
    return train_matrix, valid_matrix, {
        "selected_gene_count": int(valid_matrix.shape[1]),
        "fit_n": len(train_ids),
    }


def _predict_model(model, inputs: T1RFoldInputs):
    model.eval()
    with torch.no_grad():
        forward = model(inputs.clinical_score, inputs.transcriptome, inputs.active)
    return forward.fused_score.numpy(), forward.residual_score.numpy()


def _fit_t1r(input_dim, hidden_dim, model_seed, inputs, spec, candidate) -> FittedT1R:
    model = _new_model(input_dim, hidden_dim, model_seed)
    plan = _make_cox_loss_plan(inputs.duration, inputs.event)
    with torch.no_grad():
        initial = model(inputs.clinical_score, inputs.transcriptome, inputs.active)
        initial_loss = float(_negative_breslow_cox_loss(initial.fused_score, plan))
    optimizer = torch.optim.Adam(
        model.parameters(), lr=spec.learning_rate, weight_decay=spec.weight_decay
    )
    final_total = initial_loss
    for _ in range(candidate.optimization_steps):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        forward = model(inputs.clinical_score, inputs.transcriptome, inputs.active)
        cox = _negative_breslow_cox_loss(forward.fused_score, plan)
        loss = cox + candidate.residual_penalty * torch.mean(forward.residual_score.square())
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), spec.gradient_clip_norm)
        optimizer.step()
        final_total = float(loss.detach())
    model.eval()
    with torch.no_grad():
        final = model(inputs.clinical_score, inputs.transcriptome, inputs.active)
        final_cox = float(_negative_breslow_cox_loss(final.fused_score, plan))
    return FittedT1R(model, initial_loss, final_cox, final_total)


def _inner_select_t1r(
    contract: TranscriptomeContract,
    train_ids: np.ndarray,
    outer_event: np.ndarray,
    outer_time: np.ndarray,
    anchor_candidate: CoxnetCandidate,
    anchor_spec: V0Spec,
    spec: T1RSpec,
    seed: int,
):
    values = defaultdict(list)
    max_steps = max(spec.checkpoint_steps)
    input_dim = spec.top_k
    hidden_dim = spec.residual_hidden_dim
    for train_idx, valid_idx in _event_stratified_splits(
        outer_event, spec.inner_folds, seed
    ):
        inner_train_ids = train_ids[train_idx]
        inner_valid_ids = train_ids[valid_idx]
        train_event = outer_event[train_idx]
        valid_event = outer_event[valid_idx]
        train_time = outer_time[train_idx]
        valid_time = outer_time[valid_idx]
        train_clinical, valid_clinical, _, _ = _fit_anchor_for_split(
            contract, inner_train_ids, inner_valid_ids, train_event, train_time,
            anchor_candidate, anchor_spec,
        )
        train_transcriptome, valid_transcriptome, _ = _fit_modality_preprocessors(
            contract, inner_train_ids, inner_valid_ids, spec.top_k
        )
        train_inputs = _to_tensor_inputs(
            train_clinical, train_transcriptome, _active_for(contract, inner_train_ids),
            train_time, train_event,
        )
        valid_inputs = _to_tensor_inputs(
            valid_clinical, valid_transcriptome, _active_for(contract, inner_valid_ids),
            valid_time, valid_event,
        )
        train_y = structured_survival(train_event, train_time)
        valid_y = structured_survival(valid_event, valid_time)
        plan = _make_cox_loss_plan(train_inputs.duration, train_inputs.event)
        for penalty in spec.residual_penalty_grid:
            model = _new_model(input_dim, hidden_dim, seed)
            optimizer = torch.optim.Adam(
                model.parameters(), lr=spec.learning_rate, weight_decay=spec.weight_decay
            )
            checkpoints = set(spec.checkpoint_steps)
            for step in range(max_steps + 1):
                if step in checkpoints:
                    train_score, train_residual = _predict_model(model, train_inputs)
                    valid_score, valid_residual = _predict_model(model, valid_inputs)
                    train_clinical_score = train_score - train_residual
                    valid_clinical_score = valid_score - valid_residual
                    for residual_scale in spec.residual_scale_grid:
                        if residual_scale == 1.0:
                            scaled_train_score = train_score
                            scaled_valid_score = valid_score
                        else:
                            scaled_train_score = (
                                train_clinical_score + residual_scale * train_residual
                            )
                            scaled_valid_score = (
                                valid_clinical_score + residual_scale * valid_residual
                            )
                        valid_risk = breslow_risk_at_horizon(
                            train_time, train_event, scaled_train_score, scaled_valid_score,
                            spec.horizon_days,
                        )
                        values[(penalty, step, residual_scale)].append(
                            evaluate_predictions(
                                train_y, valid_y, scaled_valid_score, valid_risk,
                                spec.horizon_days,
                            )
                        )
                if step == max_steps:
                    break
                model.train()
                optimizer.zero_grad(set_to_none=True)
                forward = model(
                    train_inputs.clinical_score, train_inputs.transcriptome,
                    train_inputs.active,
                )
                cox = _negative_breslow_cox_loss(forward.fused_score, plan)
                loss = cox + penalty * torch.mean(forward.residual_score.square())
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), spec.gradient_clip_norm)
                optimizer.step()

    rows = []
    for (penalty, steps, residual_scale), metrics in sorted(values.items()):
        brier = np.asarray([row["ipcw_brier_24m"] for row in metrics], float)
        uno = np.asarray([row["uno_c_24m"] for row in metrics], float)
        rows.append({
            "residual_penalty": float(penalty),
            "optimization_steps": float(steps),
            "residual_scale": float(residual_scale),
            "mean_inner_ipcw_brier_24m": float(np.mean(brier)),
            "mean_inner_uno_c_24m": (
                float(np.mean(uno[np.isfinite(uno)])) if np.isfinite(uno).any() else -math.inf
            ),
            "successful_inner_folds": float(len(metrics)),
        })
    valid_rows = [row for row in rows if row["successful_inner_folds"] == spec.inner_folds]
    if not valid_rows:
        raise RuntimeError("no T1R candidate completed all inner folds")
    winner = min(valid_rows, key=lambda row: (
        row["mean_inner_ipcw_brier_24m"], -row["mean_inner_uno_c_24m"],
        -row["residual_penalty"], row["residual_scale"], row["optimization_steps"],
    ))
    selected = SelectedT1RCandidate(
        float(winner["residual_penalty"]), int(winner["optimization_steps"]),
        float(winner["residual_scale"]),
    )
    return selected, rows


def _fallback_errors(model, inputs: T1RFoldInputs):
    model.eval()
    with torch.no_grad():
        result = model(
            inputs.clinical_score, inputs.transcriptome, torch.zeros_like(inputs.active)
        )
    return (
        float(torch.max(torch.abs(result.residual_score))),
        float(torch.max(torch.abs(result.fused_score - inputs.clinical_score))),
    )


def development_cross_fit(contract: TranscriptomeContract, spec: T1RSpec, *, verbose: bool = False):
    ids, event, time = contract.development_arrays()
    if len(ids) != spec.expected_n or int(event.sum()) != spec.expected_events:
        raise RuntimeError("development estimand differs from frozen T1R contract")
    anchor_spec = spec.anchor_spec
    input_dim = spec.top_k
    hidden_dim = spec.residual_hidden_dim
    rows, fold_audit = [], []
    selection_counter, anchor_counter = Counter(), Counter()
    parameter_count = _new_model(input_dim, hidden_dim, 0).parameter_count
    for repetition_seed in spec.outer_repetition_seeds:
        seen = []
        splits = _event_stratified_splits(event, spec.outer_folds, repetition_seed)
        for outer_fold, (train_idx, valid_idx) in enumerate(splits):
            train_ids, valid_ids = ids[train_idx], ids[valid_idx]
            inner_seed = repetition_seed * 100 + outer_fold + 1
            anchor_candidate = _select_anchor(
                contract, train_ids, event[train_idx], time[train_idx], anchor_spec, inner_seed
            )
            anchor_counter[(anchor_candidate.alpha, anchor_candidate.l1_ratio)] += 1
            selected, inner_rows = _inner_select_t1r(
                contract, train_ids, event[train_idx], time[train_idx],
                anchor_candidate, anchor_spec, spec, inner_seed,
            )
            selection_counter[(
                selected.residual_penalty, selected.optimization_steps, selected.residual_scale
            )] += 1
            train_clinical, valid_clinical, valid_anchor_risk, anchor_audit = (
                _fit_anchor_for_split(
                    contract, train_ids, valid_ids, event[train_idx], time[train_idx],
                    anchor_candidate, anchor_spec,
                )
            )
            train_transcriptome, valid_transcriptome, modality_audit = (
                _fit_modality_preprocessors(contract, train_ids, valid_ids, spec.top_k)
            )
            train_inputs = _to_tensor_inputs(
                train_clinical, train_transcriptome, _active_for(contract, train_ids),
                time[train_idx], event[train_idx],
            )
            valid_inputs = _to_tensor_inputs(
                valid_clinical, valid_transcriptome, _active_for(contract, valid_ids),
                time[valid_idx], event[valid_idx],
            )
            fitted = _fit_t1r(input_dim, hidden_dim, inner_seed, train_inputs, spec, selected)
            train_fused, train_residual = _predict_model(fitted.model, train_inputs)
            valid_fused, valid_residual = _predict_model(fitted.model, valid_inputs)
            if selected.residual_scale != 1.0:
                train_fused = (
                    train_fused - train_residual + selected.residual_scale * train_residual
                )
                valid_residual = selected.residual_scale * valid_residual
                valid_fused = valid_clinical + valid_residual
            valid_risk = breslow_risk_at_horizon(
                time[train_idx], event[train_idx], train_fused, valid_fused, spec.horizon_days
            )
            fallback_residual_error, fallback_fused_error = _fallback_errors(
                fitted.model, valid_inputs
            )
            y_train = structured_survival(event[train_idx], time[train_idx])
            y_valid = structured_survival(event[valid_idx], time[valid_idx])
            fold_v0 = evaluate_predictions(
                y_train, y_valid, valid_clinical, valid_anchor_risk, spec.horizon_days
            )
            fold_v1 = evaluate_predictions(
                y_train, y_valid, valid_fused, valid_risk, spec.horizon_days
            )
            best_inner = next(
                row for row in inner_rows
                if row["residual_penalty"] == selected.residual_penalty
                and int(row["optimization_steps"]) == selected.optimization_steps
                and row["residual_scale"] == selected.residual_scale
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
                **(
                    {"selected_residual_scale": selected.residual_scale}
                    if spec.residual_scale_grid != (1.0,) else {}
                ),
                "selected_inner_ipcw_brier_24m": best_inner["mean_inner_ipcw_brier_24m"],
                "selected_inner_uno_c_24m": best_inner["mean_inner_uno_c_24m"],
                "initial_training_cox_loss": fitted.initial_cox_loss,
                "final_training_cox_loss": fitted.final_cox_loss,
                "fallback_residual_max_abs_error": fallback_residual_error,
                "fallback_fused_max_abs_error": fallback_fused_error,
                "clinical_preprocessing": anchor_audit,
                "modality_preprocessing": modality_audit,
                "V0_metrics": fold_v0, "T1R_metrics": fold_v1,
            })
            for local, global_index in enumerate(valid_idx):
                native_id = str(ids[global_index])
                seen.append(native_id)
                rows.append({
                    "native_id": native_id, "repetition_seed": repetition_seed,
                    "outer_fold": outer_fold, "duration_days": float(time[global_index]),
                    "event": int(event[global_index]),
                    "transcriptome_active": int(contract.active[global_index]),
                    "v0_risk_score": float(valid_clinical[local]),
                    "v0_risk_24m": float(valid_anchor_risk[local]),
                    "t1r_residual_score": float(valid_residual[local]),
                    "t1r_risk_score": float(valid_fused[local]),
                    "t1r_risk_24m": float(valid_risk[local]),
                    "t1r_survival_24m": float(1.0 - valid_risk[local]),
                    "selected_residual_penalty": selected.residual_penalty,
                    "selected_optimization_steps": selected.optimization_steps,
                    **(
                        {"selected_residual_scale": selected.residual_scale}
                        if spec.residual_scale_grid != (1.0,) else {}
                    ),
                })
            if verbose:
                print(
                    f"seed={repetition_seed} fold={outer_fold} "
                    f"penalty={selected.residual_penalty:g} "
                    f"steps={selected.optimization_steps} "
                    f"scale={selected.residual_scale:g}",
                    flush=True,
                )
        if len(seen) != len(ids) or len(seen) != len(set(seen)) or set(seen) != set(ids):
            raise RuntimeError(f"T1R OOF coverage failed for seed {repetition_seed}")

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
            full_y, full_y, aligned["t1r_risk_score"].to_numpy(float),
            aligned["t1r_risk_24m"].to_numpy(float), spec.horizon_days,
        )
        metric_names = (
            "ipcw_brier_24m", "harrell_c", "uno_c_24m", "auc_24m",
            "calibration_in_the_large_24m", "calibration_slope_24m",
            "mean_predicted_risk_24m",
        )
        deltas = {key: float(v1_metrics[key] - v0_metrics[key]) for key in metric_names}
        per_seed.append({
            "repetition_seed": int(repetition_seed), "V0": v0_metrics,
            "T1R": v1_metrics, "delta_T1R_minus_V0": deltas,
        })
        for pattern, pattern_group in aligned.groupby("transcriptome_active", sort=True):
            label = "transcriptome_present" if int(pattern) else "transcriptome_absent"
            indices = np.asarray([id_to_index[str(v)] for v in pattern_group.index])
            n, events = len(pattern_group), int(event[indices].sum())
            supported = n >= spec.pattern_minimum_n and events >= spec.pattern_minimum_events
            record = {
                "repetition_seed": int(repetition_seed), "acquisition_pattern": label,
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
                    full_y, pattern_y, pattern_group["t1r_risk_score"].to_numpy(float),
                    pattern_group["t1r_risk_24m"].to_numpy(float), spec.horizon_days,
                )
                record.update({
                    "V0": v0_pattern, "T1R": v1_pattern,
                    "delta_T1R_minus_V0": {
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
        v1_values = np.asarray([row["T1R"][metric] for row in per_seed], float)
        delta = v1_values - v0_values
        summary[metric] = {
            "V0_mean": float(np.nanmean(v0_values)),
            "T1R_mean": float(np.nanmean(v1_values)),
            "mean_delta_T1R_minus_V0": float(np.nanmean(delta)),
            "delta_sample_sd": (
                float(np.nanstd(delta, ddof=1)) if np.isfinite(delta).sum() > 1 else 0.0
            ),
            "T1R_better_seed_count": int(
                np.sum(delta < 0) if metric == "ipcw_brier_24m" else np.sum(delta > 0)
            ),
        }
    aggregate = {
        "folds": fold_audit, "per_seed_metrics": per_seed,
        "across_seed_summary": summary, "pattern_stratified_metrics": pattern_rows,
        "t1r_selection_frequency": [
            {
                "residual_penalty": penalty,
                "optimization_steps": steps,
                **({"residual_scale": scale} if spec.residual_scale_grid != (1.0,) else {}),
                "outer_fold_count": count,
            }
            for (penalty, steps, scale), count in sorted(selection_counter.items())
        ],
        "anchor_selection_frequency": [
            {"alpha": alpha, "l1_ratio": ratio, "outer_fold_count": count}
            for (alpha, ratio), count in sorted(anchor_counter.items())
        ],
        "parameter_count": parameter_count,
    }
    return oof, aggregate


def apply_t1r_gate(oof, aggregate, gate_payload):
    per_seed = aggregate["per_seed_metrics"]
    patterns, folds = aggregate["pattern_stratified_metrics"], aggregate["folds"]
    expected_rows = oof["native_id"].nunique() * len(per_seed)
    finite_v0 = np.isfinite(oof[["v0_risk_score", "v0_risk_24m"]]).all(axis=1)
    finite_v1 = np.isfinite(oof[["t1r_risk_score", "t1r_risk_24m"]]).all(axis=1)
    v0_coverage = float(finite_v0.sum() / expected_rows)
    v1_coverage = float(finite_v1.sum() / expected_rows)
    coverage_spec = gate_payload["coverage_gate"]
    coverage_pass = (
        v0_coverage == float(coverage_spec["required_V0_coverage"])
        and v1_coverage == float(coverage_spec["required_T1R_coverage"])
    )
    max_residual_error = max(float(row["fallback_residual_max_abs_error"]) for row in folds)
    max_fused_error = max(float(row["fallback_fused_max_abs_error"]) for row in folds)
    structural_spec = gate_payload["structural_gate"]
    structural_pass = (
        max_residual_error <= float(structural_spec["exact_absent_residual_max_abs_error"])
        and max_fused_error <= float(structural_spec["exact_clinical_fallback_max_abs_error"])
        and int(aggregate["parameter_count"]) <= int(structural_spec["parameter_ceiling"])
    )
    brier_deltas = np.asarray([
        row["delta_T1R_minus_V0"]["ipcw_brier_24m"] for row in per_seed
    ], float)
    uno_deltas = np.asarray([
        row["delta_T1R_minus_V0"]["uno_c_24m"] for row in per_seed
    ], float)
    v0_citl = np.asarray([row["V0"]["calibration_in_the_large_24m"] for row in per_seed], float)
    v1_citl = np.asarray([row["T1R"]["calibration_in_the_large_24m"] for row in per_seed], float)
    v0_slope = np.asarray([row["V0"]["calibration_slope_24m"] for row in per_seed], float)
    v1_slope = np.asarray([row["T1R"]["calibration_slope_24m"] for row in per_seed], float)
    citl_deterioration = float(np.nanmean(np.abs(v1_citl)) - np.nanmean(np.abs(v0_citl)))
    slope_deterioration = float(
        np.nanmean(np.abs(v1_slope - 1.0)) - np.nanmean(np.abs(v0_slope - 1.0))
    )
    supported_regrets = [
        float(row["delta_T1R_minus_V0"]["ipcw_brier_24m"])
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
        "decision": "T1R_EARNS_COMPLEXITY" if earns else "T1R_DOES_NOT_EARN_COMPLEXITY",
        "coverage": {"V0": v0_coverage, "T1R": v1_coverage, "pass": coverage_pass},
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
