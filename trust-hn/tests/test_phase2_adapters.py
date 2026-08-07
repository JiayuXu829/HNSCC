import unittest
from pathlib import Path

from trust_hn.data.adapters.hancock import HancockAdapter
from trust_hn.data.adapters.radcure import RadcureAdapter, derive_treatment_start_os
from trust_hn.data.adapters.transcriptomics import (
    TranscriptomicsAdapter,
    gse41613_followup_days,
    gse65858_primary_eligibility,
)


class Phase2AdapterRuleTests(unittest.TestCase):
    def test_radcure_endpoint_uses_last_followup_minus_rt_start(self):
        duration, event = derive_treatment_start_os(
            rt_start="100", last_follow_up="465", status="Dead", date_of_death="465"
        )
        self.assertEqual(duration, 365.0)
        self.assertEqual(event, 1)

    def test_radcure_rejects_negative_treatment_start_duration(self):
        with self.assertRaises(ValueError):
            derive_treatment_start_os(
                rt_start="500", last_follow_up="465", status="Alive", date_of_death=""
            )

    def test_gse41613_month_conversion(self):
        self.assertAlmostEqual(gse41613_followup_days("12"), 365.25)

    def test_gse65858_primary_rule(self):
        self.assertTrue(gse65858_primary_eligibility("Primary", "0", "multi"))
        self.assertFalse(gse65858_primary_eligibility("Relapse", "0", "multi"))
        self.assertFalse(gse65858_primary_eligibility("Primary", "1", "multi"))
        self.assertFalse(gse65858_primary_eligibility("Primary", "0", "palliative"))

    def test_phase1_sources_are_present_for_integration(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (root / "data/interim/radcure/v04_20241219/clinical_csv/01_RADCURE_TCIA_Clinical_r2_offset.csv").exists()
        )
        self.assertTrue((root / "data/raw/tcga_hnsc/gdc_cases_clinical_response.json").exists())


class Phase2FullAdapterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]

    def test_radcure_counts_and_sealed_outcomes(self):
        records = RadcureAdapter(self.root).load_records()
        self.assertEqual(len(records), 3346)
        self.assertEqual(sum(record.eligible for record in records), 2144)
        sealed = [record for record in records if record.split_role.value == "sealed_test"]
        self.assertEqual(len(sealed), 626)
        self.assertTrue(all(record.duration_days is None and record.event is None for record in sealed))

    def test_hancock_counts_and_sealed_outcomes(self):
        records = HancockAdapter(self.root).load_records()
        self.assertEqual(len(records), 763)
        sealed = [record for record in records if record.split_role.value == "sealed_test"]
        self.assertEqual(len(sealed), 152)
        self.assertTrue(all(record.duration_days is None and record.event is None for record in sealed))

    def test_transcriptomics_population_and_external_sealing(self):
        records = TranscriptomicsAdapter(self.root).load_records()
        by_study = {}
        for study in {record.study for record in records}:
            by_study[study] = [record for record in records if record.study == study]
        self.assertEqual(len(by_study["TCGA-HNSC"]), 520)
        self.assertEqual(sum(record.eligible for record in by_study["GSE65858"]), 244)
        self.assertEqual(len(by_study["GSE41613"]), 97)
        external = by_study["GSE65858"] + by_study["GSE41613"]
        self.assertTrue(all(record.duration_days is None and record.event is None for record in external))


if __name__ == "__main__":
    unittest.main()
