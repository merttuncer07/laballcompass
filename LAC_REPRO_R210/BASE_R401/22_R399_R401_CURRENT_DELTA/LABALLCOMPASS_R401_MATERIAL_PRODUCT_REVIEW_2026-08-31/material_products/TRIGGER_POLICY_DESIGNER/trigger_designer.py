"""Holdout-evaluated trigger policy designer based on the Lab's DTTC parent."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class Candidate:
    column: str
    direction: str = "high"
    verification_cost_per_trigger: float = 0.0
    manipulation_exposure: float = 0.0


@dataclass(frozen=True)
class Metrics:
    rows: int
    events: int
    triggers: int
    true_positives: int
    false_negatives: int
    false_positives: int
    true_negatives: int
    false_negative_rate: float
    false_positive_rate: float
    precision: float | None
    recall: float | None
    trigger_rate: float
    average_cost_per_row: float
    total_cost: float


def _number(value: Any, label: str, *, nonnegative: bool = False) -> float:
    result = float(value)
    if not math.isfinite(result) or (nonnegative and result < 0):
        suffix = " and non-negative" if nonnegative else ""
        raise ValueError(f"{label} must be finite{suffix}")
    return result


def _predict(value: float, threshold: float, direction: str) -> bool:
    return value >= threshold if direction == "high" else value <= threshold


def _thresholds(values: Sequence[float], direction: str) -> list[float]:
    unique = sorted(set(values))
    spread = max(1.0, unique[-1] - unique[0])
    thresholds = [unique[0] - spread, *unique, unique[-1] + spread]
    return thresholds if direction == "high" else list(reversed(thresholds))


def _metrics(
    values: Sequence[float],
    events: Sequence[bool],
    threshold: float,
    candidate: Candidate,
    *,
    false_negative_cost: float,
    false_positive_cost: float,
    manipulation_cost_weight: float,
) -> Metrics:
    predictions = [_predict(value, threshold, candidate.direction) for value in values]
    tp = sum(pred and event for pred, event in zip(predictions, events))
    fn = sum((not pred) and event for pred, event in zip(predictions, events))
    fp = sum(pred and (not event) for pred, event in zip(predictions, events))
    tn = len(events) - tp - fn - fp
    triggers = tp + fp
    event_count = tp + fn
    non_event_count = fp + tn
    total_cost = (
        fn * false_negative_cost
        + fp * false_positive_cost
        + triggers * candidate.verification_cost_per_trigger
        + len(events) * manipulation_cost_weight * candidate.manipulation_exposure
    )
    return Metrics(
        rows=len(events),
        events=event_count,
        triggers=triggers,
        true_positives=tp,
        false_negatives=fn,
        false_positives=fp,
        true_negatives=tn,
        false_negative_rate=fn / event_count if event_count else 0.0,
        false_positive_rate=fp / non_event_count if non_event_count else 0.0,
        precision=tp / triggers if triggers else None,
        recall=tp / event_count if event_count else None,
        trigger_rate=triggers / len(events),
        average_cost_per_row=total_cost / len(events),
        total_cost=total_cost,
    )


class TriggerPolicyDesigner:
    def __init__(
        self,
        false_negative_cost: float,
        false_positive_cost: float,
        manipulation_cost_weight: float = 1.0,
    ) -> None:
        self.false_negative_cost = _number(
            false_negative_cost, "false_negative_cost", nonnegative=True
        )
        self.false_positive_cost = _number(
            false_positive_cost, "false_positive_cost", nonnegative=True
        )
        self.manipulation_cost_weight = _number(
            manipulation_cost_weight, "manipulation_cost_weight", nonnegative=True
        )

    def fit(
        self,
        candidate: Candidate,
        calibration_values: Sequence[float],
        calibration_events: Sequence[bool],
    ) -> tuple[float, Metrics]:
        if candidate.direction not in {"high", "low"}:
            raise ValueError("candidate.direction must be 'high' or 'low'")
        if len(calibration_values) != len(calibration_events) or not calibration_values:
            raise ValueError("Calibration values and events must have equal non-zero length")
        verification_cost = _number(
            candidate.verification_cost_per_trigger,
            "verification_cost_per_trigger",
            nonnegative=True,
        )
        exposure = _number(candidate.manipulation_exposure, "manipulation_exposure", nonnegative=True)
        candidate = Candidate(candidate.column, candidate.direction, verification_cost, exposure)
        choices = []
        for threshold in _thresholds(calibration_values, candidate.direction):
            metrics = _metrics(
                calibration_values,
                calibration_events,
                threshold,
                candidate,
                false_negative_cost=self.false_negative_cost,
                false_positive_cost=self.false_positive_cost,
                manipulation_cost_weight=self.manipulation_cost_weight,
            )
            choices.append((metrics.average_cost_per_row, metrics.trigger_rate, threshold, metrics))
        _, _, threshold, metrics = min(choices)
        return threshold, metrics

    def evaluate(
        self,
        candidate: Candidate,
        threshold: float,
        values: Sequence[float],
        events: Sequence[bool],
    ) -> Metrics:
        if len(values) != len(events) or not values:
            raise ValueError("Evaluation values and events must have equal non-zero length")
        return _metrics(
            values,
            events,
            threshold,
            candidate,
            false_negative_cost=self.false_negative_cost,
            false_positive_cost=self.false_positive_cost,
            manipulation_cost_weight=self.manipulation_cost_weight,
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("CSV must contain at least one data row")
    return rows


def _split_indices(row_count: int, config: Mapping[str, Any]) -> tuple[list[int], list[int]]:
    split = config.get("split", {})
    method = split.get("method", "chronological")
    if method != "chronological":
        raise ValueError("v1 supports split.method='chronological'")
    fraction = float(split.get("calibration_fraction", 0.7))
    if not 0 < fraction < 1:
        raise ValueError("calibration_fraction must be between zero and one")
    cut = int(row_count * fraction)
    if cut < 2 or row_count - cut < 2:
        raise ValueError("Calibration and evaluation partitions each require at least two rows")
    return list(range(cut)), list(range(cut, row_count))


def _slice(values: Sequence[Any], indices: Sequence[int]) -> list[Any]:
    return [values[index] for index in indices]


def design_from_files(config: Mapping[str, Any], csv_path: Path) -> dict[str, Any]:
    rows = _read_csv(csv_path)
    loss_column = str(config["loss_column"])
    loss_threshold = _number(config["protected_loss_threshold"], "protected_loss_threshold")
    losses = [_number(row[loss_column], loss_column) for row in rows]
    events = [loss >= loss_threshold for loss in losses]
    calibration_indices, evaluation_indices = _split_indices(len(rows), config)
    designer = TriggerPolicyDesigner(
        config["false_negative_cost"],
        config["false_positive_cost"],
        config.get("manipulation_cost_weight", 1.0),
    )
    candidates = [
        Candidate(
            column=str(row["column"]),
            direction=str(row.get("direction", "high")),
            verification_cost_per_trigger=float(row.get("verification_cost_per_trigger", 0.0)),
            manipulation_exposure=float(row.get("manipulation_exposure", 0.0)),
        )
        for row in config["candidates"]
    ]
    if not candidates:
        raise ValueError("At least one candidate is required")
    if len({candidate.column for candidate in candidates}) != len(candidates):
        raise ValueError("Candidate columns must be unique")

    results = []
    for candidate in candidates:
        all_values = [_number(row[candidate.column], candidate.column) for row in rows]
        calibration_values = _slice(all_values, calibration_indices)
        evaluation_values = _slice(all_values, evaluation_indices)
        threshold, calibration_metrics = designer.fit(
            candidate, calibration_values, _slice(events, calibration_indices)
        )
        evaluation_metrics = designer.evaluate(
            candidate, threshold, evaluation_values, _slice(events, evaluation_indices)
        )
        results.append(
            {
                "candidate": asdict(candidate),
                "threshold": threshold,
                "calibration": asdict(calibration_metrics),
                "evaluation": asdict(evaluation_metrics),
            }
        )

    # Selection is made only on the calibration partition. Evaluation is never used to pick a policy.
    selected = min(
        results,
        key=lambda row: (
            row["calibration"]["average_cost_per_row"],
            row["calibration"]["trigger_rate"],
            row["candidate"]["column"],
        ),
    )
    evaluation_events = _slice(events, evaluation_indices)
    baseline_candidate = Candidate("baseline", "high")
    always = _metrics(
        [1.0] * len(evaluation_events),
        evaluation_events,
        0.0,
        baseline_candidate,
        false_negative_cost=designer.false_negative_cost,
        false_positive_cost=designer.false_positive_cost,
        manipulation_cost_weight=0.0,
    )
    never = _metrics(
        [0.0] * len(evaluation_events),
        evaluation_events,
        1.0,
        baseline_candidate,
        false_negative_cost=designer.false_negative_cost,
        false_positive_cost=designer.false_positive_cost,
        manipulation_cost_weight=0.0,
    )
    best_baseline = min(always, never, key=lambda metrics: metrics.average_cost_per_row)
    selected_eval = selected["evaluation"]
    improvement = (
        100.0
        * (best_baseline.average_cost_per_row - selected_eval["average_cost_per_row"])
        / best_baseline.average_cost_per_row
        if best_baseline.average_cost_per_row > 0
        else None
    )
    warnings = []
    calibration_event_count = sum(_slice(events, calibration_indices))
    evaluation_event_count = sum(evaluation_events)
    if calibration_event_count == 0 or calibration_event_count == len(calibration_indices):
        warnings.append("Calibration partition contains only one outcome class.")
    if evaluation_event_count == 0 or evaluation_event_count == len(evaluation_indices):
        warnings.append("Evaluation partition contains only one outcome class; some rates are uninformative.")
    if selected_eval["average_cost_per_row"] > best_baseline.average_cost_per_row:
        warnings.append("Selected trigger is worse than the best always/never policy on evaluation data.")

    return {
        "product": "TRIGGER_POLICY_DESIGNER_V1",
        "source_csv": str(csv_path),
        "rows": len(rows),
        "partition": {
            "method": "chronological",
            "calibration_rows": len(calibration_indices),
            "evaluation_rows": len(evaluation_indices),
        },
        "event_definition": {"loss_column": loss_column, "loss_at_least": loss_threshold},
        "objective": {
            "false_negative_cost": designer.false_negative_cost,
            "false_positive_cost": designer.false_positive_cost,
            "manipulation_cost_weight": designer.manipulation_cost_weight,
        },
        "selected": selected,
        "candidate_results": sorted(
            results,
            key=lambda row: (
                row["calibration"]["average_cost_per_row"],
                row["candidate"]["column"],
            ),
        ),
        "evaluation_baselines": {"always_trigger": asdict(always), "never_trigger": asdict(never)},
        "evaluation_improvement_vs_best_baseline_percent": improvement,
        "warnings": warnings,
        "boundary": "The threshold is calibrated on earlier rows and evaluated on later rows. This does not establish future stability or causal value.",
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:,.3f}"
    return str(value)


def render_markdown(result: Mapping[str, Any], title: str) -> str:
    selected = result["selected"]
    candidate = selected["candidate"]
    evaluation = selected["evaluation"]
    lines = [
        f"# Trigger policy: {title}",
        "",
        f"Selected signal: **{candidate['column']}**  ",
        f"Policy: trigger when value is **{'>=' if candidate['direction'] == 'high' else '<='} {_fmt(selected['threshold'])}**  ",
        f"Evaluation cost per row: **{_fmt(evaluation['average_cost_per_row'])}**  ",
        f"Improvement versus best always/never baseline: **{_fmt(result['evaluation_improvement_vs_best_baseline_percent'])}%**",
        "",
        "## Holdout performance",
        "",
        "| Rows | Events | Triggers | FN rate | FP rate | Precision | Recall |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        f"| {evaluation['rows']} | {evaluation['events']} | {evaluation['triggers']} | "
        f"{_fmt(evaluation['false_negative_rate'])} | {_fmt(evaluation['false_positive_rate'])} | "
        f"{_fmt(evaluation['precision'])} | {_fmt(evaluation['recall'])} |",
        "",
        "## Candidate comparison",
        "",
        "| Signal | Direction | Threshold | Calibration cost/row | Evaluation cost/row |",
        "|---|:---:|---:|---:|---:|",
    ]
    for row in result["candidate_results"]:
        lines.append(
            f"| {row['candidate']['column']} | {row['candidate']['direction']} | "
            f"{_fmt(row['threshold'])} | {_fmt(row['calibration']['average_cost_per_row'])} | "
            f"{_fmt(row['evaluation']['average_cost_per_row'])} |"
        )
    if result["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result["warnings"])
    lines.extend(["", "## Boundary", "", result["boundary"], ""])
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Design and holdout-evaluate a threshold trigger.")
    parser.add_argument("config", type=Path)
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path, default=Path("trigger_policy.json"))
    parser.add_argument("--report", type=Path, default=Path("trigger_policy.md"))
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = design_from_files(config, args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    args.report.write_text(render_markdown(result, str(config.get("name", args.data.stem))), encoding="utf-8")
    print(
        f"Wrote {args.output} and {args.report}; selected={result['selected']['candidate']['column']}, "
        f"evaluation_cost_per_row={result['selected']['evaluation']['average_cost_per_row']:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
