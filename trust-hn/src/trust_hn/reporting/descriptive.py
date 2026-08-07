"""Governance-safe descriptive outputs for Phase 2."""

from __future__ import annotations

import csv
import html
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from trust_hn.data.contracts_v2 import EndpointStatus, PatientRecord, SplitRole
from trust_hn.evaluation.endpoints import HorizonStatus, classify_horizon_outcome


PUBLIC_FIELDS = ("age", "age_group", "sex", "site", "stage", "hpv", "treatment", "smoking")


def kaplan_meier_coordinates(pairs: Iterable[tuple[float, int]]) -> list[dict[str, float | int]]:
    grouped: dict[float, Counter[int]] = defaultdict(Counter)
    pairs_list = list(pairs)
    for duration, event in pairs_list:
        if duration < 0 or event not in (0, 1):
            raise ValueError("Kaplan-Meier inputs require nonnegative duration and event in {0,1}")
        grouped[float(duration)][int(event)] += 1
    at_risk = len(pairs_list)
    survival = 1.0
    points: list[dict[str, float | int]] = []
    for time in sorted(grouped):
        events = grouped[time][1]
        censored = grouped[time][0]
        if at_risk and events:
            survival *= 1.0 - events / at_risk
        points.append(
            {
                "time_days": time,
                "n_at_risk": at_risk,
                "n_events": events,
                "n_censored": censored,
                "survival_probability": survival,
            }
        )
        at_risk -= events + censored
    return points


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_private_records(path: Path, records: Sequence[PatientRecord]) -> None:
    _write_csv(path, [record.to_private_dict() for record in records])


