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
    "ABS": [f"ABS-{i:02d}" for i in range(1, 5)],
    "INT": [f"INT-{i:02d}" for i in range(1, 5)],
    "RES": [f"RES-{i:02d}" for i in range(1, 6)],
    "DIS": [f"DIS-{i:02d}" for i in range(1, 7)],
    "MET": [f"MET-{i:02d}" for i in range(1, 9)],
}
RESULT_FIELDS_ZH = [
    "回答的问题", "声明 ID", "关联 evidence_id", "队列角色", "分析性质",
    "样本量", "覆盖率", "95% CI", "核心解释", "必须呈现的阴性/限制证据",
    "暂定图表", "正文/补充材料",
]
RESULT_FIELDS_EN = [
    "Question answered", "Claim IDs", "Linked evidence_id values", "Cohort role",
    "Analysis nature", "Sample size", "Coverage", "95% CI", "Core interpretation",
    "Mandatory negative/limiting evidence", "Provisional display", "Destination",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def sections(text: str, prefix: str) -> dict[str, str]:
    all_paragraphs = list(re.finditer(r"^###\s+((?:ABS|INT|RES|DIS|MET)-\d{2})\b.*$", text, re.M))
    result: dict[str, str] = {}
    for index, hit in enumerate(all_paragraphs):
        paragraph_id = hit.group(1)
        if not paragraph_id.startswith(prefix + "-"):
            continue
        next_paragraph = all_paragraphs[index + 1].start() if index + 1 < len(all_paragraphs) else len(text)
        next_section = re.search(r"^##\s+", text[hit.end():next_paragraph], re.M)
        end = hit.end() + next_section.start() if next_section else next_paragraph
        result[paragraph_id] = text[hit.start():end]
    return result


def main_body(text: str) -> str:
    """Return the outline paragraph blocks, excluding explicit boundary notes."""
    blocks: list[str] = []
    for prefix in EXPECTED_IDS:
        blocks.extend(sections(text, prefix).values())
    return "\n".join(blocks)


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

    # Bilingual paragraph structure must be identical and story-driven.
    for prefix, expected in EXPECTED_IDS.items():
        zh_ids = list(sections(zh, prefix))
        en_ids = list(sections(en, prefix))
        if zh_ids != expected:
            errors.append(f"Chinese {prefix} paragraph IDs differ from expected: {zh_ids}")
        if en_ids != expected:
            errors.append(f"English {prefix} paragraph IDs differ from expected: {en_ids}")
        if zh_ids != en_ids:
            errors.append(f"bilingual {prefix} paragraph IDs/order differ")

    # Required Results fields and WP1 interfaces.
    zh_results = sections(zh, "RES")
    en_results = sections(en, "RES")
    for paragraph_id, block in zh_results.items():
        for field in RESULT_FIELDS_ZH:
            if f"**{field}：**" not in block:
                errors.append(f"{OUTLINE_ZH.name} {paragraph_id} missing field: {field}")
        if not re.search(r"\bC\d{2}\b", block):
            errors.append(f"{OUTLINE_ZH.name} {paragraph_id} has no claim ID")
        if not re.search(r"`(?:P\d|GOV)-", block):
            errors.append(f"{OUTLINE_ZH.name} {paragraph_id} has no linked evidence_id")
    for paragraph_id, block in en_results.items():
        for field in RESULT_FIELDS_EN:
            if f"**{field}:**" not in block:
                errors.append(f"{OUTLINE_EN.name} {paragraph_id} missing field: {field}")
        if not re.search(r"\bC\d{2}\b", block):
            errors.append(f"{OUTLINE_EN.name} {paragraph_id} has no claim ID")
        if not re.search(r"`(?:P\d|GOV)-", block):
            errors.append(f"{OUTLINE_EN.name} {paragraph_id} has no linked evidence_id")

    # Validate every exact backticked evidence ID; documented wildcard prefixes are allowed.
    evidence_ref_count = 0
    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        for token in re.findall(r"`([^`]+)`", text):
            wildcard = token.endswith("*") and token[:-1].startswith(("P", "GOV"))
            candidates = re.findall(
                r"(?:GOV-ANCHOR-\d{3}|P\d-[A-Z]+(?:-[A-Z]+)*-R\d{3}(?:-[A-Z0-9-]+)?)",
                token,
            )
            for ref in candidates:
                evidence_ref_count += 1
                if wildcard and token[:-1].startswith(ref):
                    continue
                if ref not in evidence_ids:
                    errors.append(f"{path.name}: unknown evidence_id {ref}")
            if wildcard:
                prefix = token[:-1]
                if not any(evidence_id.startswith(prefix) for evidence_id in evidence_ids):
                    errors.append(f"{path.name}: wildcard evidence prefix has no match: {token}")

    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        for claim_id in sorted(set(re.findall(r"\bC\d{2}\b", text))):
            if claim_id not in claim_ids:
                errors.append(f"{path.name}: unknown claim ID {claim_id}")

    # Title and thesis requirements requested at the WP2 revision checkpoint.
    leading_title_zh = re.search(r"\*\*首选暂定标题：\*\*\s*(.+)", zh)
    leading_title_en = re.search(r"\*\*Leading provisional title:\*\*\s*(.+)", en)
    for label, match in [("Chinese", leading_title_zh), ("English", leading_title_en)]:
        if not match or "TRUST-HN" not in match.group(1):
            errors.append(f"{label} leading title does not contain TRUST-HN")
    if "条件性" not in zh or "临床锚点" not in zh:
        errors.append("Chinese outline lacks conditional-value/clinical-anchor thesis language")
    if "conditional" not in en.lower() or "clinical anchor" not in en.lower():
        errors.append("English outline lacks conditional-value/clinical-anchor thesis language")
    if "conditional" not in argument.lower() or "clinical anchor" not in argument.lower():
        errors.append("argument_map.md lacks the conditional clinical-anchor thesis")

    # Phase 7 must always remain post hoc exploratory.
    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        lower = text.lower()
        for hit in re.finditer(r"phase\s*7", lower):
            context = lower[max(0, hit.start() - 80):hit.end() + 100]
            if "post hoc exploratory" not in context:
                errors.append(f"{path.name}: Phase 7 mention lacks nearby post hoc exploratory label")
                break

    # Phase 8 is excluded from all current main-body paragraph blocks.
    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        body = main_body(text).lower()
        forbidden = ["phase 8", "phase8", "p8-", "gov-anchor-007", "gov-anchor-008", "gov-anchor-009", "gov-anchor-010", "gov-anchor-011"]
        for phrase in forbidden:
            if phrase in body:
                errors.append(f"{path.name}: main-body paragraph blocks reference excluded {phrase}")
    if "MET-09" in zh or "MET-09" in en or "MET-09" in argument:
        errors.append("MET-09 remains after Phase 8 main-text removal")

    # Results-specific narrative and high-risk interfaces.
    for language, result_map in [("zh", zh_results), ("en", en_results)]:
        res02 = result_map.get("RES-02", "").lower()
        res03 = result_map.get("RES-03", "").lower()
        res04 = result_map.get("RES-04", "").lower()
        res05 = result_map.get("RES-05", "").lower()
        for cohort in ["radcure", "hancock", "gse65858", "gse41613"]:
            if cohort not in res02:
                errors.append(f"{language} RES-02 lacks integrated cohort evidence: {cohort}")
        if "calibration" not in res02 and "校准" not in res02:
            errors.append(f"{language} RES-02 lacks central cross-platform calibration failure")
        if "coverage" not in res03 and "覆盖率" not in res03:
            errors.append(f"{language} RES-03 lacks B7 coverage")
        if "identical non-abstained subset" not in res03 and "相同非弃权" not in res03:
            errors.append(f"{language} RES-03 lacks identical non-abstained-subset qualifier")
        if "gse41613" not in res02 or ("hpv-negative oscc" not in res02 and "hpv 阴性 oscc" not in res02):
            errors.append(f"{language} RES-02 lacks GSE41613 HPV-negative OSCC boundary")
        if "dca" not in res04:
            errors.append(f"{language} RES-04 lacks DCA falsification evidence")
        if "clinical utility" not in res04 and "临床效用" not in res04:
            errors.append(f"{language} RES-04 lacks no-clinical-utility boundary")
        if "post hoc exploratory" not in res05:
            errors.append(f"{language} RES-05 lacks post hoc exploratory label")
        if "no universal winner" not in res05 and "没有普遍赢家" not in res05 and "无统一赢家" not in res05:
            errors.append(f"{language} RES-05 lacks no-universal-winner conclusion")

    required_argument_phrases = [
        "provisional titles", "primary research question", "contribution hierarchy",
        "main argument chain", "counterevidence", "threat-to-validity",
        "main-text versus supplement boundary", "paragraph-to-argument crosswalk",
        "the scientific story, not an experiment inventory",
    ]
    argument_lower = argument.lower()
    for phrase in required_argument_phrases:
        if phrase not in argument_lower:
            errors.append(f"argument_map.md missing required concept: {phrase}")

    # Prohibited affirmative claims.
    for path, text in [(OUTLINE_ZH, zh), (OUTLINE_EN, en), (ARGUMENT, argument)]:
        lower = text.lower()
        forbidden_affirmative = [
            "demonstrated universal robustness",
            "completed prospective validation",
            "clinically safe threshold",
            "proves clinical utility",
            "universal best model",
            "independent institutional validation",
        ]
        for phrase in forbidden_affirmative:
            for hit in re.finditer(re.escape(phrase), lower):
                context = lower[max(0, hit.start() - 45):hit.end() + 15]
                if not any(neg in context for neg in ["not ", "no ", "cannot ", "never ", "do not ", "不得", "不声称", "不能", "未"]):
                    errors.append(f"{path.name}: potentially affirmative prohibited phrase: {phrase}")

    # WP2 remains an outline checkpoint: no main.tex or section prose changes.
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
            text=True, capture_output=True, check=True,
        )
        git_root = Path(top.stdout.strip())
        allowed = PROJECT.relative_to(git_root).as_posix() + "/"
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=git_root,
            text=True, capture_output=True, check=True,
        )
        outside: list[str] = []
        forbidden_wp2: list[str] = []
        for line in status.stdout.splitlines():
            relative = line[3:].strip().strip('"').replace("\\", "/")
            if " -> " in relative:
                relative = relative.split(" -> ", 1)[1]
            if relative and not relative.startswith(allowed):
                outside.append(line)
            local = relative[len(allowed):] if relative.startswith(allowed) else ""
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
