"""Audit the processed RADCURE RDS and optionally build a Git-ignored cache."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from trust_hn.data.radcure_rds import (
    PRIMARY_ASSAYS,
    audit_radcure_rds,
    extract_assay,
    ordered_id_digest,
    write_audit_json,
    write_feature_cache,
)
from trust_hn.utils.hashing import sha256_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--rds", default="data/raw/radcure/RADCURE_READII-RADIOMICS_MAE.RDS")
    parser.add_argument("--cache", default="data/processed/radcure/phase6_pyradiomics_features.npz")
    parser.add_argument("--output", default="results/manifests/radcure_rds_structure.json")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    rds_path = root / args.rds
    converted, audit = audit_radcure_rds(rds_path)

    adapter = pd.read_csv(
        root / "data/interim/phase2/radcure/adapter_records.csv",
        dtype={"native_id": "string"},
        usecols=["native_id", "split_role", "eligible"],
    )
    assay_ids, _, _ = extract_assay(converted, PRIMARY_ASSAYS[0])
    available = set(assay_ids.astype(str))
    eligible = adapter.loc[adapter["eligible"].astype(str).str.casefold().eq("true")].copy()
    role_counts = eligible.groupby("split_role").size().to_dict()
    missing_by_role = {
        str(role): int((~rows["native_id"].astype(str).isin(available)).sum())
        for role, rows in eligible.groupby("split_role")
    }
    sealed_ids = eligible.loc[eligible["split_role"].eq("sealed_test"), "native_id"].astype(str)
    audit.update(
        {
            "rds_sha256": sha256_file(rds_path),
            "eligible_adapter_role_counts": {str(k): int(v) for k, v in role_counts.items()},
            "eligible_ids_missing_from_rds_by_role": missing_by_role,
            "sealed_test_patient_count": len(sealed_ids),
            "sealed_test_ordered_id_set_sha256": ordered_id_digest(sealed_ids),
            "all_eligible_adapter_ids_present": all(
                value == 0 for value in missing_by_role.values()
            ),
        }
    )
    output = write_audit_json(audit, root / args.output)
    if not args.no_cache:
        write_feature_cache(converted, root / args.cache)
    print(json.dumps({"audit": output.relative_to(root).as_posix(), **audit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

