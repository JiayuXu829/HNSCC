import unittest

from trust_hn.evaluation.endpoints import HorizonStatus, classify_horizon_outcome


class HorizonOutcomeTests(unittest.TestCase):
    def test_event_before_horizon_is_positive(self):
        result = classify_horizon_outcome(100, 1, 730.5)
        self.assertEqual(result.status, HorizonStatus.EVENT_BY_HORIZON)
        self.assertEqual(result.binary_label, 1)
        self.assertTrue(result.evaluable_as_binary)

    def test_event_after_horizon_is_negative_at_horizon(self):
        result = classify_horizon_outcome(900, 1, 730.5)
        self.assertEqual(result.status, HorizonStatus.EVENT_FREE_AT_HORIZON)
        self.assertEqual(result.binary_label, 0)

    def test_early_censoring_is_not_negative(self):
        result = classify_horizon_outcome(300, 0, 730.5)
        self.assertEqual(result.status, HorizonStatus.CENSORED_BEFORE_HORIZON)
        self.assertIsNone(result.binary_label)
        self.assertFalse(result.evaluable_as_binary)

    def test_observed_beyond_horizon_is_negative(self):
        result = classify_horizon_outcome(800, 0, 730.5)
        self.assertEqual(result.binary_label, 0)


if __name__ == "__main__":
    unittest.main()