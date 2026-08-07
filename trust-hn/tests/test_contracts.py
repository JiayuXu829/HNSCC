import unittest

from trust_hn.data.contracts import (
    DataContractError,
    SurvivalRecord,
    assert_patient_splits_disjoint,
    assert_samples_do_not_cross_splits,
    validate_survival_records,
)


class ContractTests(unittest.TestCase):
    def test_disjoint_patient_splits_pass(self):
        assert_patient_splits_disjoint({"train": ["A", "B"], "test": ["C"]})

    def test_overlap_is_rejected(self):
        with self.assertRaises(DataContractError):
            assert_patient_splits_disjoint({"train": ["A"], "test": ["A"]})

    def test_multiple_samples_must_stay_together(self):
        with self.assertRaises(DataContractError):
            assert_samples_do_not_cross_splits(["A", "A"], ["train", "test"])

    def test_invalid_survival_values_are_rejected(self):
        with self.assertRaises(DataContractError):
            validate_survival_records([SurvivalRecord("A", -1, 0)])
        with self.assertRaises(DataContractError):
            validate_survival_records([SurvivalRecord("A", 1, 2)])


if __name__ == "__main__":
    unittest.main()