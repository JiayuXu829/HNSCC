from __future__ import annotations

import hashlib
from types import SimpleNamespace

import numpy as np
import pytest

from trust_hn.data.radcure_rds import (
    RadcureRDSAuditError,
    assay_payload,
    audit_radcure_object,
    feature_names,
    ordered_id_digest,
)


def _assay(ids: list[str], values: dict[str, np.ndarray]) -> SimpleNamespace:
    payload = {
        "patient_ID": np.asarray(ids),
        "series_UID": np.asarray(["uid"] * len(ids)),
        "diagnostics_Image-original_Mean": np.ones(len(ids)),
        **values,
    }
    return SimpleNamespace(
        assays=SimpleNamespace(
            data=SimpleNamespace(
                listData={
                    "payload": SimpleNamespace(
                        data=SimpleNamespace(
                            unlistData=SimpleNamespace(listData=payload)
                        )
                    )
                }
            )
        )
    )


def _object(misaligned: bool = False) -> SimpleNamespace:
    ids = ["RADCURE-0001", "RADCURE-0002", "RADCURE-0003"]
    control_ids = ids[::-1] if misaligned else ids
    experiments = {
        "radiomics.pyradiomics_original": _assay(
            ids,
            {
                "original_shape_MeshVolume": np.array([1.0, 2.0, 3.0]),
                "wavelet-HLL_glcm_Contrast": np.array([4.0, 5.0, 6.0]),
            },
        ),
        "radiomics.pyradiomics_shuffled_full": _assay(
            control_ids,
            {
                "original_shape_MeshVolume": np.array([1.1, 2.1, 3.1]),
                "wavelet-HLL_glcm_Contrast": np.array([4.1, 5.1, 6.1]),
            },
        ),
        "radiomics.pyradiomics_randomized_sampled_full": _assay(
            ids,
            {
                "original_shape_MeshVolume": np.array([1.2, 2.2, 3.2]),
                "wavelet-HLL_glcm_Contrast": np.array([4.2, 5.2, 6.2]),
            },
        ),
    }
    return SimpleNamespace(
        colData=SimpleNamespace(
            rownames=np.asarray(ids),
            nrows=3,
            listData={"patient_ID": np.asarray(ids)},
        ),
        sampleMap=SimpleNamespace(nrows=9, listData={}),
        ExperimentList=SimpleNamespace(listData=experiments),
    )


def test_feature_policy_excludes_identifiers_and_diagnostics() -> None:
    payload = assay_payload(_object(), "radiomics.pyradiomics_original")
    assert feature_names(payload) == (
        "original_shape_MeshVolume",
        "wavelet-HLL_glcm_Contrast",
    )


def test_audit_checks_alignment_without_emitting_ids() -> None:
    audit = audit_radcure_object(_object())
    rendered = str(audit)
    assert audit["patient_count"] == 3
    assert audit["selected_feature_count"] == 2
    assert audit["primary_assays_aligned"] is True
    assert "RADCURE-0001" not in rendered


def test_audit_rejects_misaligned_negative_control() -> None:
    with pytest.raises(RadcureRDSAuditError, match="patient order"):
        audit_radcure_object(_object(misaligned=True))


def test_ordered_digest_matches_frozen_manifest_convention() -> None:
    ids = ["b", "a"]
    expected = hashlib.sha256(b"a\0b").hexdigest()
    assert ordered_id_digest(ids) == expected