def cohort_flow_rows(records: Sequence[PatientRecord]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for study in sorted({record.study for record in records}):
        study_records = [record for record in records if record.study == study]
        rows.append({"study": study, "flow_step": "source_records", "category": "all", "n": len(study_records)})
        rows.append({"study": study, "flow_step": "eligibility", "category": "eligible", "n": sum(record.eligible for record in study_records)})
        for reason, count in sorted(Counter(record.exclusion_reason for record in study_records if not record.eligible).items()):
            rows.append({"study": study, "flow_step": "exclusion", "category": reason, "n": count})
        for split, count in sorted(Counter(record.split_role.value for record in study_records if record.eligible).items()):
            rows.append({"study": study, "flow_step": "analysis_split", "category": split, "n": count})
    return rows


def missingness_rows(records: Sequence[PatientRecord]) -> list[dict[str, object]]:
    output = []
    eligible = [record for record in records if record.eligible]
    groups = defaultdict(list)
    for record in eligible:
        groups[(record.study, record.split_role.value)].append(record)
    for (study, split), rows in sorted(groups.items()):
        for field in PUBLIC_FIELDS:
            missing = sum(getattr(row, field) is None for row in rows)
            output.append(
                {
                    "study": study,
                    "split_role": split,
                    "field": field,
                    "n": len(rows),
                    "n_missing": missing,
                    "missing_fraction": missing / len(rows) if rows else None,
                }
            )
    return output


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quantile requires data")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def table1_candidate_rows(records: Sequence[PatientRecord]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    groups = defaultdict(list)
    for record in records:
        if record.eligible:
            groups[(record.study, record.split_role.value)].append(record)
    for (study, split), rows in sorted(groups.items()):
        ages = [row.age for row in rows if row.age is not None]
        if ages:
            for statistic, value in (
                ("mean", statistics.fmean(ages)),
                ("sd", statistics.stdev(ages) if len(ages) > 1 else 0.0),
                ("median", statistics.median(ages)),
                ("q1", _quantile(ages, 0.25)),
                ("q3", _quantile(ages, 0.75)),
            ):
                output.append({"study": study, "split_role": split, "variable": "age", "level": "", "statistic": statistic, "value": value, "n_observed": len(ages), "n_missing": len(rows) - len(ages)})
        else:
            output.append({"study": study, "split_role": split, "variable": "age", "level": "", "statistic": "not_available", "value": "", "n_observed": 0, "n_missing": len(rows)})
        for field in PUBLIC_FIELDS[1:]:
            values = [getattr(row, field) for row in rows]
            observed = [value for value in values if value is not None]
            for level, count in sorted(Counter(observed).items(), key=lambda item: str(item[0])):
                output.append({"study": study, "split_role": split, "variable": field, "level": level, "statistic": "count_percent_observed", "value": count, "percent_observed": 100 * count / len(observed) if observed else None, "n_observed": len(observed), "n_missing": len(rows) - len(observed)})
    return output


def event_summary_rows(records: Sequence[PatientRecord], horizon_days: float = 730.5) -> list[dict[str, object]]:
    output = []
    groups = defaultdict(list)
    for record in records:
        if record.eligible and record.split_role in {SplitRole.TRAIN, SplitRole.CALIBRATION}:
            groups[(record.study, record.split_role.value)].append(record)
    for (study, split), rows in sorted(groups.items()):
        usable = [row for row in rows if row.duration_days is not None and row.event is not None]
        statuses = Counter(
            classify_horizon_outcome(row.duration_days, row.event, horizon_days).status.value
            for row in usable
        )
        output.append(
            {
                "study": study,
                "split_role": split,
                "n_eligible": len(rows),
                "n_endpoint_usable": len(usable),
                "n_events_all_followup": sum(row.event for row in usable),
                "event_fraction": sum(row.event for row in usable) / len(usable) if usable else None,
                "horizon_days": horizon_days,
                HorizonStatus.EVENT_BY_HORIZON.value: statuses[HorizonStatus.EVENT_BY_HORIZON.value],
                HorizonStatus.EVENT_FREE_AT_HORIZON.value: statuses[HorizonStatus.EVENT_FREE_AT_HORIZON.value],
                HorizonStatus.CENSORED_BEFORE_HORIZON.value: statuses[HorizonStatus.CENSORED_BEFORE_HORIZON.value],
                "test_and_external_outcomes_suppressed": True,
            }
        )
    return output


def km_rows(records: Sequence[PatientRecord]) -> list[dict[str, object]]:
    output = []
    groups = defaultdict(list)
    for record in records:
        if record.eligible and record.split_role in {SplitRole.TRAIN, SplitRole.CALIBRATION} and record.endpoint_status == EndpointStatus.USABLE:
            groups[(record.study, record.split_role.value)].append((record.duration_days, record.event))
    for (study, split), pairs in sorted(groups.items()):
        for point in kaplan_meier_coordinates(pairs):
            output.append({"study": study, "split_role": split, **point})
    return output


def _svg_document(width: int, height: int, body: Sequence[str]) -> str:
    return "\n".join([f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', *body, "</svg>", ""])


def write_missingness_svg(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    groups = sorted({(str(row["study"]), str(row["split_role"])) for row in rows})
    fields = list(PUBLIC_FIELDS)
    lookup = {(str(row["study"]), str(row["split_role"]), str(row["field"])): float(row["missing_fraction"]) for row in rows}
    cell = 34; left = 210; top = 90
    body = ['<text x="20" y="30" font-family="sans-serif" font-size="20">Phase 2 missingness heatmap</text>']
    for j, field in enumerate(fields):
        body.append(f'<text x="{left+j*cell+15}" y="{top-8}" transform="rotate(-45 {left+j*cell+15},{top-8})" font-family="sans-serif" font-size="11">{html.escape(field)}</text>')
    for i, group in enumerate(groups):
        y = top + i * cell
        body.append(f'<text x="10" y="{y+22}" font-family="sans-serif" font-size="11">{html.escape(group[0]+" / "+group[1])}</text>')
        for j, field in enumerate(fields):
            fraction = lookup[(group[0], group[1], field)]
            red = int(245 - 120 * fraction); green = int(248 - 205 * fraction); blue = int(255 - 205 * fraction)
            body.append(f'<rect x="{left+j*cell}" y="{y}" width="32" height="32" fill="rgb({red},{green},{blue})" stroke="#ddd"><title>{fraction:.1%}</title></rect>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_svg_document(left + len(fields)*cell + 20, top + len(groups)*cell + 30, body), encoding="utf-8")


def write_event_svg(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    width=900; height=max(260, 80 + 55*len(rows)); body=['<text x="20" y="30" font-family="sans-serif" font-size="20">Development-only event distribution</text>']
    max_n=max((int(row["n_endpoint_usable"]) for row in rows), default=1)
    for i,row in enumerate(rows):
        y=60+i*55; events=int(row["n_events_all_followup"]); total=int(row["n_endpoint_usable"]); censored=total-events
        body.append(f'<text x="10" y="{y+17}" font-family="sans-serif" font-size="11">{html.escape(str(row["study"])+" / "+str(row["split_role"]))}</text>')
        scale=600/max_n; x=240
        body.append(f'<rect x="{x}" y="{y}" width="{events*scale:.2f}" height="22" fill="#b2182b"><title>events={events}</title></rect>')
        body.append(f'<rect x="{x+events*scale:.2f}" y="{y}" width="{censored*scale:.2f}" height="22" fill="#67a9cf"><title>censored={censored}</title></rect>')
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(_svg_document(width,height,body),encoding="utf-8")


def write_km_svg(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    width=900; height=560; left=70; top=50; plot_w=780; plot_h=440
    body=['<text x="20" y="28" font-family="sans-serif" font-size="20">Development-only Kaplan–Meier curves</text>', f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="black"/>', f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="black"/>']
    max_time=max((float(row["time_days"]) for row in rows), default=1.0)
    groups=defaultdict(list)
    for row in rows: groups[(str(row["study"]),str(row["split_role"]))].append(row)
    colors=["#2166ac","#b2182b","#1b7837","#762a83","#e08214","#008080"]
    for color,(group,points) in zip(colors*10,sorted(groups.items())):
        coords=[(left,top)]
        previous_survival=1.0
        for point in points:
            x=left+float(point["time_days"])/max_time*plot_w; y_prev=top+(1-previous_survival)*plot_h; y=top+(1-float(point["survival_probability"]))*plot_h
            coords.extend([(x,y_prev),(x,y)]); previous_survival=float(point["survival_probability"])
        path_data=" ".join(("M" if idx==0 else "L")+f"{x:.2f},{y:.2f}" for idx,(x,y) in enumerate(coords))
        body.append(f'<path d="{path_data}" fill="none" stroke="{color}" stroke-width="2"><title>{html.escape(group[0]+" / "+group[1])}</title></path>')
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(_svg_document(width,height,body),encoding="utf-8")



def composition_comparison_rows(records: Sequence[PatientRecord]) -> list[dict[str, object]]:
    """Compare covariate composition without consulting any outcomes."""
    eligible = [record for record in records if record.eligible]
    groups: dict[tuple[str, str], list[PatientRecord]] = defaultdict(list)
    for record in eligible:
        groups[(record.study, record.split_role.value)].append(record)
    comparisons = [
        (("RADCURE", "train"), ("RADCURE", "calibration")),
        (("RADCURE", "train"), ("RADCURE", "sealed_test")),
        (("HANCOCK", "train"), ("HANCOCK", "calibration")),
        (("HANCOCK", "train"), ("HANCOCK", "sealed_test")),
        (("TCGA-HNSC", "train"), ("TCGA-HNSC", "calibration")),
        (("TCGA-HNSC", "train"), ("GSE65858", "external_test")),
        (("TCGA-HNSC", "train"), ("GSE41613", "sensitivity")),
    ]
    output: list[dict[str, object]] = []
    for reference_key, comparison_key in comparisons:
        reference = groups.get(reference_key, [])
        comparison = groups.get(comparison_key, [])
        if not reference or not comparison:
            continue
        ref_age = [row.age for row in reference if row.age is not None]
        cmp_age = [row.age for row in comparison if row.age is not None]
        if len(ref_age) > 1 and len(cmp_age) > 1:
            pooled = math.sqrt((statistics.variance(ref_age) + statistics.variance(cmp_age)) / 2)
            smd = (statistics.fmean(cmp_age) - statistics.fmean(ref_age)) / pooled if pooled else 0.0
            output.append({
                "reference_study": reference_key[0], "reference_split": reference_key[1],
                "comparison_study": comparison_key[0], "comparison_split": comparison_key[1],
                "variable": "age", "metric": "standardized_mean_difference",
                "value": smd, "reference_n": len(reference), "comparison_n": len(comparison),
                "outcomes_used": False,
            })
        for field in PUBLIC_FIELDS:
            ref_missing = sum(getattr(row, field) is None for row in reference) / len(reference)
            cmp_missing = sum(getattr(row, field) is None for row in comparison) / len(comparison)
            output.append({
                "reference_study": reference_key[0], "reference_split": reference_key[1],
                "comparison_study": comparison_key[0], "comparison_split": comparison_key[1],
                "variable": field, "metric": "missing_fraction_difference",
                "value": cmp_missing - ref_missing, "reference_n": len(reference),
                "comparison_n": len(comparison), "outcomes_used": False,
            })
        for field in PUBLIC_FIELDS[1:]:
            ref_counts = Counter(str(getattr(row, field) or "__MISSING__") for row in reference)
            cmp_counts = Counter(str(getattr(row, field) or "__MISSING__") for row in comparison)
            levels = set(ref_counts) | set(cmp_counts)
            tvd = 0.5 * sum(
                abs(ref_counts[level] / len(reference) - cmp_counts[level] / len(comparison))
                for level in levels
            )
            output.append({
                "reference_study": reference_key[0], "reference_split": reference_key[1],
                "comparison_study": comparison_key[0], "comparison_split": comparison_key[1],
                "variable": field, "metric": "categorical_total_variation_distance",
                "value": tvd, "reference_n": len(reference), "comparison_n": len(comparison),
                "outcomes_used": False,
            })
    return output

def write_descriptive_outputs(results_root: Path, records: Sequence[PatientRecord]) -> dict[str, Path]:
    metrics = results_root / "metrics/phase2"; figures = results_root / "figures/phase2"
    outputs = {
        "cohort_flow": metrics / "cohort_flow.csv",
        "table1_candidates": metrics / "table1_candidates.csv",
        "missingness_summary": metrics / "missingness_summary.csv",
        "event_summary": metrics / "event_summary_development_only.csv",
        "km_coordinates": metrics / "kaplan_meier_development_only.csv",
        "composition_comparison": metrics / "composition_comparison.csv",
        "missingness_svg": figures / "missingness_heatmap.svg",
        "event_svg": figures / "event_distribution.svg",
        "km_svg": figures / "kaplan_meier_development_only.svg",
    }
    flow=cohort_flow_rows(records); table1=table1_candidate_rows(records); missing=missingness_rows(records); events=event_summary_rows(records); km=km_rows(records); composition=composition_comparison_rows(records)
    _write_csv(outputs["cohort_flow"],flow); _write_csv(outputs["table1_candidates"],table1); _write_csv(outputs["missingness_summary"],missing); _write_csv(outputs["event_summary"],events); _write_csv(outputs["km_coordinates"],km); _write_csv(outputs["composition_comparison"],composition)
    write_missingness_svg(outputs["missingness_svg"],missing); write_event_svg(outputs["event_svg"],events); write_km_svg(outputs["km_svg"],km)
    return outputs
