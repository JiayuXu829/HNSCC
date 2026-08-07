# TRUST-HN Phase 2 completion report

**Date:** 2026-08-07
**Phase:** Unified adapters and governance-safe descriptive analysis
**Status:** Complete within the user-approved conditional scope; Phase 3 remains unauthorized.
**Contract:** `2.0 / FROZEN_FOR_PHASE2`

## 1. Authorized boundary

Authorized work: three dataset adapters; a unified/versioned patient contract; frozen cohort, endpoint, and split definitions; Table 1 candidates; missingness heatmap; development-only event and Kaplan–Meier summaries; and covariate-only train/calibration/test composition comparisons.

Not authorized or performed: Phase 3 baseline fitting, TRUST-HN training, feature/hyperparameter tuning, calibration fitting, reliability-gate threshold selection, or locked/external outcome evaluation.

Raw source tables containing held-out/external outcome columns were parsed as source files, and Phase 1 had already audited aggregate event counts. However, official test/external outcomes were not materialized in Phase 2 adapter records or tracked outputs and were not used for preprocessing, selection, tuning, calibration, thresholds, or model evaluation.

## 2. Implementation delivered

### Contract and governance

Created:

- `configs/phase2_contract.json`
- `configs/phase2_governance.json`
- `data/schemas/unified_patient_record.schema.json`
- `src/trust_hn/data/contracts_v2.py`

Protections include immutable records, duplicate/invalid-endpoint rejection, deterministic exact-size SHA-256 train/calibration splits based only on IDs, refusal of outcomes in sealed/external records, and public serialization without `native_id` or `source_row_number`.

### Adapters and orchestration

Created or updated:

- `src/trust_hn/data/adapters/__init__.py`
- `src/trust_hn/data/adapters/radcure.py`
- `src/trust_hn/data/adapters/hancock.py`
- `src/trust_hn/data/adapters/transcriptomics.py`
- `src/trust_hn/data/phase2.py`
- `src/trust_hn/reporting/descriptive.py`
- `scripts/build_dataset.py`
- `configs/radcure.yaml`, `configs/hancock.yaml`, `configs/tcga_geo.yaml`
- `PROJECT_STATUS.md`, `README.md`

Implemented classes: `RadcureAdapter`, `HancockAdapter`, and `TranscriptomicsAdapter`. The dataset CLI accepts only:

```powershell
python3.12 scripts\build_dataset.py --phase phase2
```

It has no Phase 3 modeling path.

### Tests

Created:

- `tests/test_phase2_contracts.py`
- `tests/test_phase2_adapters.py`
- `tests/test_phase2_reporting.py`

They cover contract immutability, sealed-outcome suppression, identifier removal, exact deterministic splitting, endpoint arithmetic, negative-duration rejection, cohort eligibility, month-to-day conversion, full adapter counts, Kaplan–Meier coordinates, and outcome-independent composition comparison.

## 3. Frozen cohort and endpoint decisions

| Study | Source/eligible | Development split | Sealed role | Frozen endpoint/population decision |
|---|---:|---:|---:|---|
| RADCURE | 3,346 / 2,144 | train 1,215; calibration 303 | challenge test 626 | Trimmed/case-folded exact `Squamous Cell Carcinoma`; OS = `Last FU - RT Start`, first RT fraction as origin. |
| HANCOCK | 763 / 763 | train 489; calibration 122 | OOD test 152 | Diagnosis to last information/death; `survival_status == deceased` is event 1. |
| TCGA-HNSC | 520 / 520 | train 416; calibration 104 | none in Phase 2 | 519 usable OS endpoints; one unresolved duration; dead uses max nonnegative `days_to_death`, alive uses max follow-up. |
| GSE65858 | 270 / 244 | none | external test 244 | `Primary AND distant_metastasis == 0 AND treatment != palliative`. |
| GSE41613 | 97 / 97 | none | sensitivity 97 | HPV-negative OSCC sensitivity cohort; source follow-up is months; `days = months x 30.4375`. |

Additional details:

- RADCURE exclusions: 498 non-primary histology and 704 outside the primary challenge split. All 3,346 `RT Start`/`Last FU` pairs are parseable and nonnegative. `Length FU` is diagnosis-origin and unused. One record has an aggregate 80-day `Date of Death` versus `Last FU` discrepancy; the adapter consistently uses source-defined `Last FU`.
- HANCOCK has 611 development records with usable endpoints.
- TCGA expression availability is represented lazily; no `520 x 60,664` modeling matrix was materialized.
- GSE65858 exclusions: not primary 16; distant metastasis 6; both 1; palliative treatment 3.
- GSE41613 is not treated as general HNSCC external validation. Source publication: Chen et al., *Clinical Cancer Research* 2013, PMCID `PMC3593802`, PMID `23319825`.

## 4. Outputs

Patient-level outputs exist only in Git-ignored locations:

```text
data/interim/phase2/{radcure,hancock,tcga_hnsc,gse65858,gse41613}/adapter_records.csv
```

Tracked aggregate outputs:

