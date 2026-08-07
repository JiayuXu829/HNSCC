import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from trust_hn.governance import FreezeRecord, SealedTestError
from trust_hn.utils.hashing import sha256_file


class GovernanceTests(unittest.TestCase):
    def test_draft_freeze_refuses_locked_test(self):
        root = Path(__file__).resolve().parents[1]
        freeze = FreezeRecord.load(root / "configs" / "analysis_freeze.yaml")
        with self.assertRaises(SealedTestError):
            freeze.assert_locked_evaluation_allowed("anything", root)

    def test_complete_freeze_accepts_only_registered_token_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "model.yaml"
            manifest = root / "sealed.txt"
            config.write_text("model: fixed\n", encoding="utf-8")
            manifest.write_text("hashed-patient-ids\n", encoding="utf-8")
            token = "explicit-one-time-token"
            payload = {
                "status": "FROZEN",
                "primary_hypotheses_frozen": True,
                "models_frozen": True,
                "thresholds_frozen": True,
                "config_sha256": {"model.yaml": sha256_file(config)},
                "sealed_manifest_sha256": {"sealed.txt": sha256_file(manifest)},
                "test_unseal": {
                    "approved": True,
                    "approval_token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                },
            }
            freeze_path = root / "freeze.yaml"
            freeze_path.write_text(json.dumps(payload), encoding="utf-8")
            FreezeRecord.load(freeze_path).assert_locked_evaluation_allowed(token, root)
            with self.assertRaises(SealedTestError):
                FreezeRecord.load(freeze_path).assert_locked_evaluation_allowed("wrong", root)


if __name__ == "__main__":
    unittest.main()