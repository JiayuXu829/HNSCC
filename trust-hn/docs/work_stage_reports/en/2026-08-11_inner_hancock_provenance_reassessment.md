# Reassessment of inner_hancock Provenance and Manuscript Strategy

**Date:** 2026-08-11  
**Status:** Provenance conflict unresolved; frozen results and cohort type not relabeled

## 1. User statement

The user stated that `inner_hancock` is a private institutional HNSCC cohort and requested that all prior HANCOCK references be changed to `inner_hancock`, with a corresponding change in manuscript strategy.

## 2. Workspace findings

The following renamed directories are present:

- `data/raw/inner_hancock/`
- `data/interim/inner_hancock/`
- `data/interim/phase1_audit/inner_hancock/`
- `data/interim/phase2/inner_hancock/`
- `data/manifests/inner_hancock/`

However, the assets inside these directories remain traceable to the previously downloaded public HANCOCK resource:

1. `configs/phase1_sources.json` registers the assets as a pinned snapshot of the public GitHub repository `ankilab/HANCOCK_MultimodalDataset` and three files from the FAU public data portal.
2. `data/raw/inner_hancock/*.receipt.json` still records public source URLs, retrieval timestamps, the former `data/raw/hancock/...` paths, and SHA-256 hashes.
3. SHA-256 values recomputed for all four ZIP files in `data/raw/inner_hancock/` exactly match their public-download receipts.
4. The extracted tree contains the public HANCOCK repository name, official split files, and public structured-data files.
5. The timestamp and analysis continuity of `data/interim/phase2/inner_hancock/adapter_records.csv` match the existing Phase 2 workflow; no newly ingested institutional raw dataset or institutional manifest was found.
6. Git currently shows deletion of the former HANCOCK manifest and license note, without a replacement institutional provenance manifest. Deleting provenance records does not change the origin of the data.

The machine-readable evidence therefore indicates that `inner_hancock` is currently a renamed copy of the public HANCOCK assets, not a separately ingested and reanalyzed institutional patient cohort.

## 3. Changes deliberately not made

To avoid research provenance misrepresentation, this reassessment did not:

- relabel existing HANCOCK numerical results as private institutional results;
- globally replace HANCOCK in frozen Phase 2–7 configurations, results, figures, or receipts;
- remove public URLs, licenses, citation requirements, or acquisition hashes;
- describe a held-out/OOD test automatically as external or prospective institutional validation;
- reuse public HANCOCK numerical results as evidence from a single-center private cohort.

## 4. Conditional manuscript strategy

If a genuine institutional cohort is subsequently connected, the manuscript can be revised as follows:

1. Use `inner_hancock` as the canonical code identifier and the neutral display name **Institutional HNSCC cohort** in the manuscript.
2. Describe it as a retrospective institutional cohort unless a documented prospective protocol exists.
3. If training and test patients originate from the same institution, call the evaluation internal held-out validation rather than external validation.
4. Retain RADCURE, TCGA-HNSC, GSE65858, and GSE41613 as public cross-cohort, cross-modality, or cross-platform evidence.
5. Add ethics approval or waiver, consent handling, accrual period, eligibility criteria, endpoint definition, follow-up cutoff, de-identification, and restricted-access rationale to Methods.
6. Distinguish public datasets from the privacy/ethics-restricted institutional cohort in the Data Availability statement.
7. Rerun every affected Phase 2–7 analysis with the genuine institutional data and generate new results, figures, and receipts; existing public HANCOCK numbers cannot be inherited.

## 5. Minimum material needed to resolve the conflict

No names, medical-record numbers, or direct patient identifiers should be provided in chat. The workspace only needs either:

- the controlled path containing the genuine institutional dataset; or
- a de-identified institutional manifest/schema listing filenames, sample size, modalities, accrual period, endpoint fields, and split design.

Recommended path:

```text
data/private/inner_hancock/
```

This path should be Git-ignored and kept separate from the existing public HANCOCK assets.

## 6. Current conclusion

Until genuine institutional data or an auditable institutional manifest is connected, the existing results associated with the current `inner_hancock` directory cannot be reported as private institutional data. `inner_hancock` may be reserved as a future canonical identifier, but historical public HANCOCK results and provenance must remain intact and cannot be transformed by string replacement.
