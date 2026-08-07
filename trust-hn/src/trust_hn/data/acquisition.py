"""Allowlist-enforced acquisition of small public Phase 1 artifacts."""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from trust_hn.utils.hashing import sha256_file


class AcquisitionPolicyError(PermissionError):
    """Raised before a download that violates the Phase 1 safety envelope."""


@dataclass(frozen=True)
class AcquisitionPolicy:
    allowed_hosts: frozenset[str]
    allowed_roles: frozenset[str]
    forbidden_roles: frozenset[str]
    max_single_file_bytes: int
    max_planned_total_bytes: int
    https_required: bool
    raw_destination_root: str

    @classmethod
    def load(cls, path: str | Path) -> "AcquisitionPolicy":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            allowed_hosts=frozenset(str(value).lower() for value in payload["allowed_hosts"]),
            allowed_roles=frozenset(str(value) for value in payload["allowed_artifact_roles"]),
            forbidden_roles=frozenset(str(value) for value in payload["forbidden_artifact_roles"]),
            max_single_file_bytes=int(payload["max_single_file_bytes"]),
            max_planned_total_bytes=int(payload["max_planned_total_bytes"]),
            https_required=bool(payload["https_required"]),
            raw_destination_root=str(payload["raw_destination_root"]),
        )

    def validate_request(self, url: str, role: str, expected_bytes: int | None = None) -> None:
        parsed = urllib.parse.urlparse(url)
        if self.https_required and parsed.scheme.lower() != "https":
            raise AcquisitionPolicyError("only HTTPS sources are permitted")
        host = (parsed.hostname or "").lower()
        if host not in self.allowed_hosts:
            raise AcquisitionPolicyError(f"source host is not allowlisted: {host or '<missing>'}")
        if role in self.forbidden_roles:
            raise AcquisitionPolicyError(f"artifact role is explicitly forbidden: {role}")
        if role not in self.allowed_roles:
            raise AcquisitionPolicyError(f"artifact role is not approved: {role}")
        if expected_bytes is not None:
            if expected_bytes < 0:
                raise AcquisitionPolicyError("expected_bytes cannot be negative")
            if expected_bytes > self.max_single_file_bytes:
                raise AcquisitionPolicyError("planned file exceeds the single-file size ceiling")

    def resolve_destination(self, project_root: Path, study: str, filename: str) -> Path:
        if not study or any(character in study for character in "\\/:"):
            raise AcquisitionPolicyError("study must be a safe directory name")
        if Path(filename).name != filename or not filename:
            raise AcquisitionPolicyError("filename must not contain a directory component")
        raw_root = (project_root / self.raw_destination_root).resolve()
        destination = (raw_root / study / filename).resolve()
        try:
            destination.relative_to(raw_root)
        except ValueError as exc:
            raise AcquisitionPolicyError("destination escapes data/raw") from exc
        return destination


def _parse_content_length(headers: Mapping[str, str]) -> int | None:
    value = headers.get("Content-Length")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def download_public_artifact(
    *,
    url: str,
    role: str,
    study: str,
    filename: str,
    project_root: Path,
    policy: AcquisitionPolicy,
    expected_sha256: str | None = None,
    expected_bytes: int | None = None,
) -> dict[str, object]:
    """Download one approved artifact atomically and emit a provenance receipt."""
    policy.validate_request(url, role, expected_bytes)
    destination = policy.resolve_destination(project_root, study, filename)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        observed_hash = sha256_file(destination)
        if expected_sha256 and observed_hash != expected_sha256.lower():
            raise AcquisitionPolicyError(f"existing file hash mismatch: {destination}")
        return {
            "status": "already_present",
            "study": study,
            "role": role,
            "source_url": url,
            "relative_path": destination.relative_to(project_root).as_posix(),
            "bytes": destination.stat().st_size,
            "sha256": observed_hash,
        }

    request = urllib.request.Request(url, headers={"User-Agent": "TRUST-HN/0.1 Phase1Audit"})
    temporary_path: Path | None = None
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            content_length = _parse_content_length(response.headers)
            if content_length is not None and content_length > policy.max_single_file_bytes:
                raise AcquisitionPolicyError("server Content-Length exceeds size ceiling")
            with tempfile.NamedTemporaryFile(
                dir=destination.parent, prefix=f".{filename}.", suffix=".part", delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                downloaded = 0
                while chunk := response.read(1024 * 1024):
                    downloaded += len(chunk)
                    if downloaded > policy.max_single_file_bytes:
                        raise AcquisitionPolicyError("download exceeded size ceiling")
                    temporary.write(chunk)
        observed_hash = sha256_file(temporary_path)
        if expected_bytes is not None and temporary_path.stat().st_size != expected_bytes:
            raise AcquisitionPolicyError("downloaded byte count differs from frozen expectation")
        if expected_sha256 and observed_hash != expected_sha256.lower():
            raise AcquisitionPolicyError("downloaded SHA-256 differs from frozen expectation")
        os.replace(temporary_path, destination)
        destination.chmod(stat.S_IREAD)
        receipt = {
            "status": "downloaded",
            "study": study,
            "role": role,
            "source_url": url,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "relative_path": destination.relative_to(project_root).as_posix(),
            "bytes": destination.stat().st_size,
            "sha256": observed_hash,
            "immutable": True,
        }
        receipt_path = destination.with_suffix(destination.suffix + ".receipt.json")
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return receipt
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()