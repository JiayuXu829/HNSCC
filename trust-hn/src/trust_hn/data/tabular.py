"""Dependency-free readers and field resolution for Phase 1 tabular audits."""

from __future__ import annotations

import csv
import gzip
import io
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Mapping, Sequence, TextIO


class TableAuditError(ValueError):
    """Raised when a source table cannot be interpreted without guessing."""


MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "unknown", "not available"}


def normalize_field_name(value: str) -> str:
    """Normalize formatting only; this is not semantic fuzzy matching."""
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def is_missing(value: object) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in MISSING_TOKENS


@contextmanager
def open_text(path: str | Path) -> Iterator[TextIO]:
    path = Path(path)
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
            yield handle
    else:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            yield handle


def detect_delimiter(sample: str, path: str | Path) -> str:
    suffixes = [suffix.lower() for suffix in Path(path).suffixes]
    if ".tsv" in suffixes:
        return "\t"
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t;|").delimiter
    except csv.Error:
        if sample.count("\t") > sample.count(","):
            return "\t"
        return ","


def read_delimited(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read CSV/TSV, optionally gzip compressed, preserving source strings."""
    with open_text(path) as handle:
        sample = handle.read(65536)
        handle.seek(0)
        delimiter = detect_delimiter(sample, path)
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            raise TableAuditError(f"table has no header: {path}")
        headers = [str(name).strip() for name in reader.fieldnames]
        if len(headers) != len(set(headers)):
            raise TableAuditError(f"duplicate column names are not allowed: {path}")
        rows = []
        for row in reader:
            rows.append({str(key).strip(): "" if value is None else value for key, value in row.items()})
    return headers, rows


def resolve_unique_field(headers: Sequence[str], candidates: Sequence[str]) -> str | None:
    """Resolve an explicitly listed candidate after formatting normalization.

    Returns ``None`` if no candidate exists and raises on ambiguity. It never
    uses edit distance or semantic guessing.
    """
    normalized_headers: dict[str, list[str]] = {}
    for header in headers:
        normalized_headers.setdefault(normalize_field_name(header), []).append(header)

    matches: list[str] = []
    for candidate in candidates:
        matches.extend(normalized_headers.get(normalize_field_name(candidate), []))
    unique = sorted(set(matches))
    if len(unique) > 1:
        raise TableAuditError(f"candidate list is ambiguous; matched columns: {unique}")
    return unique[0] if unique else None


def parse_binary_event(value: str, mapping: Mapping[str, int] | None = None) -> int:
    if is_missing(value):
        raise TableAuditError("event is missing")
    normalized = str(value).strip().lower()
    if mapping:
        normalized_mapping = {str(key).strip().lower(): int(result) for key, result in mapping.items()}
        if normalized in normalized_mapping:
            result = normalized_mapping[normalized]
            if result not in (0, 1):
                raise TableAuditError("event mapping must produce 0 or 1")
            return result
    if normalized in {"0", "0.0", "false", "no", "alive", "censored"}:
        return 0
    if normalized in {"1", "1.0", "true", "yes", "dead", "deceased", "event"}:
        return 1
    raise TableAuditError(f"cannot map event value without an explicit mapping: {value!r}")


def parse_nonnegative_float(value: str, field_name: str) -> float:
    if is_missing(value):
        raise TableAuditError(f"{field_name} is missing")
    try:
        number = float(str(value).strip())
    except ValueError as exc:
        raise TableAuditError(f"{field_name} is not numeric: {value!r}") from exc
    if number < 0:
        raise TableAuditError(f"{field_name} is negative: {value!r}")
    return number