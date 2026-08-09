from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from trust_hn.data.phase6_data import (
    CohortFeatures,
    _aggregate_probes,
    _first_gene_symbol,
    _read_geo_table,
    _within_sample_ranks,
    load_geo_features,
    load_radcure_features,
    ordered_id_digest,
    verify_frozen_cohort_manifest,
)


class Phase6DataUnitTests(unittest.TestCase):
    def test_ordered_digest_is_order_invariant_but_content_sensitive(self) -> None:
        self.assertEqual(ordered_id_digest(["b", "a"]), ordered_id_digest(["a", "b"]))
        self.assertNotEqual(ordered_id_digest(["a", "b"]), ordered_id_digest(["a", "c"]))

    def test_gene_symbol_mapping_is_deterministic(self) -> None:
        self.assertEqual(_first_gene_symbol(" mir4640///DDR1 "), "MIR4640")
        self.assertEqual(_first_gene_symbol("tp53; WRAP53"), "TP53")
        self.assertIsNone(_first_gene_symbol(pd.NA))
        self.assertIsNone(_first_gene_symbol("---"))

    def test_geo_table_parser_reads_expression_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.txt"
            path.write_text(
                '!Sample_characteristics_ch1\t"os: 10"\t"os: 20"\n'
                "!series_matrix_table_begin\n"
                '"ID_REF"\t"S2"\t"S1"\n'
                '"p1"\t1.0\t2.0\n'
                '"p2"\t3.0\t4.0\n'
                "!series_matrix_table_end\n",
                encoding="utf-8",
            )
            probes, ids, matrix = _read_geo_table(path)
            np.testing.assert_array_equal(probes, ["p1", "p2"])
            np.testing.assert_array_equal(ids, ["S2", "S1"])
            np.testing.assert_allclose(matrix, [[1.0, 2.0], [3.0, 4.0]])

    def test_probe_aggregation_uses_median_and_uppercase_symbol(self) -> None:
        probes = np.asarray(["p1", "p2", "p3"])
        ids = np.asarray(["s1", "s2"])
        matrix = np.asarray([[1, 2], [3, 4], [8, 10]], dtype=np.float32)
        result = _aggregate_probes(
            probes,
            ids,
            matrix,
            {"p1": "TP53", "p2": "TP53", "p3": "EGFR"},
        )
        self.assertEqual(result.columns.tolist(), ["EGFR", "TP53"])
        np.testing.assert_allclose(result.loc["s1"], [8.0, 2.0])
        np.testing.assert_allclose(result.loc["s2"], [10.0, 3.0])

    def test_within_sample_ranks_do_not_use_outcomes(self) -> None:
        frame = pd.DataFrame([[3.0, 1.0, 2.0], [2.0, 2.0, 1.0]])
        ranks = _within_sample_ranks(frame)
        np.testing.assert_allclose(ranks[0], [1.0, 1 / 3, 2 / 3])
        np.testing.assert_allclose(ranks[1], [5 / 6, 5 / 6, 1 / 3])

    def test_feature_container_rejects_outcome_columns(self) -> None:
        with self.assertRaisesRegex(ValueError, "outcome columns"):
            CohortFeatures(
                "TEST",
                "test",
                np.asarray(["a"]),
                pd.DataFrame({"event": [1]}),
                pd.DataFrame({"x": [1.0]}),
            )


class Phase6DataIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]

    def test_frozen_manifest_counts_and_digests_match(self) -> None:
        rows = verify_frozen_cohort_manifest(self.root)
        self.assertEqual({row["patient_count"] for row in rows}, {626, 152, 244, 97})

    def test_radcure_missing_radiomics_rows_are_retained(self) -> None:
        cohort = load_radcure_features(self.root)
        self.assertEqual(len(cohort.ids), 626)
        self.assertEqual(int(cohort.modality.isna().all(axis=1).sum()), 32)
        self.assertFalse(set(map(str.casefold, cohort.clinical.columns)) & {"event", "status"})

    def test_geo_feature_cache_is_aligned_and_outcome_free(self) -> None:
        expected = {"GSE65858": 244, "GSE41613": 97}
        for name, count in expected.items():
            cohort = load_geo_features(self.root, name)
            self.assertEqual(len(cohort.ids), count)
            self.assertEqual(cohort.modality.shape[1], 14417)
            self.assertFalse(
                set(map(str.casefold, cohort.clinical.columns))
                & {"os", "os_event", "fu time", "vital", "event", "duration_days"}
            )


if __name__ == "__main__":
    unittest.main()
