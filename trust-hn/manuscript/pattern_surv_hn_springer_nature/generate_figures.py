from __future__ import annotations

import json
import math
import shutil
import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[3]
FIGDIR = Path(__file__).resolve().parent / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    "font.family": "Arial", "font.size": 7,
    "axes.titlesize": 7.5, "axes.labelsize": 7,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.3,
    "axes.linewidth": 0.55, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.major.width": 0.55, "ytick.major.width": 0.55,
    "xtick.major.size": 2.3, "ytick.major.size": 2.3,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600,
})

MM = 1 / 25.4
FULLW = 183 * MM
COL_BLUE = "#2F5597"
COL_ORANGE = "#D9731D"
COL_TEAL = "#0F7B6C"
COL_PURPLE = "#7A5AA8"
COL_RED = "#C4385D"
COL_GREY = "#6B7A8A"
COL_LIGHT = "#C9D3DF"
COL_DARK = "#25324A"
COLS = [COL_BLUE, COL_ORANGE, COL_TEAL, COL_PURPLE, COL_RED]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def panel(ax, label: str):
    ax.text(-0.13, 1.06, label, transform=ax.transAxes, fontsize=8,
            fontweight="bold", va="bottom", ha="left", color=COL_DARK)


def save(fig: plt.Figure, stem: str):
    for ext in ("pdf", "png"):
        fig.savefig(FIGDIR / f"{stem}.{ext}", format=ext, dpi=600,
                    bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)
    print(f"saved {stem}.pdf/.png")


def clean_axes(ax):
    ax.grid(axis="y", color="#E2E7ED", linewidth=0.45, alpha=0.9)
    ax.set_axisbelow(True)


def figure1():
    """Publication-facing framework with descriptive model names rather than audit IDs."""
    fig, axes = plt.subplots(1, 4, figsize=(FULLW, 93 * MM),
                             gridspec_kw={"left": 0.025, "right": 0.99, "top": 0.88,
                                          "bottom": 0.13, "wspace": 0.10,
                                          "width_ratios": [1.03, 1.08, 1.10, 1.03]})
    titles = ["Inputs and evidence contract", "Permutation-invariant residual",
              "Nested shrinkage control", "Governed prediction paths"]
    for idx, (ax, title) in enumerate(zip(axes, titles, strict=True)):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.01, 0.01), 0.98, 0.98,
                                    boxstyle="round,pad=0.006,rounding_size=0.012",
                                    facecolor="white", edgecolor="#9AA8B7",
                                    linewidth=0.75, linestyle=(0, (4, 3))))
        ax.text(0.04, 1.035, chr(97 + idx), fontsize=8, fontweight="bold", color=COL_DARK)
        ax.text(0.13, 1.035, title, fontsize=7.2, fontweight="bold", color=COL_DARK)

    def box(ax, xy, wh, title, subtitle="", edge=COL_BLUE, face="#F3F7FB", fs=6.5):
        x, y = xy; w, h = wh
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.014",
                                    facecolor=face, edgecolor=edge, linewidth=0.8))
        ax.text(x + w / 2, y + h * (0.62 if subtitle else 0.50), title,
                ha="center", va="center", fontsize=fs, fontweight="bold", color=edge)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center",
                    fontsize=5.0, color=COL_GREY, linespacing=1.05)
        return (x, y, w, h)

    def arrow(ax, start, end, color=COL_DARK, style="-|>"):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=7,
                                    linewidth=0.75, color=color, connectionstyle="arc3,rad=0"))

    ax = axes[0]
    cam = box(ax, (0.08, 0.70), (0.84, 0.16), "Clinical anchor model (CAM)",
              "postoperative clinical-\npathological variables", COL_BLUE)
    ax.text(0.08, 0.62, "Optional modalities", fontsize=6.5, fontweight="bold", color=COL_TEAL)
    ys = [0.46, 0.31, 0.16]
    for y, name, detail in zip(ys, ["Blood", "ICD", "TMA"], ["32 features", "80 features", "8 features"], strict=True):
        box(ax, (0.08, y), (0.30, 0.10), name, detail, COL_TEAL, "#F1FAF8", 6.1)
        box(ax, (0.50, y), (0.42, 0.10), "Usability gate", "status + quality", COL_TEAL, "#F1FAF8", 5.9)
        arrow(ax, (0.38, y + 0.05), (0.50, y + 0.05), COL_TEAL)
    ax.text(0.50, 0.075, "Absent and acquired-but-unusable\ninputs remain distinct", ha="center",
            va="center", fontsize=5.7, color=COL_GREY)

    ax = axes[1]
    ax.text(0.50, 0.89, "Usable modality tokens", ha="center", fontsize=6.5,
            fontweight="bold", color=COL_TEAL)
    for i, y in enumerate([0.70, 0.53, 0.36]):
        box(ax, (0.08, y), (0.25, 0.10), f"z$_{i+1}$", "identity + quality", COL_TEAL, "#F1FAF8", 6.2)
        box(ax, (0.45, y), (0.29, 0.10), "Shared encoder", "$\phi$: 16-24-16", COL_TEAL, "#F1FAF8", 5.6)
        arrow(ax, (0.33, y + 0.05), (0.45, y + 0.05), COL_TEAL)
        arrow(ax, (0.74, y + 0.05), (0.82, 0.55), COL_TEAL)
    box(ax, (0.77, 0.47), (0.18, 0.14), "Masked\nmean", "set invariant", COL_ORANGE, "#FFF7E8", 5.4)
    arrow(ax, (0.86, 0.47), (0.86, 0.27), COL_ORANGE)
    box(ax, (0.57, 0.13), (0.38, 0.12), "Residual score", "$\Delta\eta_{res}$", COL_PURPLE, "#F7F3FB", 6.0)
    ax.text(0.08, 0.08, "Empty set  →  residual = 0", fontsize=6.0, color=COL_ORANGE, fontweight="bold")

    ax = axes[2]
    box(ax, (0.10, 0.73), (0.80, 0.14), "Three-fold inner cross-validation",
        "penalty • checkpoint • residual scale", COL_PURPLE, "#F7F3FB", 6.2)
    box(ax, (0.08, 0.43), (0.34, 0.13), "CAM score", "$\eta_{CAM}$", COL_BLUE, "#F3F7FB", 6.2)
    box(ax, (0.08, 0.20), (0.34, 0.13), "Residual", "$\lambda_f\Delta\eta_{res}$", COL_PURPLE, "#F7F3FB", 6.2)
    ax.text(0.56, 0.39, "+", ha="center", va="center", fontsize=13, color=COL_BLUE, fontweight="bold")
    arrow(ax, (0.42, 0.495), (0.52, 0.42), COL_BLUE)
    arrow(ax, (0.42, 0.265), (0.52, 0.36), COL_PURPLE)
    arrow(ax, (0.50, 0.73), (0.25, 0.33), COL_PURPLE)
    box(ax, (0.66, 0.31), (0.27, 0.16), "Raw SCRF", "$\eta_{CAM}$ + scaled residual", COL_BLUE, "#EEF5FC", 6.2)
    arrow(ax, (0.60, 0.39), (0.66, 0.39), COL_BLUE)
    ax.text(0.50, 0.08, "Fold-bound preprocessing and baseline hazard", ha="center", fontsize=5.7, color=COL_GREY)

    ax = axes[3]
    box(ax, (0.08, 0.74), (0.84, 0.14), "Primary: raw SCRF", "24-month risk • full coverage", COL_BLUE, "#EEF5FC", 6.5)
    box(ax, (0.08, 0.52), (0.84, 0.13), "Exact CAM fallback", "when no optional modality is usable", COL_ORANGE, "#FFF7E8", 6.3)
    box(ax, (0.08, 0.30), (0.84, 0.13), "Development-only\ncalibration bridge", "global • monotone • rank preserving", COL_TEAL, "#F1FAF8", 5.7)
    box(ax, (0.08, 0.08), (0.84, 0.13), "Exploratory reliability router", "not validated for deployment", COL_GREY, "#F5F6F8", 5.8)
    arrow(ax, (0.50, 0.74), (0.50, 0.65), COL_BLUE)
    arrow(ax, (0.50, 0.52), (0.50, 0.43), COL_ORANGE)
    arrow(ax, (0.50, 0.30), (0.50, 0.21), COL_TEAL)

    fig.text(0.025, 0.035, "Primary prediction path", fontsize=5.8, color=COL_BLUE, fontweight="bold")
    fig.text(0.265, 0.035, "Optional evidence pathway", fontsize=5.8, color=COL_TEAL, fontweight="bold")
    fig.text(0.535, 0.035, "Shrinkage selected inside training data", fontsize=5.8, color=COL_PURPLE, fontweight="bold")
    fig.text(0.805, 0.035, "Exact fallback", fontsize=5.8, color=COL_ORANGE, fontweight="bold")
    save(fig, "figure1_pattern_surv_hn_framework")