- `results/metrics/phase2/cohort_flow.csv`
- `results/metrics/phase2/table1_candidates.csv`
- `results/metrics/phase2/missingness_summary.csv`
- `results/metrics/phase2/event_summary_development_only.csv`
- `results/metrics/phase2/kaplan_meier_development_only.csv`
- `results/metrics/phase2/composition_comparison.csv`
- `results/figures/phase2/missingness_heatmap.svg`
- `results/figures/phase2/event_distribution.svg`
- `results/figures/phase2/kaplan_meier_development_only.svg`
- `docs/audits/phase2/endpoint_audit.md`
- `results/manifests/phase2_adapter_receipt.json`

The composition comparison uses covariates only (age standardized mean difference, missing-fraction differences, and categorical total-variation distance) and records `outcomes_used=False`.

## 5. Source versions and SHA-256

| Artifact/version | SHA-256 |
|---|---|
| RADCURE `v04_20241219/01_RADCURE_TCIA_Clinical_r2_offset.csv` | `18068176b5e92fbd57e4879610613ece6d123de3100be3016d22a3d5439eb8e0` |
| HANCOCK targets, Git `521b99b03a94008b28df5c3df4aa5f82aa14b25a` | `c6e8674cb304b1c90d3ea55570359e79ac2353b64ec201e1501726f558c08503` |
| HANCOCK TMA cell density, same snapshot | `fb2468d284e29a067d5d08793de5e52c48978410a0145671cd81381466d48b99` |
| HANCOCK official splits, same snapshot | `75b42a6dbd86207a4803629c3fe580cd18103c688595350abf13b1710ebc051f` |
| HANCOCK clinical JSON, same snapshot | `355a53661f8e9a6b36dd7a5d66a57b650cd34cd3b87cbf7c91b4806fe7949bb4` |
| HANCOCK pathological JSON, same snapshot | `9595b3427087bd4922147bf40321559f024c74d52b46c9c6a698c2751eaffaf5` |
| TCGA-HNSC GDC clinical response JSON | `df0d8bbd8345acdde6b2286252d07e3a605351fbeb8bb5fd77b1670e273aa72f` |
| TCGA-HNSC STAR-count manifest TSV | `68b36aea7b8c4befeeaf310de39ab6cb5f6f8832e5af8f24560326b75566a6dc` |
| GSE65858 GEO snapshot `geo_2026-06-03` | `88b303164882ee37fe85170eaf7a71a08781e6809ede640233883b30aad355cd` |
| GSE41613 GEO snapshot `geo_2026-07-06` | `92c9adea26af6e58fbbfc87f74ad46b9aee688cfdce11c2cc2df90f84940ee17` |

Contract hashes:

- `phase2_contract.json`: `8ce3633debeca7148c0e11a80bd582821f9a919a7bd3ec7b3bb9207f0ab56d40`
- `phase2_governance.json`: `ae489b5e9cb34ccd855107cf35936fcbcb9ab5a4d147e8aec3c9ee2c318cd952`
- unified JSON Schema: `3e76aa29862deade7d7e05f35bb036577d05ce79980f22383a749d737828405b`

All output hashes are enumerated in `results/manifests/phase2_adapter_receipt.json`.

## 6. Verification

Commands:

```powershell
$env:PYTHONPATH='src;.'
python3.12 -m unittest discover -s tests -v
python3.12 -m compileall -q src scripts tests
python3.12 scripts\build_dataset.py --phase phase2
git check-ignore -v data\interim\phase2\radcure\adapter_records.csv
git diff --check
```

Results:

- **45 tests passed**.
- Python compilation passed.
- Phase 2 build passed and regenerated the receipt.
- Patient-level files are Git-ignored.
- Tracked Phase 2 outputs/reports had zero RADCURE, TCGA, or GEO native-ID pattern hits.
- Tracked aggregate CSV headers contain none of `native_id`, `patient_id`, `sample_id`, or `source_row_number`.
- HANCOCK IDs are short numeric strings, so protection is structural through aggregate-only writers and forbidden ID columns.

## 7. Risks and Phase 3 gate

1. ORCESTRA RDS structure is not validated with R/Rscript or a validated parser; RADCURE radiomics modeling remains blocked.
2. One TCGA-HNSC case has unresolved OS duration and remains excluded from endpoint-dependent summaries.
3. The documented RADCURE 80-day date discrepancy remains resolved operationally by the frozen `Last FU` rule.
4. Cross-study covariate differences are descriptive and cannot justify external-outcome-guided harmonization.
5. Phase 2 establishes data readiness, not predictive performance, calibration, clinical utility, or reliability-gate validity.

**Recommendation: CONDITIONAL GO for Phase 3 clinical and expression baselines only, subject to explicit user authorization.**

**Recommendation: NO-GO for RADCURE radiomics baselines until ORCESTRA RDS structure is validated.**

Any Phase 3 authorization should cover baseline implementation and development-only validation, not TRUST-HN core training, sealed/external outcome access, final testing, or threshold selection using sealed cohorts.
