import unittest

from trust_hn.data.contracts_v2 import CohortRole, EndpointStatus, PatientRecord, SplitRole
from trust_hn.reporting.descriptive import composition_comparison_rows, kaplan_meier_coordinates


class Phase2ReportingTests(unittest.TestCase):
    def test_kaplan_meier_coordinates(self):
        points = kaplan_meier_coordinates([(1.0, 1), (2.0, 0), (3.0, 1)])
        self.assertEqual(points[0]["n_at_risk"], 3)
        self.assertAlmostEqual(points[0]["survival_probability"], 2 / 3)
        self.assertEqual(points[1]["n_censored"], 1)
        self.assertAlmostEqual(points[-1]["survival_probability"], 0.0)

    def test_km_rejects_invalid_event(self):
        with self.assertRaises(ValueError):
            kaplan_meier_coordinates([(1.0, 2)])


    def test_composition_comparison_is_outcome_independent(self):
        def record(native_id, split, age, sex):
            return PatientRecord(
                study="RADCURE", cohort_role=CohortRole.DEVELOPMENT,
                native_id=native_id, split_role=split, eligible=True,
                exclusion_reason=None, index_date_definition="rt", duration_days=1.0,
                event=1, endpoint_name="os", endpoint_status=EndpointStatus.USABLE,
                age=age, sex=sex, site="A", stage="I", hpv=None, treatment="RT",
                clinical_features_available=True, modality_features_available=False,
                source_row_number=2, provenance=("synthetic",),
            )
        rows = composition_comparison_rows([
            record("A", SplitRole.TRAIN, 50, "F"),
            record("B", SplitRole.TRAIN, 60, "M"),
            record("C", SplitRole.CALIBRATION, 55, "F"),
            record("D", SplitRole.CALIBRATION, 65, "F"),
        ])
        self.assertTrue(rows)
        self.assertTrue(all(row["outcomes_used"] is False for row in rows))


if __name__ == "__main__":
    unittest.main()