U1 = "trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U1_1_data_contract/aggregate_contract_audit.json"
U2 = "trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U2_V1R_residual_shrinkage_rescue/aggregate_u2_v1r_rescue_audit.json"
U5R8 = "trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U5R8_V1R_beta09_logloss_bridge_confirmation_validation/u5r7_confirmation_bridge_aggregate_results.json"
U6 = "trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U6R1_patient_level_router_aggregation_exploration/u6r1_aggregate_results.json"
U7 = "trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U7R2_RADCURE_external_characterization/u7r2_radcure_external_characterization_aggregate_results.json"
U8 = "trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U8_T1R_transcriptome_residual_shrinkage/aggregate_t1r_transcriptome_development_cv_audit.json"
U8E = "trust-hn/research_studies/01_pattern_surv_hn/core_backbone/U8E_T1R_external_characterization/aggregate_t1r_external_characterization_audit.json"
BRIDGE = "trust-hn/paper/manuscript_results/V1R_positive/v1r_bridge_positive_results.json"
LOCKED = "trust-hn/paper/manuscript_results/V1R_positive/v1r_locked_confirmation_positive_results.json"
U9_TABLE = "trust-hn/results/metrics/pattern_surv_hn/U9_published_comparator_benchmark/u9_main_table_summary.csv"
U10_TABLE = "trust-hn/results/metrics/pattern_surv_hn/U10_recent_comparator_benchmark/u10_main_table_summary.csv"


