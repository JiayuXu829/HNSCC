"""Transcriptome ecosystem contract for the T1R method port.

T1R ports V1R's shrinkage-controlled residual structure to a single dense transcriptome
modality. This module assembles the fixed clinical anchor and the gene-rank transcriptome
matrix from the frozen Phase 6 loaders and exposes them in a row-aligned form for the
development cross-validation in :mod:`trust_hn.pattern_surv_hn.t1r_development_cv`.

The anchor uses TCGA's seven clinical variables (numeric ``age``; categorical ``sex, site,
stage, hpv, treatment, smoking``), exactly the columns the frozen Phase 6 transcriptome
cohorts already expose. The transcriptome modality is the within-sample gene rank over the
TCGA/GEO common-gene intersection, already materialised by the Phase 6 rank cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from trust_hn.data.phase6_data import load_geo_features, load_phase6_development_data

ANCHOR_NUMERIC_FEATURES: tuple[str, ...] = ("age",)
ANCHOR_CATEGORICAL_FEATURES: tuple[str, ...] = (
    "sex",
    "site",
    "stage",
    "hpv",
    "treatment",
    "smoking",
)
ANCHOR_FEATURES: tuple[str, ...] = ANCHOR_NUMERIC_FEATURES + ANCHOR_CATEGORICAL_FEATURES


@dataclass(frozen=True)
class TranscriptomeContract:
    """Row-aligned clinical anchor plus gene-rank transcriptome for one cohort.

    ``anchor`` and ``modality`` are indexed by ``native_id``. ``event``/``time`` are present
    only for the development cohort (outcomes are exposed there); for external cohorts the
    outcomes are loaded separately behind Phase 6 governance and are never held here.
    """

    ids: np.ndarray
    event: np.ndarray | None
    time: np.ndarray | None
    anchor: pd.DataFrame
    modality: pd.DataFrame
    active: np.ndarray
    cohort: str
    role: str

    def __post_init__(self) -> None:
        n = len(self.ids)
        if self.ids.ndim != 1 or len(set(self.ids.astype(str))) != n:
            raise ValueError("transcriptome contract IDs must be unique")
        for name, frame in (("anchor", self.anchor), ("modality", self.modality)):
            if len(frame) != n:
                raise ValueError(f"{name} row count differs from contract IDs")
            if tuple(frame.index.astype(str)) != tuple(self.ids.astype(str)):
                raise ValueError(f"{name} index order differs from contract IDs")
        if self.active.shape != (n,):
            raise ValueError("active flag must align with contract IDs")
        if self.modality.shape[1] < 1:
            raise ValueError("transcriptome modality has no genes")
        missing = [column for column in ANCHOR_FEATURES if column not in self.anchor.columns]
        if missing:
            raise ValueError(f"anchor missing required columns: {missing}")
        if self.event is not None and self.event.shape != (n,):
            raise ValueError("event vector length differs from contract IDs")
        if self.time is not None and self.time.shape != (n,):
            raise ValueError("time vector length differs from contract IDs")

    @property
    def native_ids(self) -> np.ndarray:
        return self.ids.astype(str)

    @property
    def gene_count(self) -> int:
        return int(self.modality.shape[1])

    @property
    def n(self) -> int:
        return len(self.ids)

    def development_arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.event is None or self.time is None:
            raise ValueError("development outcomes are not present on this contract")
        return self.native_ids, self.event.astype(bool), self.time.astype(float)

    @classmethod
    def from_development(cls, project_root: Path) -> TranscriptomeContract:
        root = Path(project_root)
        data = load_phase6_development_data(root, "TCGA-HNSC")
        if data.modality is None:
            raise ValueError(data.modality_blocker or "TCGA transcriptome is unavailable")
        ids = data.ids.astype(str)
        event = np.concatenate([data.train_event, data.calibration_event]).astype(bool)
        time = np.concatenate([data.train_time, data.calibration_time]).astype(float)
        anchor = data.clinical.copy().set_index(pd.Index(ids, name="native_id"))
        modality = data.modality.copy().set_index(pd.Index(ids, name="native_id"))
        active = (~modality.isna().all(axis=1)).to_numpy(dtype=bool)
        return cls(ids, event, time, anchor, modality, active, "TCGA-HNSC", "development")

    @classmethod
    def from_external(cls, project_root: Path, cohort: str) -> TranscriptomeContract:
        root = Path(project_root)
        features = load_geo_features(root, cohort)
        ids = features.ids.astype(str)
        anchor = features.clinical.copy().set_index(pd.Index(ids, name="native_id"))
        modality = features.modality.copy().set_index(pd.Index(ids, name="native_id"))
        active = (~modality.isna().all(axis=1)).to_numpy(dtype=bool)
        return cls(ids, None, None, anchor, modality, active, features.cohort, features.role)
