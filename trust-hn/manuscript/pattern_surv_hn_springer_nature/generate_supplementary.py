from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "supplementary.md"
OUTPUT = HERE / "supplementary.tex"

MANUSCRIPT_TITLE = (
    "Clinically anchored multimodal survival prediction under missing, shifted "
    "and shortcut-prone evidence in head and neck cancer"
)
MATH_PATTERN = re.compile(r"(\$[^$]*\$|\\\(.*?\\\)|\\\[.*?\\\])", re.DOTALL)


def tex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def inline_code(match: re.Match[str]) -> str:
    content = match.group(1)
    escaped = tex_escape(content)

    # Long repository paths and integrity hashes must remain traceable, while
    # still allowing line breaks in a two-column-safe Nature-template layout.
    if "/" in content and len(content) > 28:
        escaped = "\\allowbreak{}".join(tex_escape(ch) for ch in content)
        return r"{\footnotesize\texttt{" + escaped + r"}}"

    if re.fullmatch(r"[A-F0-9]{40,}", content):
        escaped = "\\allowbreak{}".join(
            escaped[i : i + 8] for i in range(0, len(escaped), 8)
        )
    elif len(content) > 28:
        escaped = escaped.replace("/", "/\\allowbreak{}")
        escaped = escaped.replace("\\_", "\\_\\allowbreak{}")

    if len(content) > 28:
        return r"{\small\texttt{" + escaped + r"}}"
    return r"\texttt{" + escaped + "}"