def figure2():
    d = load(U1)
    fig = plt.figure(figsize=(FULLW, 126 * MM))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.25, 1, 1], height_ratios=[1, 1.12],
                          left=0.065, right=0.985, top=0.93, bottom=0.085, wspace=0.34, hspace=0.55)

    ax = fig.add_subplot(gs[0, 0])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    boxes = [
        (0.02, 0.75, "HANCOCK records", f"n={d['records']}"),
        (0.02, 0.48, "Eligible postoperative", f"n={d['eligible']}"),
        (0.02, 0.17, "Development", f"n={d['development_eligible']}; deaths={d['development_events']}"),
        (0.65, 0.17, "Outcome-sealed cohort", f"n={d['outcome_sealed']}; deaths=40"),
    ]
    for x, y, title, detail in boxes:
        col = COL_BLUE if x < 0.5 else COL_TEAL
        ax.add_patch(FancyBboxPatch((x, y), 0.35 if x < 0.5 else 0.33, 0.16,
                                    boxstyle="round,pad=0.012,rounding_size=0.02",
                                    linewidth=0.65, edgecolor=col, facecolor="#F4F8FC"))
        cx = x + (0.175 if x < 0.5 else 0.165)
        ax.text(cx, y + 0.098, title, ha="center", va="center", fontsize=6.6, fontweight="bold", color=COL_DARK)
        ax.text(cx, y + 0.042, detail, ha="center", va="center", fontsize=6.3, color=COL_GREY)
    ax.text(0.20, 0.685, f"excluded n={d['excluded']}", fontsize=6.1, color=COL_RED, ha="center")
    ax.add_patch(FancyArrowPatch((0.20, 0.745), (0.20, 0.655), arrowstyle="-|>", mutation_scale=7, linewidth=0.7, color=COL_GREY))
    ax.add_patch(FancyArrowPatch((0.20, 0.475), (0.20, 0.345), arrowstyle="-|>", mutation_scale=7, linewidth=0.7, color=COL_GREY))
    ax.add_patch(FancyArrowPatch((0.40, 0.25), (0.64, 0.25), arrowstyle="-|>", mutation_scale=7, linewidth=0.7, color=COL_GREY, connectionstyle="arc3,rad=0.18"))
    ax.text(0.525, 0.075, "Outcome sealed before confirmation prediction unsealing", ha="center", fontsize=6.0, color=COL_GREY)
    panel(ax, "a")

    ax = fig.add_subplot(gs[0, 1:])
    mods = ["blood", "icd", "tma"]; labels = ["Blood", "ICD", "TMA"]; x = np.arange(len(mods)); bottom = np.zeros(len(mods))
    cats = [("usable_complete", "Usable, complete", "#93C5A7"), ("conditional_provenance", "Usable, contract", "#7FB7A9"), ("usable_partial", "Usable, partial", COL_TEAL),
            ("acquired_unusable", "Acquired, unusable", COL_ORANGE), ("absent", "Absent", COL_GREY)]
    for key, lab, col in cats:
        vals = np.array([d["modality_counts"][m]["status_counts"].get(key, 0) for m in mods], dtype=float)
        ax.bar(x, vals, bottom=bottom, width=0.55, label=lab, color=col, edgecolor="white", linewidth=0.4)
        for xi, (v, b) in enumerate(zip(vals, bottom)):
            if v > 25:
                ax.text(xi, b + v / 2, f"{int(v)}", ha="center", va="center", fontsize=6.1,
                        color="white" if key in ("acquired_unusable", "absent") else COL_DARK)
        bottom += vals
    ax.set_xticks(x, labels); ax.set_ylabel("Eligible patients"); ax.set_ylim(0, 810)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.20), columnspacing=0.75, handlelength=1.1)
    clean_axes(ax); panel(ax, "b")

    ax = fig.add_subplot(gs[1, :2])
    patterns = [p for p in d["usable_patterns"] if p["split_role"] != "sealed_test"]
    agg = {}
    for p in patterns:
        z = agg.setdefault(p["pattern"], {"n": 0, "events": 0}); z["n"] += p["n"]; z["events"] += p["events_exposed"] or 0
    order = sorted(agg, key=lambda k: agg[k]["n"])
    names = [f"{k[0]}-{k[1]}-{k[2]}" for k in order]
    ns = np.array([agg[k]["n"] for k in order], float); ev = np.array([agg[k]["events"] for k in order], float); yy = np.arange(len(order))
    ax.barh(yy - 0.19, ns, height=0.36, color=COL_BLUE, label="Patients")
    ax.barh(yy + 0.19, ev, height=0.36, color=COL_ORANGE, label="Deaths")
    supported = (ns >= 30) & (ev >= 10)
    for yi, (n, e, s) in enumerate(zip(ns, ev, supported)):
        ax.text(n + 4, yi - 0.19, str(int(n)), va="center", fontsize=6.0, color=COL_BLUE)
        ax.text(e + 4, yi + 0.19, str(int(e)), va="center", fontsize=6.0, color=COL_ORANGE)
        if not s: ax.text(392, yi, "low support", va="center", ha="right", fontsize=5.8, color=COL_RED)
    ax.set_yticks(yy, names); ax.set_xlabel("Development patients and exposed deaths"); ax.set_xlim(0, 410)
    ax.legend(loc="lower right", ncol=2); ax.grid(axis="x", color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True)
    ax.text(0.01, 1.06, "Blood-ICD-TMA usability tuple (1=usable)", transform=ax.transAxes, fontsize=6.2, color=COL_GREY)
    panel(ax, "c")

    ax = fig.add_subplot(gs[1, 2])
    ax.scatter(ns, ev, s=np.maximum(ns * 1.3, 14), c=np.where(supported, COL_TEAL, COL_RED), alpha=0.85, edgecolor="white", linewidth=0.5, zorder=3)
    for k, n, e in zip(order, ns, ev):
        if n > 40: ax.text(n, e + 5, f"{k[0]}-{k[1]}-{k[2]}", ha="center", fontsize=6.0, color=COL_GREY)
    ax.axvline(30, color=COL_GREY, linestyle="--", linewidth=0.65); ax.axhline(10, color=COL_GREY, linestyle="--", linewidth=0.65)
    ax.set_xscale("log"); ax.set_xlim(0.8, 1000); ax.set_ylim(-5, 150)
    ax.set_xlabel("Pattern n (log scale)"); ax.set_ylabel("Deaths")
    ax.text(0.05, 0.90, "Supported:\nn >= 30; deaths >= 10", transform=ax.transAxes, fontsize=6.0, color=COL_TEAL)
    ax.text(0.60, 0.08, "Rare", transform=ax.transAxes, fontsize=6.0, color=COL_RED)
    ax.grid(color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True); panel(ax, "d")
    save(fig, "figure2_cohort_flow_acquisition_usability")

def figure3():
    d = load(U2); summary = d["results"]["across_seed_summary"]; seeds = d["results"]["per_seed_metrics"]
    fig = plt.figure(figsize=(FULLW, 106 * MM))
    gs = fig.add_gridspec(2, 4, left=0.075, right=0.985, top=0.90, bottom=0.10, wspace=0.55, hspace=0.58)
    ax = fig.add_subplot(gs[0, :2])
    metrics = [("IPCW Brier24", "ipcw_brier_24m", False), ("Uno C24", "uno_c_24m", True), ("AUC24", "auc_24m", True), ("Harrell C", "harrell_c", True)]
    xx = np.arange(len(metrics)); v0 = [summary[m]["V0_mean"] for _, m, _ in metrics]; v1 = [summary[m]["V1_mean"] for _, m, _ in metrics]
    ax.plot(xx, v0, "o", ms=4.2, color=COL_GREY, label="Clinical anchor"); ax.plot(xx, v1, "o", ms=4.2, color=COL_BLUE, label="SCRF")
    for i, (a, b) in enumerate(zip(v0, v1)): ax.plot([i, i], [a, b], color="#B8C4D2", linewidth=0.8, zorder=0)
    ax.set_xticks(xx, [m for m, _, _ in metrics], rotation=18, ha="right"); ax.set_ylabel("Mean over five seeds")
    ax.legend(loc="center left", bbox_to_anchor=(0.02, 0.48)); clean_axes(ax)
    ax.text(0.02, 0.88, "Brier lower; discrimination higher", transform=ax.transAxes, fontsize=6.0, color=COL_GREY)
    panel(ax, "a")

    ax = fig.add_subplot(gs[0, 2:]); colors = [COL_BLUE, COL_ORANGE, COL_TEAL, COL_PURPLE]
    for j, (label, key, _) in enumerate(metrics):
        vals = [s["delta_V1_minus_V0"][key] for s in seeds]
        ax.scatter(np.full(len(vals), j) + np.linspace(-0.10, 0.10, len(vals)), vals, s=10, color=colors[j], alpha=0.75, edgecolor="none")
        ax.hlines(np.mean(vals), j - 0.22, j + 0.22, color=colors[j], linewidth=1.2)
    ax.axhline(0, color=COL_DARK, linewidth=0.65); ax.set_xticks(range(len(metrics)), [m for m, _, _ in metrics], rotation=18, ha="right")
    ax.set_ylabel("SCRF − clinical anchor"); ax.grid(axis="y", color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True)
    ax.text(0.01, 1.06, "Dots: seeds; bars: means", transform=ax.transAxes, fontsize=6.0, color=COL_GREY); panel(ax, "b")

    ax = fig.add_subplot(gs[1, :2]); labels = [m for m, _, _ in metrics]; better = [summary[m]["V1_better_seed_count"] for _, m, _ in metrics]
    ax.barh(np.arange(len(labels)), better, height=0.55, color=colors)
    ax.set_yticks(np.arange(len(labels)), labels); ax.invert_yaxis(); ax.set_xlim(0, 5.25); ax.set_xticks(range(6))
    ax.set_xlabel("Seeds favouring SCRF / 5")
    for i, v in enumerate(better): ax.text(v + 0.10, i, f"{v}/5", va="center", fontsize=6.2, color=COL_DARK)
    ax.grid(axis="x", color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True); panel(ax, "c")

    ax = fig.add_subplot(gs[1, 2:]); ax.axis("off")
    items = [("Coverage, anchor and SCRF", "100%", COL_TEAL), ("Empty-set residual error", "0", COL_TEAL),
             ("Empty-set fused-score error", "0", COL_TEAL), ("Worst supported-pattern Brier regret", "+0.009848", COL_ORANGE),
             ("Prespecified no-harm boundary", "+0.020", COL_GREY)]
    for i, (label, val, col) in enumerate(items):
        y = 0.88 - i * 0.19
        ax.hlines(y - 0.085, 0.02, 0.98, color="#E2E7ED", linewidth=0.5)
        ax.text(0.03, y, label, fontsize=6.4, va="center", color=COL_DARK)
        ax.text(0.97, y, val, fontsize=6.8, va="center", ha="right", color=col, fontweight="bold")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    panel(ax, "d"); save(fig, "figure3_v1r_development_performance_safety")


