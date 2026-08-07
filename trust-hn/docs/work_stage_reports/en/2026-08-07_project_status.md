# TRUST-HN Project Status

**Last updated:** 2026-08-07  
**Current gate:** BLOCKED at Phase 1; acquisition awaits explicit network/download approval from the user.  
**Sealed test touched:** No.

## Phase status

| Phase | Status | Evidence / decision |
|---|---|---|
| 0. Repository and governance | Complete | Governance, configuration, templates, and sealed-test refusal are implemented. |
| 1. Data acquisition and feasibility audit | Blocked | Allowlist downloader, GDC metadata query, tabular profiler, audit specs, and audit bundles are ready; source artifacts cannot be downloaded without explicit approval. |
| 2. Unified adapters and descriptive analysis | Not authorized | Requires Phase 1 go/no-go review. |
| 3. Baselines | Not authorized | Requires approved data flow and endpoint audit. |
| 4. TRUST-HN core | Not authorized | Requires baseline review. |
| 5. Stress tests and freeze | Not authorized | Not started. |
| 6. Locked/external tests | Sealed | Must remain unavailable until analysis freeze and explicit approval. |
| 7. Paper | Skeleton only | Results text must remain placeholder until real analyses are complete. |
| 8. Reproduction/submission | Not started | Not started. |

## Verification snapshot

- 26 standard-library tests pass on Python 3.11.8.
- AST syntax parsing passes for all 35 Python files.
- Draft locked-test invocation is rejected because the analysis is not frozen.
- No source dataset or patient outcome table has been downloaded or inspected locally.

## Decisions fixed at project start

- Repository root: `D:\medical_paper\HNSCC\trust-hn`.
- Data storage: only inside this repository; large/raw data are Git-ignored.
- Target runtime: Python 3.11.
- Fixed development seeds: `17, 29, 43, 71, 101`.
- Primary automatic coverage targets: 90% and 80%.
- RADCURE raw CT and HANCOCK raw WSI will not be downloaded.
- No test outcomes will be used for preprocessing, feature selection, hyperparameter selection, calibration, or gate thresholds.

## Immediate blockers

1. The usable bundled Python 3.11.8 lacks `venv` and scientific dependencies.
2. Project-local Python/uv installation requires an explicitly approved, pinned download.
3. Dataset acquisition requires network permission and artifact-level license verification.

## Next checkpoint

Install a project-local Python environment and acquire only allowed Phase 1 artifacts. Produce one complete audit bundle per study and stop for go/no-go review before any modeling.
## Blocked audit

The same external-state blocker has persisted for three consecutive goal turns: project-local runtime and public dataset downloads require explicit user approval, and no approval response has been received. Phase 1 cannot be scientifically completed from metadata templates alone. Work must resume from official artifact acquisition; bypassing the gate or fabricating audit results is prohibited.