def normalize_unicode(text: str) -> str:
    replacements = {
        "\u0394": r"$\Delta$",
        "\u2265": r"$\ge$",
        "\u2264": r"$\le$",
        "\u2192": r"$\rightarrow$",
        "\u2014": "---",
        "\u2013": "--",
        "\u2018": "`",
        "\u2019": "'",
        "\u201c": "``",
        "\u201d": "''",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def format_text(text: str) -> str:
    parts: list[str] = []
    pos = 0
    for match in MATH_PATTERN.finditer(text):
        parts.append(format_plain(text[pos : match.start()]))
        parts.append(match.group(1))
        pos = match.end()
    parts.append(format_plain(text[pos:]))
    return "".join(parts)


def format_plain(text: str) -> str:
    if not text:
        return ""
    text = normalize_unicode(text)
    text = re.sub(r"`([^`]+)`", inline_code, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\\emph{\1}", text)
    text = re.sub(r"(?<![\\{])&", r"\\&", text)
    text = re.sub(r"(?<![\\{])%", r"\\%", text)
    text = re.sub(r"(?<![\\{])#", r"\\#", text)
    text = re.sub(r"(?<![\\{])_", r"\\_", text)
    return text


def strip_table_delimiters(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip() for cell in value.split("|")]


def is_table_separator(line: str) -> bool:
    return bool(
        re.fullmatch(
            r"\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*", line
        )
    )


def table_alignment(line: str) -> list[str]:
    cells = strip_table_delimiters(line)
    return [
        "right" if cell.startswith(":") and cell.endswith(":") else "left"
        for cell in cells
    ]


def format_table(
    rows: list[list[str]], align: list[str], caption: str, label: str
) -> list[str]:
    ncols = max(len(row) for row in rows)
    rows = [row + [""] * (ncols - len(row)) for row in rows]
    align = align + ["left"] * (ncols - len(align))

    # Reserve wider terminal columns for words such as "Interpretation" and
    # "Calibration", while keeping numeric columns compact and page safe.
    if ncols <= 4:
        widths = [0.30] + [0.18] * (ncols - 1)
    elif ncols == 5:
        widths = [0.20] + [0.16] * (ncols - 2) + [0.18]
    elif ncols == 6:
        widths = [0.19] + [0.13] * (ncols - 2) + [0.16]
    else:
        widths = [0.16] + [0.107] * (ncols - 2) + [0.125]
    prefixes = {
        "left": r">{\raggedright\arraybackslash}",
        "right": r">{\raggedleft\arraybackslash}",
    }
    colspec = " ".join(
        f"{prefixes[align[j]]}p{{{widths[j]:.3f}\\textwidth}}"
        for j in range(ncols)
    )

    out = [
        "",
        r"\begingroup",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{2pt}",
        rf"\begin{{longtable}}{{{colspec}}}",
        rf"\caption{{{format_text(caption)}}}\label{{{label}}}\\",
        r"\toprule",
    ]
    out.append(" & ".join(format_text(cell) for cell in rows[0]) + r" \\")
    out.extend(
        [
            r"\midrule",
            r"\endfirsthead",
            rf"\multicolumn{{{ncols}}}{{l}}{{\itshape Supplementary table continued from previous page}}\\",
            r"\toprule",
        ]
    )
    out.append(" & ".join(format_text(cell) for cell in rows[0]) + r" \\")
    out.extend([r"\midrule", r"\endhead", r"\bottomrule", r"\endlastfoot"])
    for row in rows[1:]:
        out.append(" & ".join(format_text(cell) for cell in row) + r" \\")
    out.extend([r"\end{longtable}", r"\endgroup", ""])
    return out


def make_preamble() -> str:
    return r"""\pdfminorversion=7
\documentclass[pdflatex,sn-nature]{sn-jnl}
\usepackage{graphicx,amsmath,amssymb,booktabs,longtable,array,caption,url}
\captionsetup{labelformat=empty,font=small,justification=raggedright,singlelinecheck=false}
\hypersetup{hypertexnames=false}
\raggedbottom
\setcounter{table}{0}
\setlength{\LTcapwidth}{\textwidth}
\renewcommand{\arraystretch}{1.10}
\emergencystretch=1.5em

\begin{document}
\title[Supplementary Information for PATTERN-Surv-HN]{Supplementary Information for: """ + MANUSCRIPT_TITLE + r"""}
\maketitle

"""


def convert() -> None:
    lines = SOURCE.read_text(encoding="utf-8-sig").splitlines()
    out: list[str] = []
    latest_heading = "PATTERN-Surv-HN supplementary table"
    table_count = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = normalize_unicode(stripped[level:].strip())

            if i == 0:
                i += 1
                continue

            latest_heading = title
            if title.startswith("Supplementary Table"):
                # The heading is converted to the table caption below.
                i += 1
                continue

            command = "section*" if level == 2 else "subsection*"
            if title.startswith("RADCURE"):
                # Keep the wide seven-column benchmark table on one page.
                out.append(r"\clearpage")
            out.extend([rf"\{command}{{{format_text(title)}}}", ""])
            i += 1
            continue

        if stripped.startswith(">"):
            quote = stripped.lstrip(">").strip()
            out.extend(
                [
                    r"\begin{quote}",
                    format_text(quote),
                    r"\end{quote}",
                    "",
                ]
            )
            i += 1
            continue

        if (
            stripped.startswith("|")
            and i + 1 < len(lines)
            and is_table_separator(lines[i + 1])
        ):
            align = table_alignment(lines[i + 1])
            rows = [strip_table_delimiters(line)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(strip_table_delimiters(lines[i]))
                i += 1

            table_count += 1
            if latest_heading.startswith("Supplementary Table"):
                caption = latest_heading
            else:
                caption = (
                    f"Supplementary Table {table_count}. "
                    f"{latest_heading}: aggregate results"
                )
            label = f"tab:supptable{table_count}"
            out.extend(format_table(rows, align, caption, label))
            continue

        # Preserve display-math blocks exactly.
        if stripped.startswith(r"\["):
            math_lines = [line]
            i += 1
            while i < len(lines):
                math_lines.append(lines[i])
                if lines[i].strip().endswith(r"\]"):
                    i += 1
                    break
                i += 1
            out.extend(["", *math_lines, ""])
            continue

        out.extend([format_text(stripped), ""])
        i += 1

    closing = "\n\\end{document}\n"
    OUTPUT.write_text(
        make_preamble() + "\n".join(out).strip() + closing,
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"saved {OUTPUT.name}: {len(out)} source blocks, "
        f"{table_count} supplementary tables"
    )


if __name__ == "__main__":
    convert()
