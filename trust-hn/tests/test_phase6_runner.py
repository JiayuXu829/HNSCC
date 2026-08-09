from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from trust_hn.evaluation.phase6_runner import (
    _load_preflight_receipt,
    _profile_coverages,
    _read_prediction,
    prediction_path,
)
from trust_hn.governance import SealedTestError
from trust_hn.utils.hashing import sha256_file


class Phase6RunnerTests(unittest.TestCase):
    def test_profile_parsing_and_prediction_path_are_deterministic(self) -> None:
        config = {
            "primary_gate_profile": "full_equal_weight_90",
            "sensitivity_gate_profiles": ["full_equal_weight_80", "full_equal_weight_100"],
        }
        self.assertEqual(_profile_coverages(config), (0.8, 0.9, 1.0))
        path = prediction_path(
            Path("root"), "RADCURE", assay="shuffled_full", profile="90"
        )
        self.assertEqual(
            path.as_posix(),
            "root/results/predictions/phase6/radcure__shuffled_full__aggregate90.csv",
        )

    def test_preflight_receipt_verifies_prediction_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prediction = root / "results/predictions/phase6/example.csv"
            prediction.parent.mkdir(parents=True)
            prediction.write_text("native_id,b2_risk\np1,0.2\n", encoding="utf-8")
            receipt = root / "results/manifests/phase6_preunseal_prediction_receipt.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(
                json.dumps(
                    {
                        "status": "COMPLETE",
                        "outcomes_loaded": False,
                        "prediction_file_sha256": {
                            "results/predictions/phase6/example.csv": sha256_file(prediction)
                        },
                    }
                ),
                encoding="utf-8",
            )
            _load_preflight_receipt(root)
            prediction.write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(SealedTestError):
                _load_preflight_receipt(root)

    def test_prediction_loading_requires_exact_id_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = prediction_path(root, "GSE65858", profile="90")
            path.parent.mkdir(parents=True)
            pd.DataFrame(
                {
                    "native_id": ["a", "b"],
                    "cohort": ["GSE65858"] * 2,
                    "assay": ["original"] * 2,
                    "gate_profile": ["90"] * 2,
                    "b2_score": [0.1, 0.2],
                }
            ).to_csv(path, index=False)
            loaded = _read_prediction(root, "GSE65858", ["a", "b"])
            self.assertEqual(loaded["b2_score"].tolist(), [0.1, 0.2])
            with self.assertRaises(ValueError):
                _read_prediction(root, "GSE65858", ["b", "a"])


if __name__ == "__main__":
    unittest.main()