def figure4():
    dev = load(BRIDGE); post = load(U5R8)["raw_v1r_vs_bridge"]; m = dev["metrics"]
    fig = plt.figure(figsize=(FULLW, 112 * MM))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.1, 1, 1], left=0.075, right=0.985, top=0.91, bottom=0.10, wspace=0.42, hspace=0.55)
    ax = fig.add_subplot(gs[0, 0])
    labels = ["IPCW\nBrier24", "|CITL|", "|slope − 1|"]
    raw = [m["ipcw_brier24_raw"], abs(m["citl_raw"]), abs(m["calibration_slope_raw"] - 1)]
    bridge = [m["ipcw_brier24_candidate"], abs(m["citl_candidate"]), abs(m["calibration_slope_candidate"] - 1)]
    xx = np.arange(3)
    ax.bar(xx - 0.18, raw, width=0.34, color=COL_BLUE, label="Raw SCRF"); ax.bar(xx + 0.18, bridge, width=0.34, color=COL_TEAL, label="Monotone bridge")
    for i in range(3):
        ax.text(i - 0.18, raw[i] + 0.006, f"{raw[i]:.3f}", ha="center", fontsize=5.8, color=COL_BLUE)
        ax.text(i + 0.18, bridge[i] + 0.006, f"{bridge[i]:.3f}", ha="center", fontsize=5.8, color=COL_TEAL)
    ax.set_xticks(xx, labels); ax.set_ylabel("Error (smaller is better)"); ax.set_ylim(0, 0.19)
    ax.legend(loc="upper left"); clean_axes(ax); ax.set_title("Development-only diagnostic (U5R7)", loc="left", color=COL_DARK); panel(ax, "a")

    ax = fig.add_subplot(gs[0, 1])
    vals = [m["delta_ipcw_brier24"], m["worst_supported_pattern_regret"]]
    thresholds = [dev["gates"]["global_delta_ipcw_brier_max"], dev["gates"]["supported_pattern_regret_max"]]
    labels = ["Global Brier\nchange", "Worst supported-\npattern regret"]; xx = np.arange(2)
    ax.bar(xx - 0.13, vals, width=0.25, color=COL_BLUE, label="Observed"); ax.bar(xx + 0.13, thresholds, width=0.25, color=COL_LIGHT, label="Gate")
    for i, v in enumerate(vals): ax.text(i - 0.13, v + 0.00012, f"{v:+.4f}", ha="center", fontsize=6.0)
    for i, v in enumerate(thresholds): ax.text(i + 0.13, v + 0.00012, f"{v:+.3f}", ha="center", fontsize=6.0, color=COL_GREY)
    ax.axhline(0, color=COL_DARK, linewidth=0.55); ax.set_xticks(xx, labels); ax.set_ylabel("Brier regret"); ax.set_ylim(0, 0.006)
    ax.legend(loc="upper left"); clean_axes(ax); panel(ax, "b")

    ax = fig.add_subplot(gs[0, 2]); post_labels = ["IPCW\nBrier24", "|CITL|", "|slope ? 1|"]; xx = np.arange(3)
    raw = [post["ipcw_brier_raw"], abs(post["citl_raw"]), abs(post["calibration_slope_raw"] - 1)]
    bridge = [post["ipcw_brier_bridge"], abs(post["citl_bridge"]), abs(post["calibration_slope_bridge"] - 1)]; post_labels = ["IPCW\nBrier24", "|CITL|", "|slope − 1|"]; xx = np.arange(3)
    ax.bar(xx - 0.18, raw[:2] + [raw[2]], width=0.34, color=COL_BLUE, label="Raw SCRF"); ax.bar(xx + 0.18, bridge, width=0.34, color=COL_ORANGE, label="Frozen bridge")
    for i in range(3):
        ax.text(i - 0.18, raw[i] + 0.025, f"{raw[i]:.3f}", ha="center", fontsize=5.8, color=COL_BLUE)
        ax.text(i + 0.18, bridge[i] + 0.025, f"{bridge[i]:.3f}", ha="center", fontsize=5.8, color=COL_ORANGE)
    ax.set_xticks(xx, post_labels); ax.set_ylabel("Error (smaller is better)"); ax.set_ylim(0, 0.82)
    ax.legend(loc="upper left"); clean_axes(ax); ax.set_title("U5R8 post-unseal validation", loc="left", color=COL_DARK); panel(ax, "c")

    ax = fig.add_subplot(gs[1, 0]); p = np.linspace(0.001, 0.55, 400); alpha = -0.1450337985699547
    pb = 1 / (1 + np.exp(-(alpha + 0.90 * np.log(p / (1 - p)))))
    ax.plot(p * 100, p * 100, color=COL_GREY, linewidth=0.8, label="Identity"); ax.plot(p * 100, pb * 100, color=COL_TEAL, linewidth=1.1, label="β=0.90 bridge")
    ax.set_xlabel("Raw SCRF 24-month risk (%)"); ax.set_ylabel("Bridged risk (%)"); ax.set_xlim(0, 55); ax.set_ylim(0, 55)
    ax.legend(loc="upper left"); ax.grid(color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True); panel(ax, "d")

    ax = fig.add_subplot(gs[1, 1:])
    change_labels = ["IPCW Brier", "|CITL|", "|slope - 1|"]
    changes = [
        post["ipcw_brier_bridge"] - post["ipcw_brier_raw"],
        abs(post["citl_bridge"]) - abs(post["citl_raw"]),
        abs(post["calibration_slope_bridge"] - 1)
        - abs(post["calibration_slope_raw"] - 1),
    ]
    yy = np.arange(len(changes))
    ax.axvline(0, color=COL_DARK, linewidth=0.65)
    ax.hlines(yy, 0, changes, color=COL_ORANGE, linewidth=1.4)
    ax.scatter(changes, yy, s=28, color=COL_ORANGE, zorder=3)
    for y, value in zip(yy, changes, strict=True):
        ax.text(value + 0.008, y, f"{value:+.4f}", va="center", fontsize=6.2, color=COL_DARK)
    ax.set_yticks(yy, change_labels); ax.invert_yaxis(); ax.set_xlim(-0.03, 0.22)
    ax.set_xlabel("Change after frozen bridge (positive = larger error)")
    ax.grid(axis="x", color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True)
    ax.set_title("U5R8 transport of the probability scale", loc="left", color=COL_DARK); panel(ax, "e")
    save(fig, "figure4_calibration_bridge_development_and_transport")


