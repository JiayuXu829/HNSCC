"""Aggregate-only audit and extraction for the processed RADCURE ORCESTRA RDS.

The R object is a ``MultiAssayExperiment`` containing Bioconductor classes that
``rdata`` does not construct natively. The converter nevertheless exposes the
underlying slots as ``SimpleNamespace`` objects. This module deliberately uses
only those stable slots, validates exact patient/feature alignment, and keeps
patient-level matrices in Git-ignored locations.
"""

from __future__ import annotations

import hashlib
import json
import warnings
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import numpy as np

PRIMARY_ASSAYS = (
    "radiomics.pyradiomics_original",
    "radiomics.pyradiomics_shuffled_full",
    "radiomics.pyradiomics_randomized_sampled_full",
)

_EXCLUDED_EXACT = {
    "patient_ID",
    "study_description",
    "series_UID",
    "series_description",
    "image_modality",
    "instances",
    "seg_series_UID",
    "seg_modality",
    "seg_ref_image",
    "roi",
    "roi_number",
    "negative_control",
}
_EXCLUDED_PREFIXES = ("diagnostics_",)


class RadcureRDSAuditError(ValueError):
    """Raised when the converted RDS violates the frozen structural contract."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RadcureRDSAuditError(f"{label} is not a mapping")
    return value


def load_radcure_rds(path: str | Path) -> Any:
    """Load the RDS while suppressing known missing Bioconductor constructors."""
    try:
        import rdata
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("rdata==1.1.0 is required to inspect the RADCURE RDS") from exc
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r"Missing constructor for R class .*" )
        return rdata.read_rds(Path(path))


def experiment_names(root: Any) -> tuple[str, ...]:
    experiments = getattr(getattr(root, "ExperimentList", None), "listData", None)
    return tuple(str(name) for name in _mapping(experiments, "ExperimentList.listData"))


def assay_payload(root: Any, experiment_name: str) -> Mapping[str, Any]:
    experiments = _mapping(
        getattr(getattr(root, "ExperimentList", None), "listData", None),
        "ExperimentList.listData",
    )
    if experiment_name not in experiments:
        raise RadcureRDSAuditError(f"missing experiment: {experiment_name}")
    experiment = experiments[experiment_name]
    assay_list = _mapping(
        getattr(getattr(getattr(experiment, "assays", None), "data", None), "listData", None),
        f"{experiment_name}.assays.data.listData",
    )
    if len(assay_list) != 1:
        raise RadcureRDSAuditError(f"{experiment_name} must contain exactly one assay")
    assay = next(iter(assay_list.values()))
    payload = getattr(
        getattr(getattr(assay, "data", None), "unlistData", None), "listData", None
    )
    return _mapping(payload, f"{experiment_name}.unlistData.listData")


def patient_ids(payload: Mapping[str, Any]) -> np.ndarray:
    if "patient_ID" not in payload:
        raise RadcureRDSAuditError("assay has no patient_ID field")
    ids = np.asarray(payload["patient_ID"]).astype(str)
    if ids.ndim != 1 or ids.size == 0:
        raise RadcureRDSAuditError("patient_ID must be a non-empty vector")
    normalized = np.char.strip(ids)
    if np.any(normalized == ""):
        raise RadcureRDSAuditError("blank patient_ID detected")
    if np.unique(normalized).size != normalized.size:
        raise RadcureRDSAuditError("duplicate patient_ID detected")
    return normalized


def _is_numeric_vector(value: Any, expected_length: int) -> bool:
    array = np.asarray(value)
    return array.ndim == 1 and len(array) == expected_length and array.dtype.kind in "biufc"


def feature_names(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Select numerical PyRadiomics features using names/types only, never outcomes."""
    n = len(patient_ids(payload))
    names = []
    for raw_name, value in payload.items():
        name = str(raw_name)
        if name in _EXCLUDED_EXACT or name.startswith(_EXCLUDED_PREFIXES):
            continue
        if _is_numeric_vector(value, n):
            names.append(name)
    if not names:
        raise RadcureRDSAuditError("no numerical PyRadiomics features selected")
    return tuple(names)


