from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from trust_hn.data.phase6_data import COHORT_SPECS, ordered_id_digest
from trust_hn.governance import SealedTestError
from trust_hn.phase6_governance import (
    assert_phase6_ready,
    assert_token_absent_from_tracked_files,
    consume_phase6_authorization,
    register_phase6_authorization,
)
from trust_hn.utils.hashing import sha256_file


class Phase6GovernanceTests(unittest.TestCase):
    def _fixture(self, root: Path) -> None:
        manifest_entries = []
        for index, (cohort, (slug, role, manifest_name)) in enumerate(COHORT_SPECS.items()):
            ids = [f"{cohort}-{index}-a", f"{cohort}-{index}-b"]
            source = root / "data/interim/phase2" / slug / "adapter_records.csv"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                "native_id,split_role,eligible,endpoint_status,age,sex,site,stage,"
                "hpv,treatment,age_group,smoking\n"
                + "\n".join(
                    f"{native_id},{role},True,sealed,60,F,site,III,negative,RT,60+,never"
                    for native_id in ids
                )
                + "\n",
                encoding="utf-8",
            )
            manifest_entries.append(
                {
                    "cohort": manifest_name,
                    "split_roles": [role],
                    "patient_count": 2,
                    "ordered_id_set_sha256": ordered_id_digest(ids),
                    "source_adapter_sha256": sha256_file(source),
                    "contains_patient_level_identifiers": False,
                    "contains_outcomes": False,
                }
            )
        manifest = root / "data/manifests/sealed/phase6_cohort_set_manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps({"schema_version": "1", "cohorts": manifest_entries}),
            encoding="utf-8",
        )
        model = root / "model.json"
        model.write_text('{"fixed": true}\n', encoding="utf-8")
        decision = root / "phase6.py"
        decision.write_text("# frozen decision code\n", encoding="utf-8")
        freeze = {
            "status": "FROZEN",
            "primary_hypotheses_frozen": True,
            "models_frozen": True,
            "thresholds_frozen": True,
            "config_sha256": {"model.json": sha256_file(model)},
            "sealed_manifest_sha256": {
                "data/manifests/sealed/phase6_cohort_set_manifest.json": sha256_file(manifest)
            },
            "phase6_outcomes_seen": False,
            "test_unseal": {"approved": False},
        }
        path = root / "configs/analysis_freeze.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(freeze), encoding="utf-8")

    def test_registration_stores_only_token_hash_and_consumes_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            token = "one-time-secret-token"
            payload = register_phase6_authorization(
                root,
                approval_token=token,
                decision_files=["phase6.py"],
                approved_by="project owner",
            )
            rendered = json.dumps(payload)
            self.assertNotIn(token, rendered)
            self.assertEqual(
                payload["test_unseal"]["approval_token_sha256"],
                hashlib.sha256(token.encode()).hexdigest(),
            )
            assert_phase6_ready(root, approval_token=token)
            with self.assertRaises(SealedTestError):
                assert_phase6_ready(root, approval_token="wrong")
            receipt = consume_phase6_authorization(
                root, approval_token=token, receipt_path=root / "receipt.json"
            )
            self.assertNotIn(token, json.dumps(receipt.payload))
            freeze = json.loads((root / "configs/analysis_freeze.yaml").read_text())
            self.assertTrue(freeze["phase6_outcomes_seen"])
            self.assertTrue(freeze["test_unseal"]["consumed"])
            with self.assertRaises(SealedTestError):
                consume_phase6_authorization(root, approval_token=token)

    def test_hash_or_manifest_mismatch_refuses_registration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            (root / "model.json").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(SealedTestError):
                register_phase6_authorization(
                    root,
                    approval_token="secret",
                    decision_files=["phase6.py"],
                    approved_by="owner",
                )

    def test_plaintext_token_scan_excludes_runtime_but_rejects_tracked_area(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            token = "token-never-track"
            runtime = root / ".runtime"
            runtime.mkdir()
            (runtime / "phase6.token").write_text(token, encoding="utf-8")
            assert_token_absent_from_tracked_files(root, token)
            (root / "report.md").write_text(f"leaked {token}", encoding="utf-8")
            with self.assertRaises(SealedTestError):
                assert_token_absent_from_tracked_files(root, token)


if __name__ == "__main__":
    unittest.main()
