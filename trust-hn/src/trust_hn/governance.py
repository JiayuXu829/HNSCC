"""Analysis-freeze and sealed-test enforcement.

The freeze file is stored as JSON text with a ``.yaml`` suffix. JSON is a valid
subset of YAML and permits Phase 0 checks using only the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from trust_hn.utils.hashing import sha256_file


class SealedTestError(PermissionError):
    """Raised whenever locked-test access is not fully authorized."""


@dataclass(frozen=True)
class FreezeRecord:
    path: Path
    payload: Mapping[str, object]

    @classmethod
    def load(cls, path: str | Path) -> "FreezeRecord":
        path = Path(path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SealedTestError(f"invalid or unreadable freeze file: {path}") from exc
        if not isinstance(payload, dict):
            raise SealedTestError("freeze record must be a mapping")
        return cls(path=path, payload=payload)

    def assert_locked_evaluation_allowed(
        self,
        approval_token: str | None,
        project_root: str | Path,
    ) -> None:
        project_root = Path(project_root).resolve()
        status = str(self.payload.get("status", "")).upper()
        if status != "FROZEN":
            raise SealedTestError("analysis is not FROZEN")

        required_flags = ("primary_hypotheses_frozen", "models_frozen", "thresholds_frozen")
        missing_flags = [flag for flag in required_flags if self.payload.get(flag) is not True]
        if missing_flags:
            raise SealedTestError(f"freeze flags are incomplete: {missing_flags}")

        unseal = self.payload.get("test_unseal")
        if not isinstance(unseal, dict) or unseal.get("approved") is not True:
            raise SealedTestError("locked-test unsealing has not been approved")
        expected_token_hash = unseal.get("approval_token_sha256")
        if not approval_token or not expected_token_hash:
            raise SealedTestError("an approval token and its registered hash are required")
        observed_token_hash = hashlib.sha256(approval_token.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(observed_token_hash, str(expected_token_hash)):
            raise SealedTestError("approval token does not match the freeze record")

        self._assert_hashes(project_root, "config_sha256")
        self._assert_hashes(project_root, "sealed_manifest_sha256")

    def _assert_hashes(self, project_root: Path, key: str) -> None:
        entries = self.payload.get(key)
        if not isinstance(entries, dict) or not entries:
            raise SealedTestError(f"{key} is empty; immutable inputs are not registered")
        for relative_path, expected_hash in entries.items():
            candidate = (project_root / str(relative_path)).resolve()
            try:
                candidate.relative_to(project_root)
            except ValueError as exc:
                raise SealedTestError(f"registered path escapes project root: {relative_path}") from exc
            if not candidate.is_file():
                raise SealedTestError(f"registered file is missing: {relative_path}")
            observed_hash = sha256_file(candidate)
            if not hmac.compare_digest(observed_hash, str(expected_hash)):
                raise SealedTestError(f"hash mismatch for {relative_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Authorize a locked TRUST-HN evaluation")
    parser.add_argument("--freeze", default="configs/analysis_freeze.yaml")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--approval-token", required=True)
    args = parser.parse_args(argv)
    FreezeRecord.load(args.freeze).assert_locked_evaluation_allowed(
        approval_token=args.approval_token,
        project_root=args.project_root,
    )
    print("LOCKED_EVALUATION_AUTHORIZED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())