def figure5():
    d = load(LOCKED); metrics = d; boot = d["bootstrap"]
    fig, axes = plt.subplots(1, 2, figsize=(FULLW, 72 * MM), gridspec_kw={"width_ratios": [1.05, 1.25], "left": 0.075, "right": 0.98, "top": 0.85, "bottom": 0.17, "wspace": 0.35})
    ax = axes[0]; labels = ["Uno C", "IPCW\nBrier", "AUC24", "Harrell C"]; keys = ["uno_c_24m", "ipcw_brier_24m", "auc_24m", "harrell_c"]
    v0 = [metrics["V0"][k] for k in keys]; v1 = [metrics["V1R"][k] for k in keys]; xx = np.arange(4)
    ax.plot(xx, v0, "o", ms=4.2, color=COL_GREY, label="Clinical anchor"); ax.plot(xx, v1, "o", ms=4.2, color=COL_BLUE, label="Raw SCRF")
    for i, (a, b) in enumerate(zip(v0, v1)): ax.plot([i, i], [a, b], color="#B8C4D2", linewidth=0.8, zorder=0)
    ax.set_xticks(xx, labels); ax.set_ylabel("Locked-cohort estimate"); ax.legend(loc="center left"); clean_axes(ax)
    ax.text(0.01, 1.06, "Brier lower is better; other metrics higher are better", transform=ax.transAxes, fontsize=6.0, color=COL_GREY); panel(ax, "a")

    ax = axes[1]
    rows = [("Δ Uno C", boot["uno_c_24m"]), ("Δ IPCW Brier", boot["ipcw_brier_24m"]), ("Δ AUC24", boot["auc_24m"]), ("Δ Harrell C", boot["harrell_c"])]
    yy = np.arange(len(rows))
    for y, (label, b) in enumerate(rows):
        mean, lo, hi = b["mean"], b["ci95_lower"], b["ci95_upper"]; col = COL_TEAL if "Brier" in label else COL_BLUE
        ax.hlines(y, lo, hi, color=col, linewidth=1.5); ax.plot([lo, lo], [y - 0.10, y + 0.10], color=col, linewidth=1.2); ax.plot([hi, hi], [y - 0.10, y + 0.10], color=col, linewidth=1.2)
        ax.scatter(mean, y, s=20, color=col, zorder=3); ax.text(hi + 0.006, y, f"{mean:+.4f}  [{lo:+.4f}, {hi:+.4f}]", va="center", fontsize=6.0, color=COL_DARK)
    ax.axvline(0, color=COL_DARK, linewidth=0.7); ax.set_yticks(yy, [r[0] for r in rows]); ax.invert_yaxis(); ax.set_xlim(-0.085, 0.115)
    ax.set_xlabel("Raw SCRF − clinical anchor (bootstrap 95% interval)"); ax.grid(axis="x", color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True)
    ax.text(0.01, 1.06, "All intervals cross zero; estimates are directional", transform=ax.transAxes, fontsize=6.3, color=COL_GREY); panel(ax, "b")
    save(fig, "figure5_locked_raw_v1r_confirmation")

def extfig1():
    d = load(U6); policies = d["policies"]
    fig = plt.figure(figsize=(FULLW, 78 * MM))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.9], left=0.09, right=0.98, top=0.86, bottom=0.19, wspace=0.55)
    selected = [p for p in policies if p["spec"] != "V0_reference"]
    labels = []
    for p in selected:
        if p["spec"] == "raw_V1R_reference": labels.append("Raw SCRF")
        else:
            name = "reliability" if p["spec"].endswith("prediction_instability") else "core"
            labels.append(f"{name}\nτ={p['threshold']:.1f}")
    xx = np.arange(len(selected)); vals = [p["delta_vs_v0"] for p in selected]
    colors = [COL_BLUE if lab == "Raw SCRF" else COL_TEAL for lab in labels]
    ax = fig.add_subplot(gs[0, :2]); ax.axhline(0, color=COL_DARK, linewidth=0.6); ax.bar(xx, vals, width=0.62, color=colors)
    besti = int(np.argmin(vals)); ax.annotate("best exploratory router", xy=(besti, vals[besti]), xytext=(besti - 0.15, vals[besti] - 0.00028), fontsize=6.0, color=COL_DARK, arrowprops=dict(arrowstyle="-", linewidth=0.5, color=COL_GREY))
    ax.set_xticks(xx, labels, rotation=35, ha="right"); ax.set_ylabel("IPCW Brier24 vs CAM"); ax.set_ylim(-0.0016, 0.00025); clean_axes(ax); panel(ax, "a")
    ax = fig.add_subplot(gs[0, 2]); v1r = next(p for p in policies if p["spec"] == "raw_V1R_reference")
    bestp = min((p for p in policies if p["spec"] != "raw_V1R_reference"), key=lambda p: p["delta_vs_v0"])
    bs = next(b for b in d["bootstrap"]["summary"] if b["spec"] == bestp["spec"] and b["threshold"] == bestp["threshold"])
    ax.scatter([v1r["delta_vs_v0"]], [0], s=30, color=COL_BLUE, label="Raw SCRF"); ax.scatter([bestp["delta_vs_v0"]], [1], s=30, color=COL_TEAL, label="Best router")
    ax.errorbar([bs["delta_vs_v0_ci95_lower"]], [1], xerr=[[bs["delta_vs_v0_ci95_upper"] - bs["delta_vs_v0_ci95_lower"]]], fmt="none", ecolor=COL_TEAL, elinewidth=1.2, capsize=2.5)
    ax.axvline(0, color=COL_DARK, linewidth=0.65); ax.set_yticks([0, 1], ["Raw SCRF", "Router"]); ax.set_xlabel("Brier delta vs CAM (95% CI shown for router)")
    ax.grid(axis="x", color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True); ax.text(0.02, 1.06, "Interval crosses zero; exploratory", transform=ax.transAxes, fontsize=6.2, color=COL_RED); panel(ax, "b")
    save(fig, "extended_data_figure1_router_exploration")


