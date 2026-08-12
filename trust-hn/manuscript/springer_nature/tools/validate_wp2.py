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

OUTLINE_ZH = PM / "paper_outline_zh-CN.md"
OUTLINE_EN = PM / "paper_outline_en.md"
ARGUMENT = PM / "argument_map.md"
CLAIM_ZH = PM / "claim_matrix_zh-CN.md"
EVIDENCE_MAP = PM / "evidence_map.csv"

REQUIRED = [OUTLINE_ZH, OUTLINE_EN, ARGUMENT, CLAIM_ZH, EVIDENCE_MAP]
EXPECTED_IDS = {
    "ABS": [f"ABS-{i:02d}" for i in range(1, 6)],
    "INT": [f"INT-{i:02d}" for i in range(1, 5)],
    "RES": [f"RES-{i:02d}" for i in range(1, 9)],
    "DIS": [f"DIS-{i:02d}" for i in range(1, 8)],
    "MET": [f"MET-{i:02d}" for i in range(1, 10)],
}
RESULT_FIELDS_ZH = [
    "????", "??ID", "?? evidence_id", "????", "????",
    "???", "???", "95%CI", "????", "???????/?????",
    "????", "??/??????",
]
RESULT_FIELDS_EN = [
    "Question answered", "Claim IDs", "Linked evidence_id values", "Cohort role",
    "Analysis nature", "Sample size", "Coverage", "95% CI", "Core interpretation",
    "Mandatory negative/limiting evidence", "Provisional display", "Destination",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def sections(text: str, prefix: str) -> dict[str, str]:
    pat = re.compile(rf"^###\s+({re.escape(prefix)}-\d{{2}})\b.*$", re.M)
    hits = list(pat.finditer(text))
    out: dict[str, str] = {}
    for i, hit in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        out[hit.group(1)] = text[hit.start():end]
    return out


def finish(errors: list[str], warnings: list[str], evidence_refs: int) -> int:
    print(f"WP2 validation: evidence_refs={evidence_refs}, errors={len(errors)}, warnings={len(warnings)}")
    for item in warnings:
        print("WARNING:", item)
    for item in errors:
        print("ERROR:", item)
    return 1 if errors else 0


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing required WP2/WP1 interface file: {path}")
    if errors:
        return finish(errors, warnings, 0)

    zh = read(OUTLINE_ZH)
    en = read(OUTLINE_EN)
    argument = read(ARGUMENT)
    claim_text = read(CLAIM_ZH)

    with EVIDENCE_MAP.open(encoding="utf-8-sig", newline="") as handle:
        evidence_rows = list(csv.DictReader(handle))
    evidence_ids = {row["evidence_id"] for row in evidence_rows}
    claim_ids = set(re.findall(r"^\|\s*(C\d{2})\s*\|", claim_text, re.M))
    if claim_ids != {f"C{i:02d}" for i in range(1, 21)}:
        errors.append(f"claim matrix IDs are incomplete/unexpected: {sorted(claim_ids)}")

    # Bilingual paragraph structure must be identical and complete.
    for prefix, expected in EXPECTED_IDS.items():
        z_ids = list(sections(zh, prefix))
        e_ids = list(sections(en, prefix))
        if z_ids != expected:
            errors.append(f"Chinese {prefix} paragraph IDs differ from expected: {z_ids}")
        if e_ids != expected:
            errors.append(f"English {prefix} paragraph IDs differ from expected: {e_ids}")
        if z_ids != e_ids:
            errors.append(f"bilingual {prefix} paragraph IDs/order differ")

    # Required Results fields and WP1 interface constraints.
    zres = sections(zh, "RES")
    eres = sections(en, "RES")
    for pid, block in zres.items():
        for field in RESULT_FIELDS_ZH:
            if f"**{field}?**" not in block:
                errors.append(f"{OUTLINE_ZH.name} {pid} missing field: {field}")
        if not re.search(r"\bC\d{2}\b", block):
            errors.append(f"{OUTLINE_ZH.name} {pid} has no claim ID")
        if not re.search(r"`(?:P\d|GOV)-", block):
            errors.append(f"{OUTLINE_ZH.name} {pid} has no linked evidence_id")
    for pid, block in eres.items():
        for field in RESULT_FIELDS_EN:
            if f"**{field}:**" not in block:
                errors.append(f"{OUTLINE_EN.name} {pid} missing field: {field}")
        if not re.search(r"\bC\d{2}\b", block):
            errors.append(f"{OUTLINE_EN.name} {pid} has no claim ID")
        if not re.search(r"`(?:P\d|GOV)-", block):
            errors.append(f"{OUTLINE_EN.name} {pid} has no linked evidence_id")

    # Validate every exact backticked evidence ID; allow documented wildcard prefixes/ranges.
    evidence_ref_count = 0
    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        for token in re.findall(r"`([^`]+)`", text):
            wildcard = token.endswith("*") and token[:-1].startswith(("P", "GOV"))
            candidates = re.findall(r"(?:GOV-ANCHOR-\d{3}|P\d-[A-Z]+(?:-[A-Z]+)*-R\d{3}(?:-[A-Z0-9-]+)?)", token)
            for ref in candidates:
                evidence_ref_count += 1
                if wildcard and token[:-1].startswith(ref):
                    continue
                if ref not in evidence_ids:
                    errors.append(f"{path.name}: unknown evidence_id {ref}")
            # A wildcard is acceptable only if at least one evidence ID has the prefix.
            if wildcard:
                prefix = token[:-1]
                if not any(eid.startswith(prefix) for eid in evidence_ids):
                    errors.append(f"{path.name}: wildcard evidence prefix has no match: {token}")

    # Validate every Cxx reference.
    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        for cid in sorted(set(re.findall(r"\bC\d{2}\b", text))):
            if cid not in claim_ids:
                errors.append(f"{path.name}: unknown claim ID {cid}")

    # Phase-specific governance language.
    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        lower = text.lower()
        if "phase 7" in lower and "post hoc exploratory" not in lower:
            errors.append(f"{path.name}: Phase 7 lacks post hoc exploratory label")
        if "phase 8" in lower:
            if "known-overlap" not in lower:
                errors.append(f"{path.name}: Phase 8 lacks known-overlap wording")
            if "not validation" not in lower and "??validation" not in lower:
                errors.append(f"{path.name}: Phase 8 lacks explicit not-validation wording")

    # Results-specific high-risk interfaces.
    for lang, result_map in [("zh", zres), ("en", eres)]:
        res04 = result_map.get("RES-04", "").lower()
        res05 = result_map.get("RES-05", "").lower()
        res07 = result_map.get("RES-07", "").lower()
        res08 = result_map.get("RES-08", "").lower()
        if "coverage" not in res04 and "???" not in res04:
            errors.append(f"{lang} RES-04 lacks B7 coverage")
        if not (("identical non-abstained subset" in res04) or ("???????" in res04)):
            errors.append(f"{lang} RES-04 lacks identical non-abstained-subset qualifier for B7 paired results")
        if not (("coverage" in res05) or ("???" in res05)):
            errors.append(f"{lang} RES-05 lacks coverage")
        if not (("identical non-abstained subset" in res05) or ("???????" in res05)):
            errors.append(f"{lang} RES-05 lacks identical non-abstained-subset wording")
        if "gse41613" not in res04 or "hpv-negative oscc" not in res04 and "hpv??oscc" not in res04:
            errors.append(f"{lang} RES-04 lacks GSE41613 HPV-negative OSCC boundary")
        if "sensitivity" not in res04 and "???" not in res04:
            errors.append(f"{lang} RES-04 lacks sensitivity-only wording")
        if not (("does not establish clinical utility" in res07) or ("????????" in res07)):
            errors.append(f"{lang} RES-07 lacks no-clinical-utility boundary")
        if "post hoc exploratory" not in res08:
            errors.append(f"{lang} RES-08 lacks post hoc exploratory label")

    # Argument and manuscript-level content requirements.
    required_argument_phrases = [
        "provisional titles", "primary research question", "contribution hierarchy",
        "main argument chain", "counterevidence", "threat-to-validity",
        "main-text versus supplement boundary", "paragraph-to-argument crosswalk",
    ]
    arg_lower = argument.lower()
    for phrase in required_argument_phrases:
        if phrase not in arg_lower:
            errors.append(f"argument_map.md missing required concept: {phrase}")

    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        low = text.lower()
        # These exact affirmative formulations are never acceptable in WP2 artifacts.
        forbidden_affirmative = [
            "demonstrated universal robustness",
            "completed prospective validation",
            "clinically safe threshold",
            "proves clinical utility",
            "universal best model",
            "independent institutional validation",
        ]
        for phrase in forbidden_affirmative:
            for hit in re.finditer(re.escape(phrase), low):
                context = low[max(0, hit.start() - 35):hit.end() + 10]
                if not any(neg in context for neg in ["not ", "no ", "cannot ", "never ", "do not ", "??", "??", "???", "???"]):
                    errors.append(f"{path.name}: potentially affirmative prohibited phrase: {phrase}")

    # WP2 is an outline checkpoint: main.tex and section prose must remain untouched.
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True, capture_output=True, check=True)
        git_root = Path(top.stdout.strip())
        allowed = PROJECT.relative_to(git_root).as_posix() + "/"
        status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=git_root, text=True, capture_output=True, check=True)
        outside: list[str] = []
        forbidden_wp2: list[str] = []
        for line in status.stdout.splitlines():
            rel = line[3:].strip().strip('"').replace("\\", "/")
            if " -> " in rel:
                rel = rel.split(" -> ", 1)[1]
            if rel and not rel.startswith(allowed):
                outside.append(line)
            local = rel[len(allowed):] if rel.startswith(allowed) else ""
            if local == "main.tex" or local.startswith("sections/"):
                forbidden_wp2.append(line)
        if outside:
            errors.append("modified/untracked files outside manuscript project: " + " | ".join(outside))
        if forbidden_wp2:
            errors.append("WP2 modified main.tex or manuscript section prose: " + " | ".join(forbidden_wp2))
    except Exception as exc:
        warnings.append(f"git boundary check unavailable: {exc}")

    if evidence_ref_count < 80:
        warnings.append(f"only {evidence_ref_count} exact evidence references were detected")

    return finish(errors, warnings, evidence_ref_count)


if __name__ == "__main__":
    sys.exit(main())
