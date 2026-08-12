from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1]
ROOT = HERE.parents[3]
PM = PROJECT / "project_management"

COHORTS = PM / "cohort_dictionary.csv"
METHODS = PM / "method_dictionary.csv"
ENDPOINTS = PM / "endpoint_variable_dictionary.md"
TERMS = PM / "terminology_style_guide.md"
NUMERIC = PM / "numeric_reporting_standard.md"
REPORT = PM / "WP3_completion_report_zh-CN.md"
README = PROJECT / "README.md"
REQUIRED = [COHORTS, METHODS, ENDPOINTS, TERMS, NUMERIC, REPORT, README]

EXPECTED_COHORTS = [
    "RADCURE",
    "HANCOCK",
    "TCGA-HNSC",
    "GSE65858",
    "GSE41613",
    "inner_hancock",
]
EXPECTED_METHODS = [*[f"B{i}" for i in range(8)], "M0", "N0", *[f"C{i}" for i in range(1, 5)]]
ALLOWED_PROJECT_PATHS = {
    "README.md",
    "project_management/cohort_dictionary.csv",
    "project_management/method_dictionary.csv",
    "project_management/endpoint_variable_dictionary.md",
    "project_management/terminology_style_guide.md",
    "project_management/numeric_reporting_standard.md",
    "project_management/WP3_completion_report_zh-CN.md",
    "tools/validate_wp3.py",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require_terms(text: str, terms: list[str], label: str, errors: list[str]) -> None:
    low = text.lower()
    for term in terms:
        if term.lower() not in low:
            errors.append(f"{label} missing required term: {term}")


def git_status(errors: list[str], warnings: list[str]) -> None:
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        git_root = Path(top.stdout.strip())
        project_prefix = PROJECT.relative_to(git_root).as_posix() + "/"
        proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=git_root,
            text=True,
            capture_output=True,
            check=True,
        )
        outside: list[str] = []
        unexpected: list[str] = []
        for line in proc.stdout.splitlines():
            path = line[3:].strip().strip('"').replace("\\", "/")
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if not path:
                continue
            if not path.startswith(project_prefix):
                outside.append(line)
                continue
            local = path[len(project_prefix) :]
            if local not in ALLOWED_PROJECT_PATHS:
                unexpected.append(line)
        if outside:
            errors.append("modified/untracked files outside manuscript project: " + " | ".join(outside))
        if unexpected:
            errors.append("WP3 changed files outside its allowed write set: " + " | ".join(unexpected))
    except Exception as exc:  # pragma: no cover - environment guard
        warnings.append(f"git boundary check unavailable: {exc}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing required WP3 file: {path}")
    if errors:
        return finish(errors, warnings, 0, 0)

    cohort_rows = rows(COHORTS)
    method_rows = rows(METHODS)
    # Encoding integrity: literal replacement markers are not valid dictionary content.
    for dictionary_path, dictionary_rows in [(COHORTS, cohort_rows), (METHODS, method_rows)]:
        for row_number, row in enumerate(dictionary_rows, start=2):
            for field, value in row.items():
                if value and ("?" in value or "\ufffd" in value):
                    errors.append(
                        f"{dictionary_path.name}:{row_number} field {field} contains an encoding replacement marker"
                    )

    endpoint_text = read(ENDPOINTS)
    term_text = read(TERMS)
    numeric_text = read(NUMERIC)
    report_text = read(REPORT)
    readme_text = read(README)

    # Cohort dictionary: exact, unique codes and binding manuscript roles.
    cohort_codes = [row.get("cohort_code", "") for row in cohort_rows]
    if cohort_codes != EXPECTED_COHORTS:
        errors.append(f"cohort codes/order differ from expected: {cohort_codes}")
    if len(set(cohort_codes)) != len(cohort_codes):
        errors.append("cohort dictionary has duplicate cohort codes")
    by_cohort = {row["cohort_code"]: row for row in cohort_rows}
    cohort_requirements = {
        "RADCURE": ["locked retrospective test", "626", "first radiotherapy fraction"],
        "HANCOCK": ["retrospective OOD test", "152", "diagnosis"],
        "TCGA-HNSC": ["development and calibration", "no independent Phase 6 test"],
        "GSE65858": ["cross-platform external test", "244"],
        "GSE41613": ["HPV-negative OSCC sensitivity analysis", "97"],
    }
    for code, required in cohort_requirements.items():
        text = " ".join(by_cohort[code].values()).lower()
        for value in required:
            if value.lower() not in text:
                errors.append(f"cohort {code} missing binding wording/value: {value}")
    inner = by_cohort.get("inner_hancock", {})
    inner_text = " ".join(inner.values()).lower()
    for phrase in [
        "known-overlap workflow and bias simulation",
        "not validation",
        "excluded_current_manuscript",
        "supplement only if separately approved",
    ]:
        if phrase not in inner_text:
            errors.append(f"inner_hancock boundary missing: {phrase}")
    for forbidden in ["independent validation", "private validation", "institutional validation"]:
        if forbidden not in inner.get("prohibited_wording", "").lower():
            errors.append(f"inner_hancock prohibited wording list missing: {forbidden}")

    # Method dictionary: exact method set and core scientific roles.
    method_codes = [row.get("method_code", "") for row in method_rows]
    if method_codes != EXPECTED_METHODS:
        errors.append(f"method codes/order differ from expected: {method_codes}")
    if len(set(method_codes)) != len(method_codes):
        errors.append("method dictionary has duplicate method codes")
    by_method = {row["method_code"]: row for row in method_rows}
    method_requirements = {
        "B0": ["kaplan", "constant-risk"],
        "B2": ["clinical anchor", "elastic-net cox"],
        "B5": ["forced-fusion", "direct concatenation"],
        "B6": ["stacked residual fusion", "cross-fitted b2"],
        "B7": ["reliability-gated selective prediction", "identical non-abstained subset", "coverage"],
        "M0": ["missingness-indicator-only"],
        "N0": ["outcome-independent permuted-modality"],
        "C1": ["gradient boosting survival analysis", "post hoc exploratory"],
        "C2": ["xgboost-cox", "post hoc exploratory"],
        "C3": ["late-fusion", "post hoc exploratory"],
        "C4": ["missing-aware", "post hoc exploratory"],
    }
    for code, required in method_requirements.items():
        text = " ".join(by_method[code].values()).lower()
        for value in required:
            if value.lower() not in text:
                errors.append(f"method {code} missing binding definition: {value}")
    for code in ["C1", "C2", "C3", "C4"]:
        if "phase 7 post hoc exploratory" not in " ".join(by_method[code].values()).lower():
            errors.append(f"{code} lacks Phase 7 post hoc exploratory governance label")

    # Endpoint/variable contract.
    require_terms(
        endpoint_text,
        [
            "24-month overall survival (24-month OS)",
            "730.5",
            "event_by_horizon",
            "event_free_at_horizon",
            "censored_before_horizon",
            "zero evaluation weight",
            "IPCW Brier score",
            "0.05",
            "2,000 patient-level paired bootstrap replicates",
            "1,000 patient-level paired bootstrap replicates",
            "20-model bootstrap ensemble",
            "not available",
            "not evaluated",
            "not applicable",
            "not estimable",
        ],
        ENDPOINTS.name,
        errors,
    )
    for code in EXPECTED_COHORTS:
        if code not in endpoint_text:
            errors.append(f"endpoint dictionary lacks cohort-specific boundary: {code}")

    # Terminology and prohibited-claim contract.
    require_terms(
        term_text,
        [
            "clinical anchor",
            "direct forced fusion",
            "stacked residual fusion",
            "reliability-aware gating",
            "selective prediction",
            "non-abstained coverage",
            "identical non-abstained subset",
            "AUGMENT",
            "FALLBACK",
            "ABSTAIN",
            "post hoc exploratory",
            "restricted retrospective HPV-negative OSCC sensitivity analysis",
            "known-overlap workflow and bias simulation; not validation",
            "prospective validation",
            "universal robustness",
            "clinical utility established",
            "deployable threshold",
            "patient benefit",
            "radiomics-specific biological signal",
        ],
        TERMS.name,
        errors,
    )
    if not re.search(r"Phase 8.*(?:Abstract|Introduction|Results|Discussion|Methods)", term_text, re.S):
        errors.append("terminology guide lacks explicit Phase 8 main-text exclusion")

    # Numeric contract and worked examples.
    require_terms(
        numeric_text,
        [
            "first-listed model minus the second-listed model",
            "negative IPCW Brier differences therefore favoured the first-listed model",
            "identical non-abstained subset",
            "evaluated n",
            "coverage",
            "100.0%",
            "Unicode minus",
            "paired metric difference",
            "not available",
            "not estimable",
            "post hoc exploratory",
            "+0.00382",
            "−0.00812",
            "+0.07294",
        ],
        NUMERIC.name,
        errors,
    )
    if "5 位小数" not in numeric_text or "4 位小数" not in numeric_text or "1 位小数" not in numeric_text:
        errors.append("numeric standard lacks explicit precision tiers")

    # Completion report/README state and WP boundary.
    require_terms(
        report_text,
        [
            "修改文件",
            "证据与数据来源",
            "验证命令",
            "剩余 TODO",
            "冻结资产",
            "允许声明",
            "禁止声明",
            "下一审查点",
        ],
        REPORT.name,
        errors,
    )
    if "WP3" not in readme_text or "validate_wp3.py" not in readme_text:
        errors.append("README does not expose WP3 status/validator")
    if "WP4" not in report_text or "未进入 WP4" not in report_text:
        errors.append("WP3 report lacks explicit stop-before-WP4 boundary")

    # No manuscript prose/template edits in this work package.
    for path in [PROJECT / "main.tex", PROJECT / "sections"]:
        if not path.exists():
            errors.append(f"expected manuscript baseline path missing: {path}")

    git_status(errors, warnings)
    return finish(errors, warnings, len(cohort_rows), len(method_rows))


def finish(errors: list[str], warnings: list[str], cohort_count: int, method_count: int) -> int:
    print(
        f"WP3 validation: cohorts={cohort_count}, methods={method_count}, "
        f"errors={len(errors)}, warnings={len(warnings)}"
    )
    for item in warnings:
        print("WARNING:", item)
    for item in errors:
        print("ERROR:", item)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