def extfig2():
    d = load(U7); rows = d["metrics"]
    fig = plt.figure(figsize=(FULLW, 90 * MM)); gs = fig.add_gridspec(2, 2, left=0.08, right=0.98, top=0.90, bottom=0.10, wspace=0.38, hspace=0.62)
    panels = [("a", "IPCW Brier (lower is better)", "ipcw_brier"), ("b", "Uno C (higher is better)", "uno_c"), ("c", "AUC at horizon (higher is better)", "auc_horizon"), ("d", "Calibration slope (target=1)", "calibration_slope")]
    models = [r["model"] for r in rows]; palette = dict(zip(models, COLS))
    for idx, (lab, title, key) in enumerate(panels):
        ax = fig.add_subplot(gs[idx // 2, idx % 2]); vals = [r[key] for r in rows]
        ax.bar(models, vals, width=0.58, color=[palette[m] for m in models])
        if key == "calibration_slope": ax.axhline(1, color=COL_DARK, linestyle="--", linewidth=0.7)
        for i, v in enumerate(vals): ax.text(i, v + (max(vals) - min(vals)) * 0.025, f"{v:.3f}", ha="center", fontsize=6.0)
        ax.set_ylim(min(min(vals), 0) * 0.95, max(vals) * 1.12); ax.set_ylabel(title)
        ax.grid(axis="y", color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True); panel(ax, lab)
    fig.suptitle("RADCURE held-out test: adapted clinical/radiomics comparators (descriptive characterization; not current-SCRF validation)", x=0.08, y=0.975, ha="left", fontsize=7.5, fontweight="bold", color=COL_DARK)
    save(fig, "extended_data_figure2_radcure_characterization")


def extfig3():
    d = load(U8); s = d["results"]["across_seed_summary"]; seeds = d["results"]["per_seed_metrics"]; gate = d["complexity_gate"]["decision"]
    fig = plt.figure(figsize=(FULLW, 88 * MM)); gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.3, 0.85], left=0.08, right=0.98, top=0.87, bottom=0.19, wspace=0.52)
    ax = fig.add_subplot(gs[0, 0]); metrics = [("Brier24", "ipcw_brier_24m"), ("Uno C24", "uno_c_24m"), ("AUC24", "auc_24m")]
    xx = np.arange(len(metrics)); v0 = [s[k]["V0_mean"] for _, k in metrics]; t1 = [s[k]["T1R_mean"] for _, k in metrics]
    ax.plot(xx, v0, "o", ms=4, color=COL_GREY, label="Clinical anchor"); ax.plot(xx, t1, "o", ms=4, color=COL_PURPLE, label="tSCRF")
    for i in range(len(metrics)): ax.plot([i, i], [v0[i], t1[i]], color="#B8C4D2", linewidth=0.8)
    ax.set_xticks(xx, [m for m, _ in metrics]); ax.set_ylabel("TCGA-HNSC mean"); ax.legend(loc="upper left"); clean_axes(ax); panel(ax, "a")
    ax = fig.add_subplot(gs[0, 1]); colors = [COL_BLUE, COL_PURPLE, COL_TEAL]
    for j, (_, key) in enumerate(metrics):
        vals = [z["delta_T1R_minus_V0"][key] for z in seeds]
        ax.scatter(np.full(len(vals), j) + np.linspace(-0.10, 0.10, len(vals)), vals, s=10, color=colors[j], alpha=.8); ax.hlines(np.mean(vals), j - .2, j + .2, color=colors[j], linewidth=1.2)
    ax.axhline(0, color=COL_DARK, linewidth=.65); ax.set_xticks(range(len(metrics)), [m for m, _ in metrics]); ax.set_ylabel("tSCRF − anchor")
    ax.grid(axis="y", color="#E2E7ED", linewidth=.45); ax.set_axisbelow(True); panel(ax, "b")
    ax = fig.add_subplot(gs[0, 2]); ax.axis("off")
    facts = [("Cohort", f"n={d['estimand']['eligible_n']}"), ("Deaths", f"{d['estimand']['events']}"), ("Cross-fitting", "5×5 outer; inner 3-fold"), ("Complexity gate", gate.replace("_", " ").lower()), ("Claim boundary", "Post-hoc method replication")]
    for i, (a, b) in enumerate(facts):
        y = .82 - i * .18; ax.text(.02, y, a, fontsize=6.4, color=COL_GREY, va="center"); ax.text(1.0, y, b, fontsize=6.5, color=COL_DARK, va="center", ha="right"); ax.hlines(y - .08, .02, 1, color="#E2E7ED", linewidth=.45)
    panel(ax, "c"); save(fig, "extended_data_figure3_t1r_transcriptome_replication")


def extfig4():
    d = load(U8E); cohorts = d["cohorts"]
    fig = plt.figure(figsize=(FULLW, 85 * MM)); gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1, 1], left=0.08, right=.98, top=.86, bottom=.20, wspace=.45)
    ax = fig.add_subplot(gs[0, 0]); labels = ["Brier24", "Uno C24", "AUC24", "Harrell C"]; keys = ["ipcw_brier_24m", "uno_c_24m", "auc_24m", "harrell_c"]
    x = np.arange(len(keys)); width = .34
    for i, c in enumerate(cohorts):
        vals = [c["delta_T1R_minus_V0"][k] for k in keys]; ax.bar(x + (i - .5) * width, vals, width=width, label=f"{c['cohort']} (n={c['n']})", color=[COL_PURPLE, COL_TEAL][i])
    ax.axhline(0, color=COL_DARK, linewidth=.65); ax.set_xticks(x, labels, rotation=20, ha="right"); ax.set_ylabel("tSCRF − CAM"); ax.legend(loc="upper left"); clean_axes(ax); panel(ax, "a")
    ax = fig.add_subplot(gs[0, 1])
    for i, c in enumerate(cohorts):
        a = abs(c["V0_metrics"]["calibration_in_the_large_24m"]); b = abs(c["T1R_metrics"]["calibration_in_the_large_24m"])
        ax.scatter(a, i, s=25, color=COL_GREY, label="CAM" if i == 0 else None); ax.scatter(b, i, s=25, color=COL_PURPLE, label="tSCRF" if i == 0 else None); ax.plot([a, b], [i, i], color="#B8C4D2", linewidth=.8)
    ax.set_yticks(range(len(cohorts)), [c["cohort"] for c in cohorts]); ax.set_xlabel("|Calibration-in-the-large| (closer to 0 is better)")
    ax.grid(axis="x", color="#E2E7ED", linewidth=.45); ax.set_axisbelow(True); ax.legend(loc="lower right"); panel(ax, "b")
    ax = fig.add_subplot(gs[0, 2]); ax.axis("off")
    for i, c in enumerate(cohorts):
        y = .80 - i * .35; ax.text(.0, y, c["cohort"], fontsize=7, fontweight="bold", color=COL_DARK); ax.text(.0, y-.10, f"n={c['n']}; deaths={c['events']}", fontsize=6.3, color=COL_GREY); ax.text(.0, y-.20, "Post-hoc descriptive characterization", fontsize=6.3, color=COL_RED)
    ax.text(.0, .11, "No formal external-validation claim", fontsize=6.5, color=COL_RED, fontweight="bold"); panel(ax, "c")
    save(fig, "extended_data_figure4_geo_t1r_characterization")


