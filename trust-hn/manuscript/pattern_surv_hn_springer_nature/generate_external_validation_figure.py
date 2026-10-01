"""Generate the aggregate-only external-validation figure for PATTERN-Surv-HN."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch


BLUE = HexColor("#2F5D9F")
GREY = HexColor("#758397")
LIGHT_GREY = HexColor("#DCE4ED")
DARK = HexColor("#24344F")
GREEN = HexColor("#138A72")
PALE = HexColor("#F5F8FB")


def text(c, x, y, value, size=9, color=black, font="Helvetica", align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "center":
        c.drawCentredString(x, y, value)
    elif align == "right":
        c.drawRightString(x, y, value)
    else:
        c.drawString(x, y, value)


def panel_label(c, x, y, label):
    text(c, x, y, label, size=15, color=DARK, font="Helvetica-Bold")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("aggregate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.aggregate.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)

    width, height = 14 * inch, 7.1 * inch
    c = canvas.Canvas(str(args.output), pagesize=(width, height))
    c.setTitle("PATTERN-Surv-HN independent external validation")
    c.setFillColor(white)
    c.rect(0, 0, width, height, stroke=0, fill=1)

    margin = 0.45 * inch
    gap = 0.32 * inch
    panel_w = (width - 2 * margin - gap) / 2
    panel_h = (height - 2 * margin - gap) / 2
    panels = {
        "a": (margin, margin + panel_h + gap, panel_w, panel_h),
        "b": (margin + panel_w + gap, margin + panel_h + gap, panel_w, panel_h),
        "c": (margin, margin, panel_w, panel_h),
        "d": (margin + panel_w + gap, margin, panel_w, panel_h),
    }

    metrics = data["metrics"]
    cam = metrics["CAM"]
    scrf = metrics["SCRF"]
    delta = metrics["SCRF_minus_CAM"]
    ci = metrics["paired_bootstrap_95ci_from_workbook"]

    # Panel a: paired external performance.
    x, y, w, h = panels["a"]
    panel_label(c, x, y + h - 16, "a")
    text(c, x + 28, y + h - 16, "External-cohort performance", 11, GREY)
    left, bottom, plot_w, plot_h = x + 45, y + 38, w - 65, h - 78
    c.setStrokeColor(LIGHT_GREY)
    c.setLineWidth(0.7)
    for tick in np_arange(0.1, 0.9, 0.1):
        py = bottom + (tick - 0.1) / 0.75 * plot_h
        c.line(left, py, left + plot_w, py)
        text(c, left - 8, py - 3, f"{tick:.1f}", 7.5, DARK, align="right")
    c.setStrokeColor(black)
    c.line(left, bottom, left, bottom + plot_h)
    categories = [
        ("Uno C", cam["uno_c_24m"], scrf["uno_c_24m"]),
        ("IPCW\nBrier", cam["ipcw_brier_24m"], scrf["ipcw_brier_24m"]),
        ("AUC24", cam["auc_24m"], scrf["auc_24m"]),
        ("Harrell C", cam["harrell_c"], scrf["harrell_c"]),
    ]
    for index, (label, cam_value, scrf_value) in enumerate(categories):
        px = left + (index + 0.5) * plot_w / len(categories)
        for value, color, offset in ((cam_value, GREY, -4), (scrf_value, BLUE, 4)):
            py = bottom + (value - 0.1) / 0.75 * plot_h
            c.setFillColor(color)
            c.circle(px + offset, py, 4.2, stroke=0, fill=1)
        for j, line in enumerate(label.split("\n")):
            text(c, px, bottom - 14 - j * 9, line, 8, DARK, align="center")
    c.setFillColor(GREY)
    c.circle(left + 16, bottom + plot_h - 12, 3.5, stroke=0, fill=1)
    text(c, left + 27, bottom + plot_h - 15, "CAM", 8.5, DARK)
    c.setFillColor(BLUE)
    c.circle(left + 74, bottom + plot_h - 12, 3.5, stroke=0, fill=1)
    text(c, left + 85, bottom + plot_h - 15, "SCRF", 8.5, DARK)

    # Panel b: paired bootstrap intervals.
    x, y, w, h = panels["b"]
    panel_label(c, x, y + h - 16, "b")
    text(c, x + 28, y + h - 16, "Paired differences and 95% intervals", 11, GREY)
    left, bottom, plot_w, plot_h = x + 95, y + 35, w - 145, h - 70
    xmin, xmax = -0.03, 0.14
    c.setStrokeColor(LIGHT_GREY)
    for tick in [-0.025, 0, 0.025, 0.05, 0.075, 0.10, 0.125]:
        px = left + (tick - xmin) / (xmax - xmin) * plot_w
        c.line(px, bottom, px, bottom + plot_h)
        text(c, px, bottom - 13, f"{tick:+.3f}" if tick else "0", 7.5, DARK, align="center")
    zero_x = left + (0 - xmin) / (xmax - xmin) * plot_w
    c.setStrokeColor(DARK)
    c.setLineWidth(1.2)
    c.line(zero_x, bottom, zero_x, bottom + plot_h)
    rows = [
        ("Delta Uno C", "uno_c_24m", BLUE),
        ("Delta IPCW Brier", "ipcw_brier_24m", GREEN),
        ("Delta AUC24", "auc_24m", BLUE),
        ("Delta Harrell C", "harrell_c", BLUE),
    ]
    for index, (label, key, color) in enumerate(rows):
        py = bottom + plot_h - (index + 0.55) * plot_h / len(rows)
        lo = ci[key]["ci_lower"]
        hi = ci[key]["ci_upper"]
        est = delta[key]
        lx = left + (lo - xmin) / (xmax - xmin) * plot_w
        hx = left + (hi - xmin) / (xmax - xmin) * plot_w
        ex = left + (est - xmin) / (xmax - xmin) * plot_w
        text(c, left - 10, py - 3, label, 8.4, DARK, align="right")
        c.setStrokeColor(color)
        c.setLineWidth(2.1)
        c.line(lx, py, hx, py)
        c.line(lx, py - 5, lx, py + 5)
        c.line(hx, py - 5, hx, py + 5)
        c.setFillColor(color)
        c.circle(ex, py, 4.2, stroke=0, fill=1)
        text(c, left + plot_w + 8, py - 3, f"{est:+.3f}", 8.2, DARK)

    # Panel c: natural optional-modality patterns.
    x, y, w, h = panels["c"]
    panel_label(c, x, y + h - 16, "c")
    text(c, x + 28, y + h - 16, "Natural usability patterns", 11, GREY)
    patterns = sorted(data["patterns"], key=lambda row: str(row["usable_pattern"]).zfill(3))
    left, bottom, plot_w, plot_h = x + 52, y + 30, w - 80, h - 68
    max_n = max(int(row["n"]) for row in patterns)
    bar_h = plot_h / len(patterns) * 0.58
    for index, row in enumerate(patterns):
        label = str(int(row["usable_pattern"])).zfill(3)
        py = bottom + plot_h - (index + 0.72) * plot_h / len(patterns)
        length = int(row["n"]) / max_n * plot_w
        text(c, left - 9, py + 1, label, 8.3, DARK, align="right")
        c.setFillColor(BLUE if row["supported_n30_events10"] else GREY)
        c.rect(left, py - bar_h / 2, length, bar_h, stroke=0, fill=1)
        text(c, left + length + 5, py - 2, str(int(row["n"])), 8, DARK)
    text(c, left, bottom - 14, "Pattern order: blood-ICD-TMA; blue meets n>=30 and events>=10", 7.6, GREY)

    # Panel d: safety and calibration interpretation.
    x, y, w, h = panels["d"]
    panel_label(c, x, y + h - 16, "d")
    text(c, x + 28, y + h - 16, "Coverage, safety and calibration", 11, GREY)
    box_x, box_y, box_w, box_h = x + 24, y + 30, w - 44, h - 70
    c.setFillColor(PALE)
    c.roundRect(box_x, box_y, box_w, box_h, 6, stroke=0, fill=1)
    lines = [
        ("Prediction coverage", "100% for CAM and SCRF", GREEN),
        ("Empty-set fallback", "Exact CAM score and risk", GREEN),
        ("Worst supported-pattern Brier change", f"{min(float(r['delta_brier']) for r in patterns if r['supported_n30_events10']):+.4f}", GREEN),
        ("Calibration-in-the-large", f"CAM {cam['calibration_in_the_large_24m']:+.3f}; SCRF {scrf['calibration_in_the_large_24m']:+.3f}", BLUE),
        ("Calibration slope", f"CAM {cam['calibration_slope_24m']:.3f}; SCRF {scrf['calibration_slope_24m']:.3f}", GREY),
    ]
    for index, (label, value, color) in enumerate(lines):
        py = box_y + box_h - 23 - index * 28
        c.setFillColor(color)
        c.circle(box_x + 12, py + 4, 3.2, stroke=0, fill=1)
        text(c, box_x + 23, py + 7, label, 8.2, DARK, font="Helvetica-Bold")
        text(c, box_x + 23, py - 5, value, 8.2, DARK)

    c.showPage()
    c.save()


def np_arange(start: float, stop: float, step: float):
    value = start
    while value < stop - 1e-9:
        yield round(value, 10)
        value += step


if __name__ == "__main__":
    main()
