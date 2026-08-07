"""Governance-safe Phase 3 development feature loaders.

Only rows explicitly marked eligible, endpoint-usable, and assigned to the frozen
train/calibration partitions are materialized. Sealed and external rows never enter
returned modeling arrays.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StudyData:
    study: str
    train_ids: np.ndarray
    calibration_ids: np.ndarray
    train_event: np.ndarray
    train_time: np.ndarray
    calibration_event: np.ndarray
    calibration_time: np.ndarray
    split_roles: tuple[str, ...]
    clinical: pd.DataFrame
    modality: pd.DataFrame | None
    modality_blocker: str | None = None

    @property
    def ids(self) -> np.ndarray:
        return np.concatenate([self.train_ids, self.calibration_ids])

    @property
    def n_train(self) -> int:
        return len(self.train_ids)

    @property
    def clinical_train(self) -> pd.DataFrame:
        return self.clinical.iloc[: self.n_train].reset_index(drop=True)

    @property
    def clinical_calibration(self) -> pd.DataFrame:
        return self.clinical.iloc[self.n_train :].reset_index(drop=True)

    @property
    def modality_train(self) -> pd.DataFrame | None:
        if self.modality is None:
            return None
        return self.modality.iloc[: self.n_train].reset_index(drop=True)

    @property
    def modality_calibration(self) -> pd.DataFrame | None:
        if self.modality is None:
            return None
        return self.modality.iloc[self.n_train :].reset_index(drop=True)


def _read_phase2_records(root: Path, slug: str) -> pd.DataFrame:
    path = root / "data" / "interim" / "phase2" / slug / "adapter_records.csv"
    frame = pd.read_csv(path, dtype={"native_id": "string"})
    eligible = frame["eligible"].astype(str).str.casefold().eq("true")
    usable = frame["endpoint_status"].astype(str).eq("usable")
    development = frame["split_role"].isin(["train", "calibration"])
    selected = frame.loc[eligible & usable & development].copy()
    selected["native_id"] = selected["native_id"].astype("string").str.strip()
    selected["event"] = pd.to_numeric(selected["event"], errors="raise").astype(bool)
    selected["duration_days"] = pd.to_numeric(selected["duration_days"], errors="raise")
    if selected["native_id"].duplicated().any():
        raise ValueError(f"duplicate development IDs in {path}")
    return selected


def _partition_records(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = (
        frame.loc[frame["split_role"].eq("train")].sort_values("native_id").reset_index(drop=True)
    )
    calibration = (
        frame.loc[frame["split_role"].eq("calibration")]
        .sort_values("native_id")
        .reset_index(drop=True)
    )
    if train.empty or calibration.empty:
        raise ValueError("both frozen train and calibration partitions are required")
    return train, calibration


def _base_clinical(rows: pd.DataFrame) -> pd.DataFrame:
    columns = ["age", "sex", "site", "stage", "hpv", "treatment", "smoking"]
    return rows.reindex(columns=columns).reset_index(drop=True)


def _ordered_join(ids: list[str], frames: list[pd.DataFrame]) -> pd.DataFrame:
    merged = pd.DataFrame(index=pd.Index(ids, name="patient_id"))
    for frame in frames:
        local = frame.copy()
        local.index = local.index.astype(str).str.strip()
        if local.index.duplicated().any():
            raise ValueError("duplicate patient IDs in feature source")
        overlap = set(merged.columns) & set(local.columns)
        if overlap:
            local = local.rename(columns={column: f"{column}__source" for column in overlap})
        merged = merged.join(local, how="left")
    return merged.reset_index(drop=True)


def _load_radcure(root: Path, rows: pd.DataFrame) -> tuple[pd.DataFrame, None, str]:
    source = (
        root
        / "data/interim/radcure/v04_20241219/clinical_csv/01_RADCURE_TCIA_Clinical_r2_offset.csv"
    )
    raw = pd.read_csv(source, dtype={"patient_id": "string"}).set_index("patient_id")
    ids = rows["native_id"].astype(str).tolist()
    selected = raw.reindex(ids)
    clinical = pd.DataFrame(
        {
            "age": pd.to_numeric(selected["Age"], errors="coerce"),
            "sex": selected["Sex"],
            "site": selected["Ds Site"],
            "subsite": selected["Subsite"],
            "stage": selected["Stage"],
            "t_stage": selected["T"],
            "n_stage": selected["N"],
            "m_stage": selected["M "],
            "hpv": selected["HPV"],
            "treatment": selected["Tx Modality"],
            "smoking": selected["Smoking Status"],
            "ecog": selected["ECOG PS"],
            "smoking_pack_years": pd.to_numeric(selected["Smoking PY"], errors="coerce"),
            "dose": pd.to_numeric(selected["Dose"], errors="coerce"),
            "fractions": pd.to_numeric(selected["Fx"], errors="coerce"),
            "contrast_enhanced": pd.to_numeric(selected["ContrastEnhanced"], errors="coerce"),
        }
    ).reset_index(drop=True)
    blocker = "ORCESTRA RDS structure not validated; radiomics modality remains unavailable"
    return clinical, None, blocker


def _load_hancock(root: Path, rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, None]:
    feature_root = next((root / "data/interim/hancock").rglob("features/clinical.csv")).parent
    ids = rows["native_id"].astype(str).tolist()

    def read(name: str) -> pd.DataFrame:
        frame = pd.read_csv(feature_root / name, dtype={"patient_id": "string"})
        frame["patient_id"] = frame["patient_id"].str.strip().str.zfill(3)
        return frame.set_index("patient_id")

    clinical_raw = read("clinical.csv")
    pathological = read("pathological.csv")
    blood = read("blood.csv")
    tma = read("tma_cell_density.csv")
    clinical = _ordered_join(ids, [clinical_raw, pathological])
    modality = _ordered_join(ids, [blood, tma])
    return clinical, modality, None


def _tcga_expression_cache(root: Path) -> Path:
    return root / "data/interim/phase3/tcga_hnsc/expression_protein_coding_log2_tpm.npz"


def _build_tcga_expression(root: Path, ids: list[str], cache: Path) -> pd.DataFrame:
    manifest_path = root / "data/raw/tcga_hnsc/gdc_star_counts_primary_tumor_manifest.tsv"
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        manifest = list(csv.DictReader(handle, delimiter="\t"))
    by_case: dict[str, dict[str, str]] = {}
    for row in manifest:
        for native_id in str(row["case_submitter_ids"]).split(";"):
            native_id = native_id.strip()
            if native_id in by_case:
                raise ValueError(f"multiple expression files found for {native_id}")
            by_case[native_id] = row

    matrices: list[np.ndarray] = []
    expected_features: np.ndarray | None = None
    raw_root = root / "data/raw/tcga_hnsc"
    for native_id in ids:
        row = by_case.get(native_id)
        if row is None:
            raise FileNotFoundError(f"no expression manifest row for {native_id}")
        path = raw_root / f"{row['file_id']}__{row['file_name']}"
        expression = pd.read_csv(
            path,
            sep="\t",
            comment="#",
            usecols=["gene_id", "gene_name", "gene_type", "tpm_unstranded"],
            dtype={"gene_id": "string", "gene_name": "string", "gene_type": "string"},
        )
        expression = expression.loc[expression["gene_type"].eq("protein_coding")].copy()
        features = (
            expression["gene_id"].str.replace(r"\.\d+$", "", regex=True)
            + "|"
            + expression["gene_name"].fillna("")
        ).to_numpy(dtype=str)
        if expected_features is None:
            expected_features = features
        elif not np.array_equal(expected_features, features):
            raise ValueError(f"gene order/content differs in {path.name}")
        values = pd.to_numeric(expression["tpm_unstranded"], errors="raise").to_numpy(
            dtype=np.float32
        )
        matrices.append(np.log2(values + np.float32(1.0)))
    if expected_features is None:
        raise ValueError("no TCGA expression files were loaded")
    matrix = np.vstack(matrices).astype(np.float32, copy=False)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, ids=np.asarray(ids), features=expected_features, values=matrix)
    return pd.DataFrame(matrix, columns=expected_features)


def _load_tcga_expression(root: Path, ids: list[str], build: bool) -> pd.DataFrame | None:
    cache = _tcga_expression_cache(root)
    if not cache.exists():
        if not build:
            return None
        return _build_tcga_expression(root, ids, cache)
    payload = np.load(cache, allow_pickle=False)
    cached_ids = payload["ids"].astype(str).tolist()
    if cached_ids != ids:
        if not build:
            return None
        return _build_tcga_expression(root, ids, cache)
    return pd.DataFrame(payload["values"], columns=payload["features"].astype(str))


def _load_tcga(
    root: Path, rows: pd.DataFrame, build_expression: bool
) -> tuple[pd.DataFrame, pd.DataFrame | None, str | None]:
    ids = rows["native_id"].astype(str).tolist()
    clinical = _base_clinical(rows)
    modality = _load_tcga_expression(root, ids, build_expression)
    blocker = (
        None
        if modality is not None
        else "TCGA expression cache not built; rerun with build_expression=True"
    )
    return clinical, modality, blocker


def load_phase3_study_data(
    project_root: Path, study: str, *, build_expression: bool = False
) -> StudyData:
    root = Path(project_root).resolve()
    normalized = study.strip().upper().replace("_", "-")
    aliases = {
        "TCGA-HNSC": ("TCGA-HNSC", "tcga_hnsc"),
        "RADCURE": ("RADCURE", "radcure"),
        "HANCOCK": ("HANCOCK", "hancock"),
    }
    if normalized not in aliases:
        raise ValueError(f"unsupported Phase 3 study: {study}")
    canonical, slug = aliases[normalized]
    records = _read_phase2_records(root, slug)
    train, calibration = _partition_records(records)
    ordered = pd.concat([train, calibration], ignore_index=True)

    if canonical == "RADCURE":
        clinical, modality, blocker = _load_radcure(root, ordered)
    elif canonical == "HANCOCK":
        clinical, modality, blocker = _load_hancock(root, ordered)
    else:
        clinical, modality, blocker = _load_tcga(root, ordered, build_expression)

    if len(clinical) != len(ordered) or (modality is not None and len(modality) != len(ordered)):
        raise ValueError(f"feature alignment failed for {canonical}")
    return StudyData(
        study=canonical,
        train_ids=train["native_id"].astype(str).to_numpy(),
        calibration_ids=calibration["native_id"].astype(str).to_numpy(),
        train_event=train["event"].to_numpy(dtype=bool),
        train_time=train["duration_days"].to_numpy(dtype=float),
        calibration_event=calibration["event"].to_numpy(dtype=bool),
        calibration_time=calibration["duration_days"].to_numpy(dtype=float),
        split_roles=tuple(ordered["split_role"].astype(str)),
        clinical=clinical,
        modality=modality,
        modality_blocker=blocker,
    )
