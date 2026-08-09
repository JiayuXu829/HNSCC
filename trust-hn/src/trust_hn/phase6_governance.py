"""One-time authorization and consumption semantics for Phase 6 outcomes."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from trust_hn.data.phase6_data import verify_frozen_cohort_manifest
from trust_hn.governance import FreezeRecord, SealedTestError
from trust_hn.utils.hashing import sha256_file


@dataclass(frozen=True)
class ConsumptionReceipt:
    path: Path
    payload: dict[str, object]


def _atomic_json_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _relative_file(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SealedTestError(f"registered path escapes project root: {relative}") from exc
    if not candidate.is_file():
        raise SealedTestError(f"decision file is missing: {relative}")
    return candidate


def register_phase6_authorization(
    project_root: Path,
    *,
    approval_token: str,
    decision_files: Sequence[str],
    approved_by: str,
    approved_at: str = "2026-08-08",
) -> dict[str, object]:
    """Register only a token hash after all pre-unseal code/config files are final."""
    root = Path(project_root).resolve()
    freeze_path = root / "configs/analysis_freeze.yaml"
    payload = dict(FreezeRecord.load(freeze_path).payload)
    if str(payload.get("status", "")).upper() != "FROZEN":
        raise SealedTestError("analysis is not FROZEN")
    if payload.get("phase6_outcomes_seen") is not False:
        raise SealedTestError("Phase 6 outcomes are already marked as seen")
    unseal = dict(payload.get("test_unseal") or {})
    if unseal.get("approved") is True or unseal.get("consumed") is True:
        raise SealedTestError("Phase 6 authorization is already registered or consumed")
    if not approval_token:
        raise SealedTestError("a nonempty one-time token is required")

    record = FreezeRecord(freeze_path, payload)
    record._assert_hashes(root, "config_sha256")
    record._assert_hashes(root, "sealed_manifest_sha256")
    cohorts = verify_frozen_cohort_manifest(root)
    original_hash = sha256_file(freeze_path)
    hashes = dict(payload.get("config_sha256") or {})
    for relative in decision_files:
        hashes[str(relative)] = sha256_file(_relative_file(root, str(relative)))
    payload["config_sha256"] = hashes
    payload["phase6_pre_unseal_freeze_sha256"] = original_hash
    payload["phase6_registered_decision_files"] = sorted(set(map(str, decision_files)))
    payload["phase6_registered_cohorts"] = cohorts
    payload["test_unseal"] = {
        "approved": True,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "approval_token_sha256": hashlib.sha256(approval_token.encode("utf-8")).hexdigest(),
        "reason": "Explicit project-owner authorization to continue Phase 6",
        "consumed": False,
        "consumed_at": None,
    }
    _atomic_json_write(freeze_path, payload)
    return payload


def assert_phase6_ready(
    project_root: Path, *, approval_token: str
) -> list[dict[str, object]]:
    root = Path(project_root).resolve()
    freeze = FreezeRecord.load(root / "configs/analysis_freeze.yaml")
    if freeze.payload.get("phase6_outcomes_seen") is not False:
        raise SealedTestError("Phase 6 outcome authorization is already consumed")
    unseal = freeze.payload.get("test_unseal") or {}
    if isinstance(unseal, dict) and unseal.get("consumed") is True:
        raise SealedTestError("Phase 6 authorization cannot be consumed twice")
    freeze.assert_locked_evaluation_allowed(approval_token, root)
    return verify_frozen_cohort_manifest(root)


def consume_phase6_authorization(
    project_root: Path,
    *,
    approval_token: str,
    receipt_path: Path | None = None,
) -> ConsumptionReceipt:
    """Atomically mark authorization consumed immediately before outcome loading."""
    root = Path(project_root).resolve()
    cohorts = assert_phase6_ready(root, approval_token=approval_token)
    freeze_path = root / "configs/analysis_freeze.yaml"
    before_hash = sha256_file(freeze_path)
    payload = dict(FreezeRecord.load(freeze_path).payload)
    unseal = dict(payload["test_unseal"])
    consumed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    unseal["consumed"] = True
    unseal["consumed_at"] = consumed_at
    payload["test_unseal"] = unseal
    payload["phase6_outcomes_seen"] = True
    payload["phase6_outcome_access_state"] = "CONSUMED_FOR_LOCKED_EVALUATION"
    _atomic_json_write(freeze_path, payload)
    after_hash = sha256_file(freeze_path)
    receipt = {
        "schema_version": "1.0",
        "phase": "Phase 6 one-time retrospective locked/external evaluation",
        "consumed_at": consumed_at,
        "authorization_token_sha256": unseal["approval_token_sha256"],
        "freeze_sha256_before_consumption": before_hash,
        "freeze_sha256_after_consumption": after_hash,
        "phase6_pre_unseal_freeze_sha256": payload.get("phase6_pre_unseal_freeze_sha256"),
        "registered_decision_file_count": len(payload.get("phase6_registered_decision_files", [])),
        "cohorts": cohorts,
        "patient_level_identifiers_in_receipt": False,
        "outcomes_in_receipt": False,
        "retuning_authorized": False,
    }
    target = receipt_path or root / "results/manifests/phase6_locked_evaluation_receipt.json"
    _atomic_json_write(target, receipt)
    return ConsumptionReceipt(target, receipt)


def assert_token_absent_from_tracked_files(project_root: Path, approval_token: str) -> None:
    """Conservatively scan non-ignored project text files for plaintext token leakage."""
    root = Path(project_root).resolve()
    if not approval_token:
        raise ValueError("approval token is empty")
    ignored_roots = {
        (root / ".git").resolve(),
        (root / ".venv").resolve(),
        (root / ".runtime").resolve(),
        (root / "data/raw").resolve(),
        (root / "data/interim").resolve(),
        (root / "data/processed").resolve(),
        (root / "results/predictions").resolve(),
    }
    for path in root.rglob("*"):
        ignored = any(
            parent == path or parent in path.parents for parent in ignored_roots
        )
        if not path.is_file() or ignored:
            continue
        if path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if approval_token in text:
            raise SealedTestError(f"plaintext approval token leaked into tracked area: {path}")
