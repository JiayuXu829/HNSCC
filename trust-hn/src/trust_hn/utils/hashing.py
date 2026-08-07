"""Deterministic hashing helpers used by data and analysis governance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    """Hash JSON-compatible content using stable key ordering and separators."""
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def pseudonym_hash(identifier: str, salt: str) -> str:
    """Hash an identifier for overlap checks without writing the source ID."""
    if not identifier or not salt:
        raise ValueError("identifier and salt must both be non-empty")
    return hashlib.sha256(f"{salt}\0{identifier}".encode()).hexdigest()


def hash_ordered_ids(identifiers: Iterable[str], salt: str) -> str:
    """Hash a sorted unique set of identifiers for sealed-manifest integrity."""
    normalized = sorted({pseudonym_hash(str(value), salt) for value in identifiers})
    return canonical_json_sha256(normalized)