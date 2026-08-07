"""Register manually downloaded public artifacts; downloads require explicit source review."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path

from trust_hn.utils.hashing import sha256_file


ALLOWED_STUDIES = {"radcure", "hancock", "tcga_hnsc", "gse65858", "gse41613"}


def register_local_file(source: Path, project_root: Path, study: str) -> dict[str, object]:
    if study not in ALLOWED_STUDIES:
        raise ValueError(f"unsupported study: {study}")
    if not source.is_file():
        raise FileNotFoundError(source)
    target_dir = project_root / "data" / "raw" / study
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    if target.exists() and sha256_file(target) != sha256_file(source):
        raise FileExistsError(f"different file already registered at {target}")
    if not target.exists():
        shutil.copy2(source, target)
    return {
        "study": study,
        "source_name": source.name,
        "registered_path": target.relative_to(project_root).as_posix(),
        "retrieved_on": date.today().isoformat(),
        "bytes": target.stat().st_size,
        "sha256": sha256_file(target),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", required=True, choices=sorted(ALLOWED_STUDIES))
    parser.add_argument("--local-file", required=True, type=Path)
    parser.add_argument("--project-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--metadata-output", type=Path)
    args = parser.parse_args(argv)
    record = register_local_file(args.local_file, args.project_root, args.study)
    text = json.dumps(record, indent=2, ensure_ascii=False)
    if args.metadata_output:
        args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())