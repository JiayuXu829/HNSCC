# TRUST-HN

TRUST-HN is a resource-efficient reliability framework for prognosis in head and neck cancer. It evaluates whether an additional modality should **augment** a clinical anchor, whether the system should **fallback** to the clinical anchor, or whether it should **abstain** under unreliable clinical input.

## Current scope

The repository is being implemented phase by phase from `../docs/TRUST_HN_master_project_implementation.md`.

- **Phase 0:** repository, governance, reproducible configuration, audit templates, synthetic tests, and sealed-test protection.
- **Phase 1:** completed acquisition/registration and feasibility audit of authorized public artifacts.
- **Phase 2:** completed unified adapters, frozen data contract, and governance-safe descriptive outputs.
- **Phase 3:** completed development-only baselines within the authorized conditional scope.
- **Phase 4:** completed B6 stacked residual fusion and B7 reliability gating for HANCOCK and TCGA-HNSC within the authorized conditional scope; Phase 5 is not authorized, and RADCURE modality-dependent TRUST-HN remains blocked pending ORCESTRA RDS structural validation.
- Raw RADCURE CT and HANCOCK WSI are explicitly out of scope.
- No locked/sealed outcomes may be inspected for tuning.

## Layout

- `configs/`: versioned study and experiment configuration.
- `data/raw/`: immutable downloaded source files; never committed.
- `data/manifests/`: checksums, provenance, and sealed patient identifiers.
- `docs/audits/`: endpoint, split, leakage, missingness, cohort-flow, and license audits.
- `src/trust_hn/`: authoritative package code.
- `scripts/`: command-line entry points.
- `results/`: generated outputs; patient-level predictions remain untracked.
- `paper/`: manuscript sources linked to the Springer Nature template in the workspace root.


## Work-stage reports / 工作阶段报告

Dated English reports and faithful Simplified Chinese translations are stored and indexed under `docs/work_stage_reports/`.

带日期的英文报告及其忠实简体中文译本统一保存并索引于 `docs/work_stage_reports/`。

## Bootstrap (Windows PowerShell)

A Python 3.11 interpreter is required. Once available:

```powershell
cd trust-hn
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\scripts\test.ps1
```

The reproducible full analysis environment is also specified by `environment.yml`.

## Tests

```powershell
.\scripts\test.ps1
```

The full test suite covers governance, data contracts and adapters, censoring/IPCW metrics, patient-level split isolation, baseline and residual-fusion models, reliability gating, deterministic hashing, and sealed-test refusal.

## Data governance

1. Public data are downloaded only into `data/raw/<study>/`.
2. Every source file must be recorded with URL/accession, retrieval date, license notes, byte size, and SHA-256.
3. Patient identifiers used for locked tests are stored only as hashes in a sealed manifest.
4. Preprocessing, feature selection, calibration, and thresholds are fit without locked-test data.
5. `scripts/evaluate_locked_test.py` refuses execution unless an immutable analysis-freeze record, matching config hashes, and an explicit approval token are present.
6. Data and patient-level predictions are never committed to Git.

## Scientific boundary

The three studies validate a shared reliability principle; they are not merged into one patient table and do not imply one universally shared HNSCC model. All analyses are retrospective and public-data based. Fallback/abstention outputs are risk-communication mechanisms, not treatment advice.
## Phase 1 audit commands

All acquisition commands pass through `configs/download_policy.json`, which rejects non-HTTPS hosts, unapproved artifact roles, raw CT/WSI/TMA roles, oversized files, and destinations outside `data/raw`.

Profile a verified delimited patient table without making semantic guesses:

```powershell
$env:PYTHONPATH = "$PWD\src"
python scripts/profile_table.py `
  --table data/interim/radcure/patient_table.csv `
  --spec configs/audit_specs/radcure.json `
  --output-dir docs/audits/radcure/generated
```

The profiler generates an automatic dictionary, split-wise missingness, exact field-resolution record, endpoint/split summary, and warnings. Population meaning, index date, units, and clinical availability still require manual audit.

Query the frozen open-access TCGA-HNSC GDC metadata manifest:

```powershell
python scripts/query_gdc_metadata.py `
  --query configs/gdc_tcga_hnsc_star_counts_query.json `
  --output-json data/manifests/tcga_hnsc_star_counts_response.json `
  --output-tsv data/manifests/tcga_hnsc_star_counts_manifest.tsv
```

Network commands are not run until explicitly approved. Query output does not authorize downloading controlled-access files or inspecting external outcomes for model selection.

## Phase 2 command

Generate unified patient records in the Git-ignored interim area and aggregate-only descriptive outputs:

```powershell
python scripts/build_dataset.py --phase phase2
```

The command does not expose test/external outcomes and does not implement any Phase 3 model.
## Phase 3 command

Run all authorized development-only baseline experiments:

```powershell
.venv\Scripts\python.exe scripts\train_baselines.py --phase phase3
```

This command writes patient-level OOF/calibration predictions only to Git-ignored `results/predictions/phase3/` and writes aggregate metrics, figures, audits, and a hashed receipt to tracked locations. It refuses Phase 4 and does not load RADCURE challenge-test, HANCOCK OOD-test, or GEO external outcomes. RADCURE B4/B5/N0 remain governance-blocked until the ORCESTRA RDS structure is validated.

## Phase 4 command

Run the authorized development-only TRUST-HN core experiment:

```powershell
.venv\Scripts\python.exe scripts\train_trust_hn.py --phase phase4
```

This command fits B6 stacked residual fusion and B7 reliability gating on frozen HANCOCK and TCGA-HNSC training/calibration rows. Patient-level decision traces are written only to Git-ignored `results/predictions/phase4/`; aggregate metrics, figures, audits, and a hashed receipt are written to tracked locations. It does not enter Phase 5 and does not load RADCURE challenge-test, HANCOCK OOD-test, GSE65858, or GSE41613 outcomes. RADCURE B6/B7 remain governance-blocked until the ORCESTRA RDS structure is validated.