def extract_assay(
    root: Any, experiment_name: str
) -> tuple[np.ndarray, tuple[str, ...], np.ndarray]:
    payload = assay_payload(root, experiment_name)
    ids = patient_ids(payload)
    names = feature_names(payload)
    matrix = np.column_stack([np.asarray(payload[name], dtype=np.float32) for name in names])
    if matrix.shape != (len(ids), len(names)):
        raise RadcureRDSAuditError("feature matrix shape mismatch")
    if not np.isfinite(matrix).all():
        raise RadcureRDSAuditError(f"non-finite values detected in {experiment_name}")
    return ids, names, matrix


def ordered_id_digest(ids: Iterable[str]) -> str:
    normalized = sorted(str(value).strip() for value in ids)
    return hashlib.sha256("\0".join(normalized).encode("utf-8")).hexdigest()


def audit_radcure_object(root: Any) -> dict[str, object]:
    names = experiment_names(root)
    missing = [name for name in PRIMARY_ASSAYS if name not in names]
    if missing:
        raise RadcureRDSAuditError(f"missing primary assays: {missing}")

    extracted = {name: extract_assay(root, name) for name in PRIMARY_ASSAYS}
    reference_ids, reference_features, reference_matrix = extracted[PRIMARY_ASSAYS[0]]
    for name in PRIMARY_ASSAYS[1:]:
        ids, features, matrix = extracted[name]
        if not np.array_equal(ids, reference_ids):
            raise RadcureRDSAuditError(f"patient order differs for {name}")
        if features != reference_features:
            raise RadcureRDSAuditError(f"feature names/order differ for {name}")
        if matrix.shape != reference_matrix.shape:
            raise RadcureRDSAuditError(f"matrix shape differs for {name}")

    col_data = getattr(root, "colData", None)
    col_n = int(getattr(col_data, "nrows", len(reference_ids)))
    col_ids_raw = getattr(col_data, "listData", {}).get("patient_ID")
    if col_ids_raw is not None and not np.array_equal(
        np.char.strip(np.asarray(col_ids_raw).astype(str)), reference_ids
    ):
        raise RadcureRDSAuditError("colData patient order differs from radiomics assays")
    if col_n != len(reference_ids):
        raise RadcureRDSAuditError("colData patient count differs from radiomics assays")

    prefix_counts: dict[str, int] = {}
    for name in reference_features:
        prefix = name.split("_", 1)[0]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    return {
        "schema_version": "1.0",
        "patient_count": len(reference_ids),
        "coldata_field_count": len(getattr(col_data, "listData", {})),
        "sample_map_row_count": int(getattr(getattr(root, "sampleMap", None), "nrows", 0)),
        "experiment_count": len(names),
        "experiment_names": list(names),
        "audited_primary_assays": list(PRIMARY_ASSAYS),
        "selected_feature_count": len(reference_features),
        "feature_prefix_counts": dict(sorted(prefix_counts.items())),
        "matrix_shape": [int(reference_matrix.shape[0]), int(reference_matrix.shape[1])],
        "nonfinite_value_count": 0,
        "unique_patient_count": int(np.unique(reference_ids).size),
        "patient_set_sha256": ordered_id_digest(reference_ids),
        "primary_assays_aligned": True,
        "contains_patient_level_identifiers": False,
        "contains_outcomes": False,
        "feature_selection_uses_outcomes": False,
        "fmcib_used": False,
    }


def audit_radcure_rds(path: str | Path) -> tuple[Any, dict[str, object]]:
    root = load_radcure_rds(path)
    return root, audit_radcure_object(root)


def write_feature_cache(root: Any, output_path: str | Path) -> Path:
    """Write patient-level matrices only to a caller-selected Git-ignored path."""
    output = Path(output_path)
    if not any(part in {"processed", ".runtime"} for part in output.parts):
        raise RadcureRDSAuditError("feature cache must be under data/processed or .runtime")
    arrays: dict[str, np.ndarray] = {}
    reference_ids: np.ndarray | None = None
    reference_features: tuple[str, ...] | None = None
    for name in PRIMARY_ASSAYS:
        ids, features, matrix = extract_assay(root, name)
        reference_ids = ids if reference_ids is None else reference_ids
        reference_features = features if reference_features is None else reference_features
        arrays[name.replace("radiomics.pyradiomics_", "")] = matrix
    assert reference_ids is not None and reference_features is not None
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        ids=reference_ids,
        features=np.asarray(reference_features),
        **arrays,
    )
    return output


def write_audit_json(audit: Mapping[str, object], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(dict(audit), indent=2, ensure_ascii=False) + "\n"
    output.write_text(rendered, encoding="utf-8")
    return output

