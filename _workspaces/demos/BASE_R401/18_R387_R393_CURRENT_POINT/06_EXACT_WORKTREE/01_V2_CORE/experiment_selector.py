"""Leakage-aware next-experiment selection for LabAllCompass Core V2.

The selector does not infer information gain from prose. Every numeric quantity
used for routing must be declared in the experiment contract before selection.
Unknown quantities stay unknown and cannot silently receive a favorable default.

Primitive:
    UNRESOLVED DECISION
    -> WHICH UNCERTAINTY DIRECTIONS MATTER TO THE DECISION?
    -> WHICH TESTS CAN RESOLVE THEM?
    -> HOW MUCH RESOLUTION IS EXPECTED, AT WHAT RELIABILITY AND COMPUTE?
    -> CHOOSE MAX EXPECTED DECISION PROGRESS PER COMPUTE
    -> FREEZE PLAN
    -> RUN TEST
    -> UPDATE ONLY THE NEXT ROUND

Protected validation is never eligible for adaptive experiment selection.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import hashlib
import json
import math

MODEL_VERSION = "LAB_EXPERIMENT_SELECTOR_R5_V1"
SCHEMA_VERSION = 2


class EvidenceRole(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    DIAGNOSTIC = "DIAGNOSTIC"
    PROTECTED_VALIDATION = "PROTECTED_VALIDATION"


class RouteStatus(str, Enum):
    READY = "READY"
    UNQUANTIFIED = "UNQUANTIFIED"
    INELIGIBLE = "INELIGIBLE"
    OVER_COMPUTE_CEILING = "OVER_COMPUTE_CEILING"


@dataclass(frozen=True)
class UncertaintyAxis:
    axis_id: str
    label: str
    uncertainty: float
    decision_leverage: float
    importance: float = 1.0

    def __post_init__(self) -> None:
        if not self.axis_id.strip():
            raise ValueError("axis_id must be non-empty")
        for name, value in (
            ("uncertainty", self.uncertainty),
            ("decision_leverage", self.decision_leverage),
            ("importance", self.importance),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0,1]")
        if not 0.0 <= self.decision_leverage <= 1.0:
            raise ValueError("decision_leverage must be in [0,1]")
        if self.importance < 0.0:
            raise ValueError("importance must be >= 0")

    @property
    def unresolved_mass(self) -> float:
        return self.uncertainty * self.decision_leverage * self.importance


@dataclass(frozen=True)
class TestChannel:
    test_id: str
    title: str
    expected_resolution_by_axis: Mapping[str, float | None]
    compute_seconds: float | None
    reliability: float | None
    evidence_role: EvidenceRole = EvidenceRole.DEVELOPMENT
    selection_generation: int = 0
    measurement_backreaction: bool | None = False
    backreaction_adjusted: bool = False
    calibration_id: str | None = None
    test_signature: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.test_id.strip():
            raise ValueError("test_id must be non-empty")
        if self.selection_generation < 0:
            raise ValueError("selection_generation must be non-negative")
        if self.compute_seconds is not None:
            if not math.isfinite(self.compute_seconds) or self.compute_seconds <= 0:
                raise ValueError("compute_seconds must be positive when declared")
        if self.reliability is not None:
            if not math.isfinite(self.reliability) or not 0 <= self.reliability <= 1:
                raise ValueError("reliability must be in [0,1] when declared")
        for axis, value in self.expected_resolution_by_axis.items():
            if not str(axis).strip():
                raise ValueError("resolution axis id must be non-empty")
            if value is not None and (not math.isfinite(value) or not 0 <= value <= 1):
                raise ValueError("expected resolution must be in [0,1] or UNKNOWN")


@dataclass(frozen=True)
class ExperimentContract:
    decision_id: str
    search_generation: int
    selection_round: int
    axes: tuple[UncertaintyAxis, ...]
    tests: tuple[TestChannel, ...]
    stop_unresolved_mass: float = 0.0
    compute_ceiling_seconds: float | None = None
    problem_shell: str = "UNSPECIFIED"
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.decision_id.strip():
            raise ValueError("decision_id must be non-empty")
        if self.search_generation < 0 or self.selection_round < 0:
            raise ValueError("generation and round must be non-negative")
        ids = [a.axis_id for a in self.axes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate uncertainty axis")
        tids = [t.test_id for t in self.tests]
        if len(tids) != len(set(tids)):
            raise ValueError("duplicate test_id")
        if self.stop_unresolved_mass < 0 or not math.isfinite(self.stop_unresolved_mass):
            raise ValueError("stop_unresolved_mass must be finite and >=0")
        if self.compute_ceiling_seconds is not None:
            if not math.isfinite(self.compute_ceiling_seconds) or self.compute_ceiling_seconds <= 0:
                raise ValueError("compute ceiling must be positive")

    @property
    def unresolved_mass(self) -> float:
        return sum(axis.unresolved_mass for axis in self.axes)

    def fingerprint(self) -> str:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "model_version": MODEL_VERSION,
            "decision_id": self.decision_id,
            "search_generation": self.search_generation,
            "selection_round": self.selection_round,
            "problem_shell": self.problem_shell,
            "stop_unresolved_mass": self.stop_unresolved_mass,
            "compute_ceiling_seconds": self.compute_ceiling_seconds,
            "provenance": list(self.provenance),
            "axes": [
                {
                    "axis_id": a.axis_id,
                    "label": a.label,
                    "uncertainty": a.uncertainty,
                    "decision_leverage": a.decision_leverage,
                    "importance": a.importance,
                }
                for a in self.axes
            ],
            "tests": [
                {
                    "test_id": t.test_id,
                    "title": t.title,
                    "expected_resolution_by_axis": dict(sorted(t.expected_resolution_by_axis.items())),
                    "compute_seconds": t.compute_seconds,
                    "reliability": t.reliability,
                    "evidence_role": t.evidence_role.value,
                    "selection_generation": t.selection_generation,
                    "measurement_backreaction": t.measurement_backreaction,
                    "backreaction_adjusted": t.backreaction_adjusted,
                    "calibration_id": t.calibration_id,
                    "test_signature": t.test_signature,
                    "notes": t.notes,
                }
                for t in self.tests
            ],
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TestRoute:
    test_id: str
    status: RouteStatus
    expected_decision_progress: float | None
    expected_progress_per_compute: float | None
    compute_seconds: float | None
    reliability: float | None
    covered_axes: tuple[str, ...]
    unknown_fields: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ExperimentPlan:
    decision_id: str
    search_generation: int
    selection_round: int
    contract_fingerprint: str
    unresolved_mass: float
    stop: bool
    stop_reason: str
    selected_test_id: str | None
    ranked_routes: tuple[TestRoute, ...]
    blind_axes: tuple[str, ...]
    unquantified_test_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "model_version": MODEL_VERSION,
            "decision_id": self.decision_id,
            "search_generation": self.search_generation,
            "selection_round": self.selection_round,
            "contract_fingerprint": self.contract_fingerprint,
            "unresolved_mass": self.unresolved_mass,
            "stop": self.stop,
            "stop_reason": self.stop_reason,
            "selected_test_id": self.selected_test_id,
            "blind_axes": list(self.blind_axes),
            "unquantified_test_ids": list(self.unquantified_test_ids),
            "ranked_routes": [
                {
                    "test_id": r.test_id,
                    "status": r.status.value,
                    "expected_decision_progress": r.expected_decision_progress,
                    "expected_progress_per_compute": r.expected_progress_per_compute,
                    "compute_seconds": r.compute_seconds,
                    "reliability": r.reliability,
                    "covered_axes": list(r.covered_axes),
                    "unknown_fields": list(r.unknown_fields),
                    "reason": r.reason,
                }
                for r in self.ranked_routes
            ],
        }

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class ExperimentOutcome:
    event_id: str
    decision_id: str
    test_id: str
    search_generation: int
    selected_round: int
    release_round: int
    realized_uncertainty_by_axis: Mapping[str, float]
    role: EvidenceRole = EvidenceRole.DEVELOPMENT
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.release_round <= self.selected_round:
            raise ValueError("outcome must be released after the round that selected it")
        if self.search_generation < 0:
            raise ValueError("search_generation must be non-negative")
        for axis, value in self.realized_uncertainty_by_axis.items():
            if not 0 <= value <= 1 or not math.isfinite(value):
                raise ValueError(f"realized uncertainty for {axis} must be in [0,1]")


def _route_test(contract: ExperimentContract, test: TestChannel, by_axis: Mapping[str, UncertaintyAxis]) -> TestRoute:
    if test.evidence_role == EvidenceRole.PROTECTED_VALIDATION:
        return TestRoute(
            test.test_id, RouteStatus.INELIGIBLE, None, None, test.compute_seconds, test.reliability, (),
            reason="PROTECTED_VALIDATION_NEVER_DRIVES_ADAPTIVE_SELECTION",
        )
    if test.selection_generation != contract.search_generation:
        return TestRoute(
            test.test_id, RouteStatus.INELIGIBLE, None, None, test.compute_seconds, test.reliability, (),
            reason="TEST_GENERATION_MISMATCH",
        )
    if contract.compute_ceiling_seconds is not None and test.compute_seconds is not None and test.compute_seconds > contract.compute_ceiling_seconds:
        return TestRoute(
            test.test_id, RouteStatus.OVER_COMPUTE_CEILING, None, None, test.compute_seconds, test.reliability, (),
            reason="TEST_EXCEEDS_DECLARED_COMPUTE_CEILING",
        )

    covered = tuple(sorted(axis for axis, value in test.expected_resolution_by_axis.items() if axis in by_axis and value not in (None, 0.0)))
    unknown = []
    if test.compute_seconds is None:
        unknown.append("compute_seconds")
    if test.reliability is None:
        unknown.append("reliability")
    for axis, value in test.expected_resolution_by_axis.items():
        if axis in by_axis and value is None:
            unknown.append(f"expected_resolution:{axis}")
    if test.measurement_backreaction is None:
        unknown.append("measurement_backreaction")
    if not test.calibration_id:
        unknown.append("calibration_id")
    if test.measurement_backreaction is True and not test.backreaction_adjusted:
        unknown.append("backreaction_adjustment")

    if unknown:
        return TestRoute(
            test.test_id, RouteStatus.UNQUANTIFIED, None, None, test.compute_seconds, test.reliability, covered,
            tuple(sorted(set(unknown))), "NUMERIC_ROUTING_REQUIRES_DECLARED_CALIBRATION",
        )

    # Unknown axis IDs are ignored for score but remain contract-visible. The selector
    # never invents an uncertainty axis merely because a test names one.
    progress = 0.0
    for axis_id, reduction in test.expected_resolution_by_axis.items():
        if axis_id not in by_axis or reduction is None:
            continue
        axis = by_axis[axis_id]
        progress += axis.unresolved_mass * float(reduction) * float(test.reliability)
    efficiency = progress / float(test.compute_seconds)
    return TestRoute(
        test.test_id, RouteStatus.READY, progress, efficiency, test.compute_seconds, test.reliability, covered,
        reason="DECLARED_EXPECTED_DECISION_PROGRESS_PER_COMPUTE",
    )


def choose_next_experiment(contract: ExperimentContract) -> ExperimentPlan:
    by_axis = {a.axis_id: a for a in contract.axes}
    routes = tuple(_route_test(contract, t, by_axis) for t in contract.tests)

    eligible_coverage: set[str] = set()
    for route in routes:
        if route.status in (RouteStatus.READY, RouteStatus.UNQUANTIFIED):
            eligible_coverage.update(route.covered_axes)
    blind = tuple(sorted(a.axis_id for a in contract.axes if a.unresolved_mass > 0 and a.axis_id not in eligible_coverage))
    unquantified = tuple(sorted(r.test_id for r in routes if r.status == RouteStatus.UNQUANTIFIED))

    ranked = tuple(sorted(
        routes,
        key=lambda r: (
            r.status != RouteStatus.READY,
            -(r.expected_progress_per_compute if r.expected_progress_per_compute is not None else -math.inf),
            -(r.expected_decision_progress if r.expected_decision_progress is not None else -math.inf),
            r.compute_seconds if r.compute_seconds is not None else math.inf,
            r.test_id,
        ),
    ))

    if contract.unresolved_mass <= contract.stop_unresolved_mass:
        return ExperimentPlan(
            contract.decision_id, contract.search_generation, contract.selection_round, contract.fingerprint(),
            contract.unresolved_mass, True, "DECISION_UNCERTAINTY_BELOW_DECLARED_STOP_THRESHOLD", None,
            ranked, blind, unquantified,
        )

    ready = [r for r in ranked if r.status == RouteStatus.READY and (r.expected_decision_progress or 0.0) > 0.0]
    if not ready:
        reason = "NO_QUANTIFIED_TEST_CAN_REDUCE_DECLARED_DECISION_UNCERTAINTY"
        if unquantified:
            reason = "ROUTING_BLOCKED_BY_UNQUANTIFIED_TEST_CONTRACTS"
        return ExperimentPlan(
            contract.decision_id, contract.search_generation, contract.selection_round, contract.fingerprint(),
            contract.unresolved_mass, True, reason, None, ranked, blind, unquantified,
        )

    return ExperimentPlan(
        contract.decision_id, contract.search_generation, contract.selection_round, contract.fingerprint(),
        contract.unresolved_mass, False, "", ready[0].test_id, ranked, blind, unquantified,
    )


def apply_outcome(contract: ExperimentContract, plan: ExperimentPlan, outcome: ExperimentOutcome) -> ExperimentContract:
    """Produce the next-round contract; never mutate the frozen selection round."""
    if plan.contract_fingerprint != contract.fingerprint():
        raise ValueError("plan/contract fingerprint mismatch")
    if plan.selected_test_id != outcome.test_id:
        raise ValueError("outcome test was not the frozen selected test")
    if outcome.decision_id != contract.decision_id:
        raise ValueError("outcome decision mismatch")
    if outcome.search_generation != contract.search_generation:
        raise ValueError("outcome search-generation mismatch")
    if outcome.selected_round != contract.selection_round:
        raise ValueError("outcome selected-round mismatch")
    if outcome.release_round <= contract.selection_round:
        raise ValueError("outcome was not released after selection")
    if outcome.role == EvidenceRole.PROTECTED_VALIDATION:
        raise ValueError("protected validation cannot adapt the experiment program")

    by_axis = {a.axis_id: a for a in contract.axes}
    new_axes = []
    for axis in contract.axes:
        if axis.axis_id in outcome.realized_uncertainty_by_axis:
            new_axes.append(replace(axis, uncertainty=float(outcome.realized_uncertainty_by_axis[axis.axis_id])))
        else:
            new_axes.append(axis)
    unknown = set(outcome.realized_uncertainty_by_axis) - set(by_axis)
    if unknown:
        raise ValueError(f"outcome contains unknown axes: {sorted(unknown)}")

    # The already-run channel is removed. Future channels stay frozen except for the
    # round number; calibration changes require an explicitly new contract.
    remaining = tuple(t for t in contract.tests if t.test_id != outcome.test_id)
    return replace(contract, selection_round=outcome.release_round, axes=tuple(new_axes), tests=remaining)


def contract_from_dict(obj: Mapping[str, object]) -> ExperimentContract:
    axes = tuple(UncertaintyAxis(
        axis_id=str(a["axis_id"]),
        label=str(a.get("label", a["axis_id"])),
        uncertainty=float(a["uncertainty"]),
        decision_leverage=float(a["decision_leverage"]),
        importance=float(a.get("importance", 1.0)),
    ) for a in obj.get("axes", ()) if isinstance(a, Mapping))
    tests = tuple(TestChannel(
        test_id=str(t["test_id"]),
        title=str(t.get("title", t["test_id"])),
        expected_resolution_by_axis={str(k): (None if v is None else float(v)) for k, v in dict(t.get("expected_resolution_by_axis", {})).items()},
        compute_seconds=None if t.get("compute_seconds") is None else float(t["compute_seconds"]),
        reliability=None if t.get("reliability") is None else float(t["reliability"]),
        evidence_role=EvidenceRole(str(t.get("evidence_role", EvidenceRole.DEVELOPMENT.value))),
        selection_generation=int(t.get("selection_generation", obj.get("search_generation", 0))),
        measurement_backreaction=t.get("measurement_backreaction", False),
        backreaction_adjusted=bool(t.get("backreaction_adjusted", False)),
        calibration_id=None if t.get("calibration_id") in (None,"") else str(t.get("calibration_id")),
        test_signature=None if t.get("test_signature") in (None,"") else str(t.get("test_signature")),
        notes=str(t.get("notes", "")),
    ) for t in obj.get("tests", ()) if isinstance(t, Mapping))
    return ExperimentContract(
        decision_id=str(obj["decision_id"]),
        search_generation=int(obj.get("search_generation", 0)),
        selection_round=int(obj.get("selection_round", 0)),
        axes=axes,
        tests=tests,
        stop_unresolved_mass=float(obj.get("stop_unresolved_mass", 0.0)),
        compute_ceiling_seconds=None if obj.get("compute_ceiling_seconds") is None else float(obj["compute_ceiling_seconds"]),
        problem_shell=str(obj.get("problem_shell", "UNSPECIFIED")),
        provenance=tuple(str(x) for x in obj.get("provenance", ())),
    )


def load_contract(path: str | Path) -> ExperimentContract:
    return contract_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
