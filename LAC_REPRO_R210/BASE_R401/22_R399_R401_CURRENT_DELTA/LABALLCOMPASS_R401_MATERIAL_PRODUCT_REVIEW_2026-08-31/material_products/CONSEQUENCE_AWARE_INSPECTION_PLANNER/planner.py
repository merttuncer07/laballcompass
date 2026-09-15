"""Consequence-Aware Inspection Planner.

A dependency-free, user-facing productization of the Lab's
IM406_IM037_ACRA consequence-resolution allocation mechanism.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


EPSILON = 1e-10


@dataclass(frozen=True)
class InspectionTarget:
    name: str
    urgency_weight: float
    diagnostic_weight: float
    consequence: float
    cost_multiplier: float = 1.0
    delay_scale: float = 1.0
    diagnostic_scale: float = 1.0
    allowed_modes: tuple[str, ...] = ()


@dataclass(frozen=True)
class InspectionMode:
    name: str
    cost: float
    delay_error: float
    diagnostic_error: float


@dataclass(frozen=True)
class Choice:
    target: str
    mode: str
    cost: float
    decision_loss: float


@dataclass(frozen=True)
class State:
    cost: float
    loss: float
    choices: tuple[Choice, ...]


def _finite_nonnegative(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return number


def _finite_positive(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return number


def _unique_names(items: Iterable[Any], label: str) -> None:
    names = [item.name for item in items]
    if len(names) != len(set(names)):
        raise ValueError(f"{label} names must be unique")


class InspectionPlanner:
    """Select one inspection mode per target under a shared budget.

    The optimizer keeps an exact Pareto frontier of non-dominated partial
    allocations. This is a multiple-choice knapsack solver and requires no
    third-party optimization package.
    """

    def __init__(
        self,
        targets: Sequence[InspectionTarget],
        modes: Sequence[InspectionMode],
    ) -> None:
        if not targets or not modes:
            raise ValueError("At least one target and one inspection mode are required")
        self.targets = tuple(targets)
        self.modes = tuple(modes)
        _unique_names(self.targets, "Target")
        _unique_names(self.modes, "Mode")
        self.mode_by_name = {mode.name: mode for mode in self.modes}
        for target in self.targets:
            for field in (
                "urgency_weight",
                "diagnostic_weight",
                "consequence",
            ):
                _finite_nonnegative(getattr(target, field), f"{target.name}.{field}")
            for field in ("cost_multiplier", "delay_scale", "diagnostic_scale"):
                _finite_positive(getattr(target, field), f"{target.name}.{field}")
            unknown = set(target.allowed_modes) - set(self.mode_by_name)
            if unknown:
                raise ValueError(
                    f"{target.name}.allowed_modes contains unknown modes: {sorted(unknown)}"
                )
        for mode in self.modes:
            for field in ("cost", "delay_error", "diagnostic_error"):
                _finite_nonnegative(getattr(mode, field), f"{mode.name}.{field}")

    @staticmethod
    def decision_loss(target: InspectionTarget, mode: InspectionMode) -> float:
        delay_error = mode.delay_error * target.delay_scale
        diagnostic_error = mode.diagnostic_error * target.diagnostic_scale
        return target.consequence * (
            target.urgency_weight * delay_error**2
            + target.diagnostic_weight * diagnostic_error**2
        )

    @staticmethod
    def choice_cost(target: InspectionTarget, mode: InspectionMode) -> float:
        return target.cost_multiplier * mode.cost

    def _allowed(self, target: InspectionTarget) -> tuple[InspectionMode, ...]:
        if not target.allowed_modes:
            return self.modes
        allowed = set(target.allowed_modes)
        return tuple(mode for mode in self.modes if mode.name in allowed)

    @staticmethod
    def _prune(states: list[State]) -> list[State]:
        """Remove states dominated by another state with <= cost and <= loss."""
        states.sort(key=lambda state: (state.cost, state.loss, tuple(c.mode for c in state.choices)))
        frontier: list[State] = []
        best_loss = math.inf
        for state in states:
            if state.loss < best_loss - EPSILON:
                frontier.append(state)
                best_loss = state.loss
        return frontier

    def frontier(self) -> list[State]:
        states = [State(0.0, 0.0, ())]
        for target in self.targets:
            expanded: list[State] = []
            for state in states:
                for mode in self._allowed(target):
                    cost = self.choice_cost(target, mode)
                    loss = self.decision_loss(target, mode)
                    expanded.append(
                        State(
                            state.cost + cost,
                            state.loss + loss,
                            state.choices + (Choice(target.name, mode.name, cost, loss),),
                        )
                    )
            states = self._prune(expanded)
        return states

    @staticmethod
    def _best_within(frontier: Sequence[State], budget: float) -> State:
        feasible = [state for state in frontier if state.cost <= budget + EPSILON]
        if not feasible:
            minimum = min(state.cost for state in frontier)
            raise ValueError(
                f"Budget {budget:g} is infeasible; minimum required budget is {minimum:g}"
            )
        return min(feasible, key=lambda state: (state.loss, state.cost))

    def fixed_mode(self, mode_name: str) -> State | None:
        mode = self.mode_by_name.get(mode_name)
        if mode is None:
            raise KeyError(f"Unknown mode: {mode_name}")
        if any(target.allowed_modes and mode_name not in target.allowed_modes for target in self.targets):
            return None
        choices = tuple(
            Choice(
                target.name,
                mode.name,
                self.choice_cost(target, mode),
                self.decision_loss(target, mode),
            )
            for target in self.targets
        )
        return State(
            sum(choice.cost for choice in choices),
            sum(choice.decision_loss for choice in choices),
            choices,
        )

    def best_uniform(self, budget: float) -> State | None:
        candidates = [self.fixed_mode(mode.name) for mode in self.modes]
        feasible = [
            state
            for state in candidates
            if state is not None and state.cost <= budget + EPSILON
        ]
        return min(feasible, key=lambda state: (state.loss, state.cost)) if feasible else None

    @staticmethod
    def _state_payload(state: State, total_loss: float | None = None) -> dict[str, Any]:
        denominator = state.loss if total_loss is None else total_loss
        selections = []
        for choice in state.choices:
            row = asdict(choice)
            row["loss_share"] = (
                choice.decision_loss / denominator if denominator and denominator > EPSILON else 0.0
            )
            selections.append(row)
        return {"total_cost": state.cost, "total_decision_loss": state.loss, "selections": selections}

    @staticmethod
    def _improvement(reference_loss: float, candidate_loss: float) -> float | None:
        if reference_loss <= EPSILON:
            return None
        return 100.0 * (reference_loss - candidate_loss) / reference_loss

    def plan(
        self,
        budget: float,
        *,
        baseline_mode: str | None = None,
        budget_scenarios: Sequence[float] = (),
    ) -> dict[str, Any]:
        budget = _finite_nonnegative(budget, "budget")
        frontier = self.frontier()
        chosen = self._best_within(frontier, budget)
        cheapest = min(frontier, key=lambda state: (state.cost, state.loss))
        uniform = self.best_uniform(budget)
        configured = self.fixed_mode(baseline_mode) if baseline_mode else None

        next_better = next(
            (
                state
                for state in frontier
                if state.cost > budget + EPSILON and state.loss < chosen.loss - EPSILON
            ),
            None,
        )
        curve = []
        for scenario_budget in sorted(set(float(value) for value in budget_scenarios)):
            scenario_budget = _finite_nonnegative(scenario_budget, "budget_scenarios item")
            try:
                state = self._best_within(frontier, scenario_budget)
                curve.append(
                    {
                        "budget": scenario_budget,
                        "feasible": True,
                        "total_cost": state.cost,
                        "total_decision_loss": state.loss,
                        "mode_by_target": {choice.target: choice.mode for choice in state.choices},
                    }
                )
            except ValueError:
                curve.append({"budget": scenario_budget, "feasible": False})

        comparison: dict[str, Any] = {
            "minimum_cost_plan": self._state_payload(cheapest),
            "loss_reduction_vs_minimum_cost_percent": self._improvement(cheapest.loss, chosen.loss),
            "best_affordable_uniform_plan": None,
            "loss_reduction_vs_uniform_percent": None,
            "configured_baseline_plan": None,
            "loss_reduction_vs_configured_percent": None,
        }
        if uniform is not None:
            comparison["best_affordable_uniform_plan"] = self._state_payload(uniform)
            comparison["loss_reduction_vs_uniform_percent"] = self._improvement(uniform.loss, chosen.loss)
        if configured is not None:
            comparison["configured_baseline_plan"] = self._state_payload(configured)
            if configured.cost <= budget + EPSILON:
                comparison["loss_reduction_vs_configured_percent"] = self._improvement(
                    configured.loss, chosen.loss
                )

        return {
            "product": "CONSEQUENCE_AWARE_INSPECTION_PLANNER_V1",
            "budget": budget,
            "plan": self._state_payload(chosen),
            "comparison": comparison,
            "next_better_plan": (
                None
                if next_better is None
                else {
                    "required_budget": next_better.cost,
                    "additional_budget": next_better.cost - budget,
                    "total_decision_loss": next_better.loss,
                    "additional_loss_reduction_percent": self._improvement(
                        chosen.loss, next_better.loss
                    ),
                    "mode_by_target": {choice.target: choice.mode for choice in next_better.choices},
                }
            ),
            "budget_curve": curve,
            "optimizer": {
                "method": "exact_non_dominated_multiple_choice_frontier",
                "frontier_points": len(frontier),
                "targets": len(self.targets),
                "modes": len(self.modes),
            },
        }


def _parse_target(row: Mapping[str, Any]) -> InspectionTarget:
    return InspectionTarget(
        name=str(row["name"]),
        urgency_weight=float(row["urgency_weight"]),
        diagnostic_weight=float(row["diagnostic_weight"]),
        consequence=float(row["consequence"]),
        cost_multiplier=float(row.get("cost_multiplier", 1.0)),
        delay_scale=float(row.get("delay_scale", 1.0)),
        diagnostic_scale=float(row.get("diagnostic_scale", 1.0)),
        allowed_modes=tuple(str(value) for value in row.get("allowed_modes", ())),
    )


def _parse_mode(row: Mapping[str, Any]) -> InspectionMode:
    return InspectionMode(
        name=str(row["name"]),
        cost=float(row["cost"]),
        delay_error=float(row["delay_error"]),
        diagnostic_error=float(row["diagnostic_error"]),
    )


def _stressed_targets(
    targets: Sequence[InspectionTarget], multipliers: Mapping[str, Any]
) -> tuple[InspectionTarget, ...]:
    unknown = set(multipliers) - {target.name for target in targets}
    if unknown:
        raise ValueError(f"Stress case contains unknown targets: {sorted(unknown)}")
    return tuple(
        replace(
            target,
            consequence=target.consequence
            * _finite_nonnegative(multipliers.get(target.name, 1.0), "stress multiplier"),
        )
        for target in targets
    )


def plan_from_config(config: Mapping[str, Any]) -> dict[str, Any]:
    targets = tuple(_parse_target(row) for row in config["targets"])
    modes = tuple(_parse_mode(row) for row in config["modes"])
    budget = float(config["budget"])
    planner = InspectionPlanner(targets, modes)
    result = planner.plan(
        budget,
        baseline_mode=config.get("baseline_mode"),
        budget_scenarios=config.get("budget_scenarios", ()),
    )
    base_modes = {
        row["target"]: row["mode"] for row in result["plan"]["selections"]
    }
    stress_results = []
    for stress in config.get("stress_cases", ()):
        stressed = _stressed_targets(targets, stress.get("consequence_multipliers", {}))
        stressed_result = InspectionPlanner(stressed, modes).plan(budget)
        stressed_modes = {
            row["target"]: row["mode"] for row in stressed_result["plan"]["selections"]
        }
        changes = [
            {"target": name, "base_mode": base_modes[name], "stress_mode": stressed_modes[name]}
            for name in base_modes
            if base_modes[name] != stressed_modes[name]
        ]
        stress_results.append(
            {
                "name": str(stress["name"]),
                "consequence_multipliers": stress.get("consequence_multipliers", {}),
                "total_cost": stressed_result["plan"]["total_cost"],
                "total_decision_loss": stressed_result["plan"]["total_decision_loss"],
                "mode_changes": changes,
                "stable": not changes,
            }
        )
    result["stress_cases"] = stress_results
    result["interpretation"] = {
        "loss": "Relative consequence-weighted error; compare plans, do not read as currency.",
        "scope": "Inputs are declared estimates. The tool allocates them exactly but does not validate their empirical accuracy.",
    }
    return result


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:,.3f}"
    return str(value)


def render_markdown(result: Mapping[str, Any], scenario_name: str) -> str:
    plan = result["plan"]
    comparison = result["comparison"]
    lines = [
        f"# Inspection plan: {scenario_name}",
        "",
        f"Budget: **{_fmt(result['budget'])}**  ",
        f"Allocated cost: **{_fmt(plan['total_cost'])}**  ",
        f"Decision-weighted loss: **{_fmt(plan['total_decision_loss'])}**",
        "",
        "## Selected inspection modes",
        "",
        "| Target | Mode | Cost | Decision loss | Loss share |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in plan["selections"]:
        lines.append(
            f"| {row['target']} | {row['mode']} | {_fmt(row['cost'])} | "
            f"{_fmt(row['decision_loss'])} | {100 * row['loss_share']:.1f}% |"
        )
    lines.extend(
        [
            "",
            "## What the allocation buys",
            "",
            f"- Loss reduction versus the minimum-cost plan: "
            f"**{_fmt(comparison['loss_reduction_vs_minimum_cost_percent'])}%**.",
            f"- Loss reduction versus the best affordable one-mode-for-everything policy: "
            f"**{_fmt(comparison['loss_reduction_vs_uniform_percent'])}%**.",
        ]
    )
    next_plan = result["next_better_plan"]
    if next_plan:
        lines.append(
            f"- The next strictly better plan needs **{_fmt(next_plan['additional_budget'])}** "
            f"more budget and reduces current loss by **{_fmt(next_plan['additional_loss_reduction_percent'])}%**."
        )
    else:
        lines.append("- No strictly better allocation exists within the declared modes.")
    if result["budget_curve"]:
        lines.extend(
            [
                "",
                "## Budget curve",
                "",
                "| Budget | Feasible | Used | Decision loss |",
                "|---:|:---:|---:|---:|",
            ]
        )
        for row in result["budget_curve"]:
            lines.append(
                f"| {_fmt(row['budget'])} | {'yes' if row['feasible'] else 'no'} | "
                f"{_fmt(row.get('total_cost'))} | {_fmt(row.get('total_decision_loss'))} |"
            )
    if result["stress_cases"]:
        lines.extend(
            [
                "",
                "## Declared consequence stresses",
                "",
                "| Stress | Allocation stable | Changed targets | Loss |",
                "|---|:---:|---:|---:|",
            ]
        )
        for row in result["stress_cases"]:
            lines.append(
                f"| {row['name']} | {'yes' if row['stable'] else 'no'} | "
                f"{len(row['mode_changes'])} | {_fmt(row['total_decision_loss'])} |"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This plan is only as good as the supplied costs, errors and consequence weights. "
            "Validate those estimates with field data before operational deployment.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Allocate an inspection budget by consequence-weighted decision loss."
    )
    parser.add_argument("input", type=Path, help="Scenario JSON file")
    parser.add_argument("--output", type=Path, default=Path("inspection_plan.json"))
    parser.add_argument("--report", type=Path, default=Path("inspection_plan.md"))
    args = parser.parse_args(argv)

    config = json.loads(args.input.read_text(encoding="utf-8"))
    result = plan_from_config(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    args.report.write_text(
        render_markdown(result, str(config.get("name", args.input.stem))), encoding="utf-8"
    )
    print(
        f"Wrote {args.output} and {args.report}; cost={result['plan']['total_cost']:.3f}, "
        f"loss={result['plan']['total_decision_loss']:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
