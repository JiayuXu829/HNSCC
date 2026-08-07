import unittest
from dataclasses import FrozenInstanceError

from trust_hn.data.contracts_v2 import (
    CohortRole,
    DataContractError,
    EndpointStatus,
    PatientRecord,
    SplitRole,
    deterministic_development_split,
    validate_patient_records,
)


class Phase2ContractTests(unittest.TestCase):
    def make_record(self, **overrides):
        values = {
            "study": "synthetic",
            "cohort_role": CohortRole.DEVELOPMENT,
            "native_id": "P001",
            "split_role": SplitRole.TRAIN,
            "eligible": True,
            "exclusion_reason": None,
            "index_date_definition": "diagnosis",
            "duration_days": 100.0,
            "event": 1,
            "endpoint_name": "overall_survival",
            "endpoint_status": EndpointStatus.USABLE,
            "age": 60.0,
            "sex": "male",
            "site": "oral cavity",
            "stage": "III",
            "hpv": None,
            "treatment": "surgery",
            "clinical_features_available": True,
            "modality_features_available": True,
            "source_row_number": 2,
            "provenance": ("synthetic.csv",),
        }
        values.update(overrides)
        return PatientRecord(**values)

    def test_patient_record_is_immutable(self):
        record = self.make_record()
        with self.assertRaises(FrozenInstanceError):
            record.age = 61.0

    def test_sealed_record_cannot_expose_outcome(self):
        record = self.make_record(
            cohort_role=CohortRole.HELD_OUT,
            split_role=SplitRole.SEALED_TEST,
            duration_days=100.0,
            event=1,
            endpoint_status=EndpointStatus.SEALED,
        )
        with self.assertRaises(DataContractError):
            validate_patient_records([record])

    def test_public_dict_omits_native_identifier(self):
        public = self.make_record().to_public_dict()
        self.assertNotIn("native_id", public)
        self.assertNotIn("source_row_number", public)

    def test_deterministic_split_is_exact_and_order_invariant(self):
        ids = [f"P{i:03d}" for i in range(10)]
        first = deterministic_development_split(ids, 0.2, "phase2-test")
        second = deterministic_development_split(reversed(ids), 0.2, "phase2-test")
        self.assertEqual(first, second)
        self.assertEqual(sum(role == SplitRole.CALIBRATION for role in first.values()), 2)
        self.assertEqual(sum(role == SplitRole.TRAIN for role in first.values()), 8)


if __name__ == "__main__":
    unittest.main()