def extfig5():
    """Aggregate evidence-pattern stability without exposing patient-level records."""
    d = load(U2)
    rows = [r for r in d["results"]["pattern_stratified_metrics"] if r["metric_support"]]
    seeds = sorted({int(r["repetition_seed"]) for r in rows})
    patterns = sorted({r["acquisition_pattern"] for r in rows})
    lookup = {(r["acquisition_pattern"], int(r["repetition_seed"])): r for r in rows}
    brier = np.array([[lookup[(p, s)]["delta_V1_minus_V0"]["ipcw_brier_24m"] for s in seeds] for p in patterns])
    uno = np.array([[lookup[(p, s)]["delta_V1_minus_V0"]["uno_c_24m"] for s in seeds] for p in patterns])

    fig = plt.figure(figsize=(FULLW, 116 * MM))
    gs = fig.add_gridspec(2, 2, left=0.085, right=0.95, top=0.92, bottom=0.10,
                          wspace=0.40, hspace=0.52, height_ratios=[1, 0.92])

    def delta_heatmap(ax, values, title, good_when_positive):
        limit = max(abs(float(np.nanmin(values))), abs(float(np.nanmax(values))))
        cmap = "RdYlGn" if good_when_positive else "RdYlGn_r"
        im = ax.imshow(values, cmap=cmap, vmin=-limit, vmax=limit, aspect="auto")
        ax.set_xticks(range(len(seeds)), [str(s) for s in seeds])
        ax.set_yticks(range(len(patterns)), patterns)
        ax.set_xlabel("Repetition seed")
        ax.set_ylabel("Acquisition pattern\n(Blood-ICD-TMA)")
        ax.set_title(title, loc="left", color=COL_DARK)
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                ax.text(j, i, f"{values[i, j]:+.3f}", ha="center", va="center",
                        fontsize=5.7, color=COL_DARK)
        cb = fig.colorbar(im, ax=ax, fraction=0.038, pad=0.025)
        cb.ax.tick_params(labelsize=5.6)
        return ax

    ax = fig.add_subplot(gs[0, 0])
    delta_heatmap(ax, brier, "IPCW Brier change (lower is favourable)", False)
    panel(ax, "a")
    ax = fig.add_subplot(gs[0, 1])
    delta_heatmap(ax, uno, "Uno C change (higher is favourable)", True)
    panel(ax, "b")

    ax = fig.add_subplot(gs[1, 0])
    penalties = [0.01, 0.1, 1.0]
    scales = [0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
    counts = np.zeros((len(penalties), len(scales)), dtype=int)
    for item in d["results"]["v1_selection_frequency"]:
        counts[penalties.index(float(item["residual_penalty"])), scales.index(float(item["residual_scale"]))] += int(item["outer_fold_count"])
    im = ax.imshow(counts, cmap="Blues", vmin=0, vmax=max(1, int(counts.max())), aspect="auto")
    ax.set_xticks(range(len(scales)), [f"{x:g}" for x in scales])
    ax.set_yticks(range(len(penalties)), [f"{x:g}" for x in penalties])
    ax.set_xlabel("Inner-selected residual scale")
    ax.set_ylabel("Residual penalty")
    ax.set_title("Selection frequency across 25 outer fits", loc="left", color=COL_DARK)
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            ax.text(j, i, str(counts[i, j]), ha="center", va="center", fontsize=6.2,
                    color="white" if counts[i, j] > counts.max() / 2 else COL_DARK)
    panel(ax, "c")

    ax = fig.add_subplot(gs[1, 1])
    availability = np.array([[int(ch) for ch in p] for p in patterns])
    ax.imshow(availability, cmap=mpl.colors.ListedColormap(["#E7ECF2", COL_TEAL]), vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(3), ["Blood", "ICD", "TMA"])
    ax.set_yticks(range(len(patterns)), patterns)
    ax.set_ylabel("Supported acquisition pattern")
    ax.set_title("Evidence composition and support", loc="left", color=COL_DARK)
    for i, p in enumerate(patterns):
        r = lookup[(p, seeds[0])]
        for j, value in enumerate(availability[i]):
            ax.text(j, i, "usable" if value else "absent", ha="center", va="center",
                    fontsize=5.8, color="white" if value else COL_GREY)
        ax.text(3.05, i, f"n={r['n']}; deaths={r['events']}", va="center", fontsize=6.1, color=COL_DARK)
    ax.set_xlim(-0.5, 4.55)
    panel(ax, "d")
    save(fig, "extended_data_figure5_evidence_pattern_landscape")


def _read_comparator_rows(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def extfig6():
    """Compact performance and calibration landscape for all published comparators."""
    rows = _read_comparator_rows(U9_TABLE)
    rows.extend(r for r in _read_comparator_rows(U10_TABLE) if r["method"] != "V1R")
    label_map = {
        "COXPH": "Clinical Cox", "ENCOX": "Elastic-net Cox", "RSF": "Random survival forest",
        "GBSA": "Gradient boosting", "XGBCOX": "XGBoost-Cox", "DEEPSURV": "DeepSurv",
        "DEEPHIT": "DeepHit", "MULTISURV": "MultiSurv", "EARLY_FUSION": "Early fusion",
        "LATE_FUSION": "Late fusion", "MASKED_ATTENTION": "Masked attention",
        "BILINEAR_FUSION": "Bilinear fusion", "RUFFINI2026": "Missing-aware fusion",
        "HAF2026": "HAF", "V1R": "PATTERN-Surv-HN (SCRF)",
    }
    methods = [r["method"] for r in rows]
    labels = [label_map[m] for m in methods]
    keys = ["ipcw_brier_24m_mean", "uno_c_24m_mean", "auc_24m_mean", "harrell_c_mean"]
    metric_labels = ["IPCW Brier$_{24}$", "Uno C$_{24}$", "AUC$_{24}$", "Harrell C"]
    values = np.array([[float(r[k]) for k in keys] for r in rows])
    ranks = np.zeros_like(values, dtype=int)
    for j in range(values.shape[1]):
        order = np.argsort(values[:, j] if j == 0 else -values[:, j])
        ranks[order, j] = np.arange(1, len(rows) + 1)

    fig = plt.figure(figsize=(FULLW, 146 * MM))
    gs = fig.add_gridspec(2, 3, left=0.17, right=0.985, top=0.93, bottom=0.11,
                          width_ratios=[1.10, 1.10, 1.0], wspace=0.52, hspace=0.46)
    ax = fig.add_subplot(gs[:, :2])
    im = ax.imshow(ranks, cmap="Blues_r", vmin=1, vmax=len(rows), aspect="auto")
    ax.set_xticks(range(4), metric_labels, rotation=22, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.tick_params(axis="y", labelsize=6.2)
    for i in range(len(rows)):
        for j in range(4):
            ax.text(j, i, f"{values[i, j]:.3f}\n#{ranks[i, j]}", ha="center", va="center",
                    fontsize=5.3, color="white" if ranks[i, j] <= 5 else COL_DARK)
    ax.set_title("Same-fold performance: estimate and rank", loc="left", color=COL_DARK)
    cb = fig.colorbar(im, ax=ax, fraction=0.028, pad=0.025)
    cb.set_label("Rank (1 = best)")
    panel(ax, "a")

    ax = fig.add_subplot(gs[0, 2])
    colors = [COL_BLUE if m == "V1R" else (COL_PURPLE if m in {"EARLY_FUSION", "LATE_FUSION", "MASKED_ATTENTION", "BILINEAR_FUSION", "RUFFINI2026", "HAF2026"} else COL_GREY) for m in methods]
    ax.scatter(values[:, 0], values[:, 1], c=colors, s=23, edgecolor="white", linewidth=0.4, zorder=3)
    annotation_offsets = {
        "RSF": (4, 4), "ENCOX": (-2, -9), "V1R": (5, -3),
        "MASKED_ATTENTION": (6, 7), "BILINEAR_FUSION": (7, -10),
    }
    for i, m in enumerate(methods):
        short = {"V1R": "SCRF", "RSF": "RSF", "ENCOX": "EN-Cox", "MASKED_ATTENTION": "MaskAttn", "BILINEAR_FUSION": "Bilinear"}.get(m)
        if short:
            ax.annotate(short, (values[i, 0], values[i, 1]), xytext=annotation_offsets[m],
                        textcoords="offset points", fontsize=5.7)
    ax.set_xlabel("IPCW Brier$_{24}$ (lower)")
    ax.set_ylabel("Uno C$_{24}$ (higher)")
    ax.grid(color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True)
    ax.set_title("Joint accuracy profile", loc="left", color=COL_DARK)
    panel(ax, "b")

    ax = fig.add_subplot(gs[1, 2])
    citl = np.array([abs(float(r["calibration_in_the_large_24m_mean"])) for r in rows])
    slope = np.array([abs(float(r["calibration_slope_24m_mean"]) - 1.0) for r in rows])
    ax.scatter(citl, slope + 1e-5, c=colors, s=23, edgecolor="white", linewidth=0.4, zorder=3)
    for i, m in enumerate(methods):
        if m in {"V1R", "ENCOX", "RSF", "DEEPSURV", "DEEPHIT"}:
            short = {"V1R": "SCRF", "ENCOX": "EN-Cox", "RSF": "RSF", "DEEPSURV": "DeepSurv", "DEEPHIT": "DeepHit"}[m]
            ax.annotate(short, (citl[i], slope[i] + 1e-5), xytext=(3, 1), textcoords="offset points", fontsize=5.6)
    ax.set_yscale("log")
    ax.set_xlabel("|Calibration-in-the-large|")
    ax.set_ylabel("|Calibration slope − 1| (log scale)")
    ax.grid(color="#E2E7ED", linewidth=0.45); ax.set_axisbelow(True)
    ax.set_title("Probability-scale behaviour", loc="left", color=COL_DARK)
    panel(ax, "c")
    save(fig, "extended_data_figure6_published_comparator_landscape")


def main():
    source_fig = ROOT / "trust-hn/paper/figures/figure1_pattern_surv_hn_framework.pdf"
    if source_fig.exists():
        for ext in ("pdf", "png", "pptx"):
            src = source_fig.with_suffix("." + ext)
            if src.exists():
                dst = FIGDIR / src.name
                if dst.exists(): dst.chmod(0o666)
                shutil.copy2(src, dst)
    figure1(); figure2(); figure3(); figure4(); figure5(); extfig1(); extfig2(); extfig3(); extfig4(); extfig5(); extfig6()
    manifest = {"standard": "npj Digital Medicine / Nature Portfolio style; 183 mm double-column width; Arial; vector PDF plus 600-dpi PNG", "data_boundary": "All generated figures read aggregate JSON artifacts only; no patient-level predictions are included.", "figures": [
        {"number": 1, "file": "figure2_cohort_flow_acquisition_usability.pdf", "source": U1, "claim": "descriptive cohort and availability/usability audit"},
        {"number": 2, "file": "figure3_v1r_development_performance_safety.pdf", "source": U2, "claim": "development-only repeated nested cross-fitting"},
        {"number": 3, "file": "figure4_calibration_bridge_development_and_transport.pdf", "source": [BRIDGE, U5R8], "claim": "U5R7 development-only; U5R8 probability-scale transport estimates"},
        {"number": 4, "file": "figure5_locked_raw_v1r_confirmation.pdf", "source": LOCKED, "claim": "locked outcome-untouched raw-V1R directional signal; intervals cross zero"},
        {"number": 5, "file": "figure1_pattern_surv_hn_framework.pdf", "source": "publication diagram generated from the frozen method specification", "claim": "Methods architecture; raw SCRF is primary; bridge development-only; router exploratory"},
        {"number": 1, "extended": True, "file": "extended_data_figure1_router_exploration.pdf", "source": U6, "claim": "exploratory development router only"},
        {"number": 2, "extended": True, "file": "extended_data_figure2_radcure_characterization.pdf", "source": U7, "claim": "descriptive adapted-comparator characterization, not current-V1R validation"},
        {"number": 3, "extended": True, "file": "extended_data_figure3_t1r_transcriptome_replication.pdf", "source": U8, "claim": "post-hoc TCGA-HNSC method replication"},
        {"number": 4, "extended": True, "file": "extended_data_figure4_geo_t1r_characterization.pdf", "source": U8E, "claim": "post-hoc descriptive GEO characterization"},
        {"number": 5, "extended": True, "file": "extended_data_figure5_evidence_pattern_landscape.pdf", "source": U2, "claim": "aggregate supported-pattern stability and inner-selection landscape"},
        {"number": 6, "extended": True, "file": "extended_data_figure6_published_comparator_landscape.pdf", "source": [U9_TABLE, U10_TABLE], "claim": "post-hoc same-fold published-method performance and calibration landscape"}]}
    (FIGDIR / "figure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8"); print("saved figure_manifest.json")


if __name__ == "__main__":
    main()

