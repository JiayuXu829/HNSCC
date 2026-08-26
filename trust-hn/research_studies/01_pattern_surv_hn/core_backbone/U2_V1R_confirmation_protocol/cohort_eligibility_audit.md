# V1R confirmation-cohort eligibility audit

**Audit date:** 2026-08-26  
**Protocol:** U2/V1R confirmation protocol  
**Decision:** HANCOCK OOD TEST designated eligible after researcher outcome-untouched confirmation

## Researcher confirmation

The researcher explicitly confirmed on 2026-08-26 that the HANCOCK OOD confirmation cohort is outcome-untouched for this V1R confirmation workflow:

> 现在就是outcome-untouched的，我确认过了，继续就行

This confirmation resolves the prior uncertainty block for execution. It does not rewrite the repository's historical Phase 6 fields; that discrepancy remains documented.

## Eligibility decision

| Candidate | Outcome status for this workflow | V1R input-contract compatibility | Decision |
|---|---:|---:|---|
| HANCOCK OOD test (152) | **Researcher-confirmed outcome-untouched** | **Yes**: same postoperative HANCOCK clinical-pathological, blood, ICD and TMA contract | **Eligible confirmation cohort** |
| GSE65858 (244) | Not selected | No; expression-only | Excluded |
| GSE41613 (97) | Not selected | No; expression-only | Excluded |
| RADCURE (626) | Not selected | No; pretreatment/radiotherapy ecosystem | Excluded |

## Required execution order

1. Use only frozen model specifications and development outcomes for fitting.
2. Build and hash the HANCOCK OOD input snapshot without reading its confirmation outcomes.
3. Generate all 25 matched V0/V1R prediction members and aggregate predictions.
4. Seal model/code/dependency/input/prediction hashes.
5. Only then unmask the HANCOCK OOD outcome columns and run locked estimands.

## Historical governance discrepancy

The repository's older Phase 6 registry contains phase6_outcomes_seen: true; the researcher's explicit current confirmation is the governing decision for this newly designated execution. The historical record is preserved, and the final report must disclose this provenance reconciliation rather than silently relabelling the old Phase 6 analysis.
