"""Outcome-free Phase 6 feature preparation and frozen cohort alignment.

This module intentionally does not expose any held-out outcome loader. Outcome
materialization lives in :mod:`trust_hn.evaluation.phase6` behind one-time
governance authorization.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from trust_hn.data.phase3_features import StudyData, _load_hancock, load_phase3_study_data

OUTCOME_FIELDS = frozenset(
    {
        "duration_days",
        "event",
        "os",
        "os_event",
        "fu time",
        "vital",
        "survival_status",
        "days_to_last_information",
        "status",
        "last fu",
        "date of death",
    }
)

COHORT_SPECS = {
    "RADCURE": ("radcure", "sealed_test", "RADCURE challenge test"),
    "HANCOCK": ("hancock", "sealed_test", "HANCOCK OOD test"),
    "GSE65858": ("gse65858", "external_test", "GSE65858 external test"),
    "GSE41613": ("gse41613", "sensitivity", "GSE41613 sensitivity"),
}


@dataclass(frozen=True)
class CohortFeatures:
    cohort: str
    role: str
    ids: np.ndarray
    clinical: pd.DataFrame
    modality: pd.DataFrame

    def __post_init__(self) -> None:
        n = len(self.ids)
        if len(self.clinical) != n or len(self.modality) != n:
            raise ValueError(f"feature alignment failed for {self.cohort}")
        if len(set(self.ids.astype(str))) != n:
            raise ValueError(f"duplicate patient IDs in {self.cohort}")
        forbidden = {str(column).casefold() for column in self.clinical.columns} & OUTCOME_FIELDS
        if forbidden:
            raise ValueError(f"outcome columns entered feature frame: {sorted(forbidden)}")


@dataclass(frozen=True)
class TranscriptomicCache:
    common_genes: np.ndarray
    tcga_ids: np.ndarray
    tcga_ranks: np.ndarray
    gse65858_ids: np.ndarray
    gse65858_ranks: np.ndarray
    gse41613_ids: np.ndarray
    gse41613_ranks: np.ndarray


def ordered_id_digest(ids: Iterable[str]) -> str:
    ordered = sorted(str(value).strip() for value in ids)
    return hashlib.sha256("\0".join(ordered).encode("utf-8")).hexdigest()


def frozen_rows(project_root: Path, cohort: str) -> pd.DataFrame:
    canonical = cohort.strip().upper().replace("_", "-")
    if canonical == "TCGA-HNSC":
        slug, role = "tcga_hnsc", None
    else:
        try:
            slug, role, _ = COHORT_SPECS[canonical]
        except KeyError as exc:
            raise ValueError(f"unsupported Phase 6 cohort: {cohort}") from exc
    path = Path(project_root) / "data" / "interim" / "phase2" / slug / "adapter_records.csv"
    feature_columns = [
        "native_id",
        "split_role",
        "eligible",
        "endpoint_status",
        "age",
        "sex",
        "site",
        "stage",
        "hpv",
        "treatment",
        "age_group",
        "smoking",
    ]
    frame = pd.read_csv(path, usecols=feature_columns, dtype={"native_id": "string"})
    eligible = frame["eligible"].astype(str).str.casefold().eq("true")
    if role is None:
        selected = frame.loc[eligible & frame["split_role"].isin(["train", "calibration"])]
    else:
        selected = frame.loc[eligible & frame["split_role"].eq(role)]
    selected = selected.copy()
    selected["native_id"] = selected["native_id"].astype("string").str.strip()
    selected = selected.sort_values("native_id").reset_index(drop=True)
    if selected["native_id"].duplicated().any():
        raise ValueError(f"duplicate frozen IDs in {path}")
    return selected


def verify_frozen_cohort_manifest(project_root: Path) -> list[dict[str, object]]:
    root = Path(project_root)
    manifest_path = root / "data/manifests/sealed/phase6_cohort_set_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {entry["cohort"]: entry for entry in payload["cohorts"]}
    results: list[dict[str, object]] = []
    for cohort, (_, role, manifest_name) in COHORT_SPECS.items():
        rows = frozen_rows(root, cohort)
        entry = expected[manifest_name]
        observed_n = len(rows)
        observed_digest = ordered_id_digest(rows["native_id"].astype(str))
        if observed_n != int(entry["patient_count"]):
            raise ValueError(f"frozen cohort count mismatch for {cohort}")
        if observed_digest != str(entry["ordered_id_set_sha256"]):
            raise ValueError(f"frozen cohort digest mismatch for {cohort}")
        results.append(
            {
                "cohort": cohort,
                "role": role,
                "patient_count": observed_n,
                "ordered_id_set_sha256": observed_digest,
            }
        )
    return results


def _radcure_clinical(project_root: Path, ids: list[str]) -> pd.DataFrame:
    path = Path(project_root) / (
        "data/interim/radcure/v04_20241219/clinical_csv/"
        "01_RADCURE_TCIA_Clinical_r2_offset.csv"
    )
    feature_columns = [
        "patient_id",
        "Age",
        "Sex",
        "Ds Site",
        "Subsite",
        "Stage",
        "T",
        "N",
        "M ",
        "HPV",
        "Tx Modality",
        "Smoking Status",
        "ECOG PS",
        "Smoking PY",
        "Dose",
        "Fx",
        "ContrastEnhanced",
    ]
    raw = pd.read_csv(path, usecols=feature_columns, dtype={"patient_id": "string"})
    raw["patient_id"] = raw["patient_id"].astype("string").str.strip()
    selected = raw.set_index("patient_id").reindex(ids)
    return pd.DataFrame(
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


def _aligned_npz_matrix(
    path: Path, ids: list[str], value_key: str, *, expected_features: np.ndarray | None = None
) -> pd.DataFrame:
    payload = np.load(path, allow_pickle=False)
    cached_ids = payload["ids"].astype(str)
    features = payload["features"].astype(str)
    if expected_features is not None and not np.array_equal(
        features, expected_features.astype(str)
    ):
        raise ValueError(f"feature order mismatch in {path}")
    values = np.asarray(payload[value_key], dtype=np.float32)
    if values.shape != (len(cached_ids), len(features)):
        raise ValueError(f"invalid matrix shape in {path}")
    positions = {value: index for index, value in enumerate(cached_ids)}
    aligned = np.full((len(ids), len(features)), np.nan, dtype=np.float32)
    for row_index, native_id in enumerate(ids):
        source_index = positions.get(native_id)
        if source_index is not None:
            aligned[row_index] = values[source_index]
    return pd.DataFrame(aligned, columns=features)


def load_radcure_features(
    project_root: Path, *, role: str = "sealed_test", assay: str = "original"
) -> CohortFeatures:
    allowed = {"train", "calibration", "sealed_test"}
    if role not in allowed:
        raise ValueError(f"unsupported RADCURE role: {role}")
    root = Path(project_root)
    source = root / "data/interim/phase2/radcure/adapter_records.csv"
    frame = pd.read_csv(
        source,
        usecols=["native_id", "split_role", "eligible", "endpoint_status"],
        dtype={"native_id": "string"},
    )
    selected = frame.loc[
        frame["eligible"].astype(str).str.casefold().eq("true") & frame["split_role"].eq(role)
    ].copy()
    selected["native_id"] = selected["native_id"].astype("string").str.strip()
    selected = selected.sort_values("native_id").reset_index(drop=True)
    ids = selected["native_id"].astype(str).tolist()
    clinical = _radcure_clinical(root, ids)
    cache = root / "data/processed/radcure/phase6_pyradiomics_features.npz"
    modality = _aligned_npz_matrix(cache, ids, assay)
    return CohortFeatures("RADCURE", role, np.asarray(ids), clinical, modality)


def load_hancock_features(project_root: Path, *, role: str = "sealed_test") -> CohortFeatures:
    if role not in {"train", "calibration", "sealed_test"}:
        raise ValueError(f"unsupported HANCOCK role: {role}")
    root = Path(project_root)
    source = root / "data/interim/phase2/hancock/adapter_records.csv"
    rows = pd.read_csv(
        source,
        usecols=["native_id", "split_role", "eligible", "endpoint_status"],
        dtype={"native_id": "string"},
    )
    rows = rows.loc[
        rows["eligible"].astype(str).str.casefold().eq("true") & rows["split_role"].eq(role)
    ].copy()
    rows["native_id"] = rows["native_id"].astype("string").str.strip()
    rows = rows.sort_values("native_id").reset_index(drop=True)
    clinical, modality, _ = _load_hancock(root, rows)
    return CohortFeatures(
        "HANCOCK", role, rows["native_id"].astype(str).to_numpy(), clinical, modality
    )


def _read_geo_table(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sample_ids: list[str] | None = None
    probes: list[str] = []
    rows: list[np.ndarray] = []
    in_table = False
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line in handle:
            if line.startswith("!series_matrix_table_begin"):
                header = next(csv.reader([next(handle).rstrip("\r\n")], delimiter="\t"))
                sample_ids = [value.strip('"') for value in header[1:]]
                in_table = True
                continue
            if line.startswith("!series_matrix_table_end"):
                break
            if not in_table:
                continue
            row = next(csv.reader([line.rstrip("\r\n")], delimiter="\t"))
            probes.append(row[0].strip('"'))
            values = np.asarray(
                [
                    float(value) if value not in {"", "null", "NA"} else np.nan
                    for value in row[1:]
                ],
                dtype=np.float32,
            )
            rows.append(values)
    if sample_ids is None or not rows:
        raise ValueError(f"GEO expression table not found: {path}")
    matrix = np.vstack(rows)
    if matrix.shape[1] != len(sample_ids):
        raise ValueError(f"GEO sample/expression mismatch: {path}")
    return np.asarray(probes), np.asarray(sample_ids), matrix


def _first_gene_symbol(value: object) -> str | None:
    text = "" if value is None or pd.isna(value) else str(value).strip()
    if not text or text.casefold() in {"na", "n/a", "null", "---"}:
        return None
    normalized = text.replace("///", ";").replace("//", ";").replace("|", ";")
    for part in normalized.split(";"):
        symbol = part.strip().upper()
        if symbol and symbol not in {"NA", "N/A", "NULL", "---"}:
            return symbol
    return None


def _platform_gene_map(path: Path) -> dict[str, str]:
    header_line = None
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle):
            if line.startswith("ID\t"):
                header_line = line_number
                break
    if header_line is None:
        raise ValueError(f"platform table header not found: {path}")
    frame = pd.read_csv(
        path,
        sep="\t",
        skiprows=header_line,
        usecols=["ID", "Gene symbol"],
        dtype="string",
    )
    mapping: dict[str, str] = {}
    for probe, raw_symbol in frame.itertuples(index=False, name=None):
        symbol = _first_gene_symbol(raw_symbol)
        if symbol is not None and str(probe) not in mapping:
            mapping[str(probe)] = symbol
    return mapping


def _aggregate_probes(
    probes: np.ndarray, sample_ids: np.ndarray, matrix: np.ndarray, mapping: dict[str, str]
) -> pd.DataFrame:
    symbols = np.asarray([mapping.get(str(probe), "") for probe in probes])
    keep = symbols != ""
    if not keep.any():
        raise ValueError("no expression probes mapped to gene symbols")
    frame = pd.DataFrame(matrix[keep].T, index=sample_ids.astype(str), columns=symbols[keep])
    if frame.columns.duplicated().any():
        frame = frame.T.groupby(level=0, sort=True).median().T
    else:
        frame = frame.reindex(sorted(frame.columns), axis=1)
    return frame.astype(np.float32)


def _aggregate_tcga_cache(path: Path) -> pd.DataFrame:
    payload = np.load(path, allow_pickle=False)
    ids = payload["ids"].astype(str)
    raw_features = payload["features"].astype(str)
    symbols = np.asarray(
        [_first_gene_symbol(value.split("|", 1)[-1]) or "" for value in raw_features]
    )
    keep = symbols != ""
    frame = pd.DataFrame(
        np.asarray(payload["values"], dtype=np.float32)[:, keep],
        index=ids,
        columns=symbols[keep],
    )
    if frame.columns.duplicated().any():
        frame = frame.T.groupby(level=0, sort=True).median().T
    else:
        frame = frame.reindex(sorted(frame.columns), axis=1)
    return frame.astype(np.float32)


def _within_sample_ranks(frame: pd.DataFrame) -> np.ndarray:
    values = frame.to_numpy(dtype=np.float32)
    with np.errstate(invalid="ignore"):
        medians = np.nanmedian(values, axis=0)
    medians = np.where(np.isfinite(medians), medians, 0.0)
    filled = np.where(np.isnan(values), medians, values)
    return (rankdata(filled, axis=1, method="average") / float(filled.shape[1])).astype(np.float32)


def build_transcriptomic_cache(project_root: Path, *, force: bool = False) -> Path:
    root = Path(project_root)
    cache_path = root / "data/processed/phase6/common_gene_rank_features.npz"
    if cache_path.exists() and not force:
        return cache_path
    tcga = _aggregate_tcga_cache(
        root / "data/interim/phase3/tcga_hnsc/expression_protein_coding_log2_tpm.npz"
    )
    geo_specs = {
        "gse65858": (
            root / "data/interim/gse65858/geo_2026-06-03/GSE65858_series_matrix.txt",
            root / "data/interim/gse65858/geo_2026-06-03/GPL10558.annot",
        ),
        "gse41613": (
            root / "data/interim/gse41613/geo_2026-07-06/GSE41613_series_matrix.txt",
            root / "data/interim/gse41613/geo_2026-07-06/GPL570.annot",
        ),
    }
    geo: dict[str, pd.DataFrame] = {}
    for name, (matrix_path, platform_path) in geo_specs.items():
        probes, sample_ids, matrix = _read_geo_table(matrix_path)
        geo[name] = _aggregate_probes(
            probes, sample_ids, matrix, _platform_gene_map(platform_path)
        )
    common = sorted(set(tcga.columns) & set(geo["gse65858"].columns) & set(geo["gse41613"].columns))
    if not common:
        raise ValueError("TCGA/GEO common-gene intersection is empty")
    tcga = tcga.loc[:, common]
    selected_geo: dict[str, pd.DataFrame] = {}
    for cohort in ("GSE65858", "GSE41613"):
        rows = frozen_rows(root, cohort)
        ids = rows["native_id"].astype(str).tolist()
        selected_geo[cohort.lower()] = geo[cohort.lower()].reindex(ids).loc[:, common]
        if selected_geo[cohort.lower()].isna().all(axis=1).any():
            raise ValueError(f"missing GEO expression samples for {cohort}")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache_path,
        common_genes=np.asarray(common),
        tcga_ids=tcga.index.to_numpy(dtype=str),
        tcga_ranks=_within_sample_ranks(tcga),
        gse65858_ids=selected_geo["gse65858"].index.to_numpy(dtype=str),
        gse65858_ranks=_within_sample_ranks(selected_geo["gse65858"]),
        gse41613_ids=selected_geo["gse41613"].index.to_numpy(dtype=str),
        gse41613_ranks=_within_sample_ranks(selected_geo["gse41613"]),
    )
    return cache_path


def load_transcriptomic_cache(project_root: Path, *, build: bool = False) -> TranscriptomicCache:
    root = Path(project_root)
    path = root / "data/processed/phase6/common_gene_rank_features.npz"
    if build and not path.exists():
        build_transcriptomic_cache(root)
    if not path.exists():
        raise FileNotFoundError("Phase 6 common-gene rank cache is absent")
    payload = np.load(path, allow_pickle=False)
    return TranscriptomicCache(
        common_genes=payload["common_genes"].astype(str),
        tcga_ids=payload["tcga_ids"].astype(str),
        tcga_ranks=np.asarray(payload["tcga_ranks"], dtype=np.float32),
        gse65858_ids=payload["gse65858_ids"].astype(str),
        gse65858_ranks=np.asarray(payload["gse65858_ranks"], dtype=np.float32),
        gse41613_ids=payload["gse41613_ids"].astype(str),
        gse41613_ranks=np.asarray(payload["gse41613_ranks"], dtype=np.float32),
    )


def _rank_frame(
    ids: np.ndarray, values: np.ndarray, genes: np.ndarray, wanted: list[str]
) -> pd.DataFrame:
    positions = {value: index for index, value in enumerate(ids.astype(str))}
    missing = [value for value in wanted if value not in positions]
    if missing:
        raise ValueError(f"missing cached expression rows: {len(missing)}")
    matrix = np.vstack([values[positions[value]] for value in wanted])
    return pd.DataFrame(matrix, columns=genes.astype(str))


def load_geo_features(
    project_root: Path, cohort: str, *, build_cache: bool = False
) -> CohortFeatures:
    canonical = cohort.strip().upper()
    if canonical not in {"GSE65858", "GSE41613"}:
        raise ValueError(f"unsupported GEO cohort: {cohort}")
    root = Path(project_root)
    rows = frozen_rows(root, canonical)
    ids = rows["native_id"].astype(str).tolist()
    clinical = rows[["age", "sex", "site", "stage", "hpv", "treatment", "smoking"]].copy()
    cache = load_transcriptomic_cache(root, build=build_cache)
    if canonical == "GSE65858":
        modality = _rank_frame(cache.gse65858_ids, cache.gse65858_ranks, cache.common_genes, ids)
        role = "external_test"
    else:
        modality = _rank_frame(cache.gse41613_ids, cache.gse41613_ranks, cache.common_genes, ids)
        role = "sensitivity"
    return CohortFeatures(
        canonical, role, np.asarray(ids), clinical.reset_index(drop=True), modality
    )


def load_phase6_development_data(
    project_root: Path, study: str, *, assay: str = "original"
) -> StudyData:
    root = Path(project_root)
    canonical = study.strip().upper().replace("_", "-")
    if canonical == "RADCURE":
        base = load_phase3_study_data(root, "RADCURE")
        train = load_radcure_features(root, role="train", assay=assay)
        calibration = load_radcure_features(root, role="calibration", assay=assay)
        modality = pd.concat([train.modality, calibration.modality], ignore_index=True)
        return replace(base, modality=modality, modality_blocker=None)
    if assay != "original":
        raise ValueError("assay override is supported only for RADCURE")
    if canonical == "HANCOCK":
        return load_phase3_study_data(root, "HANCOCK")
    if canonical == "TCGA-HNSC":
        base = load_phase3_study_data(root, "TCGA-HNSC", build_expression=False)
        cache = load_transcriptomic_cache(root, build=True)
        wanted = base.ids.astype(str).tolist()
        modality = _rank_frame(cache.tcga_ids, cache.tcga_ranks, cache.common_genes, wanted)
        return replace(base, modality=modality, modality_blocker=None)
    raise ValueError(f"unsupported Phase 6 development study: {study}")
