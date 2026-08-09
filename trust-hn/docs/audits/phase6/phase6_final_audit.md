# TRUST-HN Phase 6 Final Audit

**Audit date:** 2026-08-08  
**State audited:** `CONSUMED_FOR_LOCKED_EVALUATION`  
**Scope:** Post-unseal integrity, aggregate-output reproducibility, privacy, ignore rules, tests and lint.  
**Decision:** PASS with one documented state-transition test limitation and historical repository-wide lint debt.

## 1. Frozen-file integrity

`FreezeRecord._assert_hashes` was run against the current project root using the registered `config_sha256` and `sealed_manifest_sha256` maps.

- Registered configuration/decision hashes checked: **32**
- Registered sealed manifest hashes checked: **1**
- Result: **PASS**

The Phase 6 registered decision files were not modified while preparing reports, checklists, manuscript text or this audit.

## 2. Aggregate-output hashes

Every path in `results/manifests/phase6_locked_evaluation_receipt.json` under `aggregate_output_sha256` was re-hashed with SHA-256.

- Aggregate metric/figure files checked: **10**
- Missing files: **0**
- Hash mismatches: **0**
- Result: **PASS**

## 3. Authorization-token privacy

The plaintext token was read only inside the local audit process from the ignored runtime file and was not printed. `assert_token_absent_from_tracked_files` completed without detecting a plaintext copy.

- Plaintext-token leakage into non-ignored project text: **not detected**
- Result: **PASS**

The token hash may appear in governance receipts; the token itself must remain secret.

## 4. Patient-identifier privacy and ignore rules

Aggregate Phase 6 CSV headers were scanned for patient/native/sample/subject/case identifier fields and contents were scanned for recognizable TCGA, GEO and RADCURE-style patient identifiers.

- Forbidden identifier columns detected: **0**
- Recognizable patient/sample identifiers detected in aggregate metric tables: **0**
- Patient-level prediction files present: **48**
- Patient-level files confirmed Git-ignored: **48/48**
- Result: **PASS**

Tracked/intended-tracked outputs contain cohort-level counts, metrics, confidence intervals, hashes and figures only.

## 5. Test verification

### 5.1 Historical implementation checkpoint

Before/at the Phase 6 implementation and evaluation checkpoint, the full repository suite had **90 passing tests**.

### 5.2 Post-consumption final audit

Running the unchanged full suite after the legitimate one-time state transition produced:

```text
1 failed, 89 passed
```

The sole failure was:

```text
tests/test_phase6_statistics.py::Phase6StatisticsTests::test_outcomes_refuse_access_before_consumption
```

This registered pre-consumption test intentionally expects outcome access to be refused. The current frozen state records `phase6_outcomes_seen=true` and `test_unseal.consumed=true`; therefore access proceeds to ID alignment and the test's synthetic ID (`secret`) raises a missing-outcome `ValueError` rather than the formerly expected `PermissionError`. Editing the registered test after outcomes were seen would invalidate the frozen hash, so it was not changed.

Verification performed instead:

- All other tests: **89 passed, 1 deselected**.
- A temporary, non-project copy of the freeze state was changed to pre-consumption solely to call the access guard; it correctly raised `PermissionError`.
- Pre-consumption refusal simulation: **PASS**.

Interpretation: this is a **state-dependent test obsolescence after authorized consumption**, not a Phase 6 model/evaluation failure. It should be replaced by separate pre- and post-consumption test fixtures only in a future governance version that explicitly permits a new hash freeze; the current registered test must remain unchanged.

## 6. Ruff verification

Ruff was run in check-only, no-cache mode on the registered Phase 6 Python implementation and test files.

- Phase 6 Python Ruff: **All checks passed**

JSON, TOML and YAML decision files were validated through their native parsers/workflow and frozen hashes rather than being passed to Ruff as Python source.

Repository-wide Ruff produced **267 historical findings** in older code:

| Code | Count |
|---|---:|
| E501 | 167 |
| E702 | 51 |
| UP035 | 13 |
| UP017 | 10 |
| E701 | 8 |
| I001 | 7 |
| F401 | 4 |
| Other | 7 |

These findings predate the current Phase 6 documentation work. No `--fix` operation was used because broad automatic changes could modify frozen earlier-phase code.

## 7. Documentation and manuscript deliverables

Created or expanded after the locked evaluation:

- `docs/work_stage_reports/en/2026-08-08_phase6_report.md`
- `docs/work_stage_reports/zh-CN/2026-08-08_phase6_report.md`
- `docs/checklists/en/TRIPOD_AI_self_assessment.md`
- `docs/checklists/zh-CN/TRIPOD_AI_self_assessment.md`
- `docs/checklists/en/PROBAST_AI_self_assessment.md`
- `docs/checklists/zh-CN/PROBAST_AI_self_assessment.md`
- `paper/manuscript.md`
- `paper/supplement.md`
- `paper/figure_legends.md`
- `PROJECT_STATUS.md`

The documents preserve negative findings, distinguish selective from full-cohort metrics and explicitly reject prospective, deployment and clinical-utility overclaims.

## 8. Final audit conclusion

The Phase 6 locked/external evaluation artifacts are intact and traceable. Registered hashes and aggregate receipt hashes match; patient-level predictions remain ignored; no plaintext token or patient identifiers were detected in aggregate outputs; and Phase 6 Python lint passes. The only test-suite exception is the expected incompatibility of a frozen pre-consumption refusal test with the now-consumed authorization state. No registered decision file was altered to hide or bypass that fact.
