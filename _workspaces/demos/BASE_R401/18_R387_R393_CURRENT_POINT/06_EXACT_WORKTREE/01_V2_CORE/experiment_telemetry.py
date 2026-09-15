"""Conservative experiment telemetry capture and calibration for LabAllCompass.

Purpose
-------
Turn realized Lab experiment runs into future-generation routing telemetry without
leaking the run back into the generation that selected it.

Primitive:
    RUN DECLARED TEST
    -> RECORD BEFORE/AFTER UNCERTAINTY + COMPUTE + PROVENANCE
    -> HOLD UNTIL A LATER SEARCH GENERATION
    -> CALIBRATE TEST/SHELL BEHAVIOR CONSERVATIVELY
    -> FILL ONLY PREVIOUSLY-UNKNOWN ROUTING FIELDS
    -> ROUTE FUTURE TESTS

Calibration policy
------------------
* exact problem-shell + exact test-signature match only;
* protected validation is permanently excluded;
* same/future-generation events are excluded;
* calibration_eligible must be explicitly true;
* unadjusted measurement backreaction is unusable and penalizes reliability;
* reliability uses a Wilson lower confidence bound;
* expected axis resolution uses a one-sided lower confidence bound on observed
  fractional uncertainty reduction;
* compute uses the maximum observed positive wall time;
* insufficient support remains UNKNOWN.

This module calibrates the experiment *channel*, not the scientific candidate.
It never changes evidence tiers or promotion state.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import hashlib
import json
import math
import statistics

from experiment_selector import (
    EvidenceRole,
    ExperimentContract,
    ExperimentOutcome,
    ExperimentPlan,
)

MODEL_VERSION = "LAB_EXPERIMENT_TELEMETRY_R5_V1"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ExperimentRunRecord:
    event_id: str
    decision_id: str
    test_id: str
    test_signature: str
    problem_shell: str
    shell_tags: tuple[str, ...]
    search_generation: int
    selection_round: int
    release_generation: int
    release_round: int
    contract_fingerprint: str
    evidence_role: EvidenceRole
    calibration_eligible: bool
    measurement_backreaction: bool | None
    backreaction_adjusted: bool
    before_uncertainty_by_axis: Mapping[str, float]
    after_uncertainty_by_axis: Mapping[str, float]
    compute_seconds: float | None
    run_status: str = "COMPLETE"
    measurement_valid: bool = True
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must be non-empty")
        if not self.test_signature.strip():
            raise ValueError("test_signature must be non-empty")
        if not self.problem_shell.strip():
            raise ValueError("problem_shell must be non-empty")
        if self.search_generation < 0 or self.release_generation < self.search_generation:
            raise ValueError("release_generation must be >= search_generation >= 0")
        if self.selection_round < 0 or self.release_round <= self.selection_round:
            raise ValueError("release_round must be after selection_round")
        if self.compute_seconds is not None and (not math.isfinite(self.compute_seconds) or self.compute_seconds <= 0):
            raise ValueError("compute_seconds must be positive when known")
        if self.run_status not in {"COMPLETE", "FAILED", "CENSORED"}:
            raise ValueError("run_status must be COMPLETE, FAILED, or CENSORED")
        for label, values in (("before", self.before_uncertainty_by_axis), ("after", self.after_uncertainty_by_axis)):
            for axis, value in values.items():
                if not str(axis).strip() or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError(f"{label} uncertainty must be finite in [0,1]")

    @property
    def usable_measurement(self) -> bool:
        if self.run_status != "COMPLETE" or not self.measurement_valid:
            return False
        if self.measurement_backreaction is None:
            return False
        if self.measurement_backreaction and not self.backreaction_adjusted:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "model_version": MODEL_VERSION,
            "event_id": self.event_id,
            "decision_id": self.decision_id,
            "test_id": self.test_id,
            "test_signature": self.test_signature,
            "problem_shell": self.problem_shell,
            "shell_tags": list(self.shell_tags),
            "search_generation": self.search_generation,
            "selection_round": self.selection_round,
            "release_generation": self.release_generation,
            "release_round": self.release_round,
            "contract_fingerprint": self.contract_fingerprint,
            "evidence_role": self.evidence_role.value,
            "calibration_eligible": self.calibration_eligible,
            "measurement_backreaction": self.measurement_backreaction,
            "backreaction_adjusted": self.backreaction_adjusted,
            "before_uncertainty_by_axis": dict(self.before_uncertainty_by_axis),
            "after_uncertainty_by_axis": dict(self.after_uncertainty_by_axis),
            "compute_seconds": self.compute_seconds,
            "run_status": self.run_status,
            "measurement_valid": self.measurement_valid,
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_dict(cls, obj: Mapping[str, object]) -> "ExperimentRunRecord":
        return cls(
            event_id=str(obj["event_id"]),
            decision_id=str(obj["decision_id"]),
            test_id=str(obj["test_id"]),
            test_signature=str(obj["test_signature"]),
            problem_shell=str(obj["problem_shell"]),
            shell_tags=tuple(str(x) for x in obj.get("shell_tags", ())),
            search_generation=int(obj["search_generation"]),
            selection_round=int(obj["selection_round"]),
            release_generation=int(obj.get("release_generation", obj["search_generation"])),
            release_round=int(obj["release_round"]),
            contract_fingerprint=str(obj["contract_fingerprint"]),
            evidence_role=EvidenceRole(str(obj.get("evidence_role", EvidenceRole.DEVELOPMENT.value))),
            calibration_eligible=bool(obj.get("calibration_eligible", False)),
            measurement_backreaction=obj.get("measurement_backreaction"),
            backreaction_adjusted=bool(obj.get("backreaction_adjusted", False)),
            before_uncertainty_by_axis={str(k): float(v) for k, v in dict(obj.get("before_uncertainty_by_axis", {})).items()},
            after_uncertainty_by_axis={str(k): float(v) for k, v in dict(obj.get("after_uncertainty_by_axis", {})).items()},
            compute_seconds=None if obj.get("compute_seconds") is None else float(obj["compute_seconds"]),
            run_status=str(obj.get("run_status", "COMPLETE")),
            measurement_valid=bool(obj.get("measurement_valid", True)),
            provenance=tuple(str(x) for x in obj.get("provenance", ())),
        )


class ExperimentTelemetryLedger:
    def __init__(self, events: Iterable[ExperimentRunRecord] = ()): self.events = list(events)

    def append(self, event: ExperimentRunRecord) -> None:
        if any(e.event_id == event.event_id for e in self.events):
            raise ValueError(f"duplicate event_id: {event.event_id}")
        self.events.append(event)

    @classmethod
    def load_jsonl(cls, path: str | Path) -> "ExperimentTelemetryLedger":
        p = Path(path)
        if not p.exists(): return cls()
        events=[]
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip(): events.append(ExperimentRunRecord.from_dict(json.loads(line)))
        return cls(events)

    def append_jsonl(self, path: str | Path, event: ExperimentRunRecord) -> None:
        p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        current=self.load_jsonl(p)
        if any(e.event_id == event.event_id for e in current.events):
            raise ValueError(f"duplicate event_id: {event.event_id}")
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), sort_keys=True, ensure_ascii=False)+"\n")
        self.events=current.events+[event]


@dataclass(frozen=True)
class TestCalibration:
    test_id: str
    test_signature: str
    problem_shell: str
    target_generation: int
    attempt_count: int
    usable_count: int
    reliability_lower_bound: float | None
    compute_upper_seconds: float | None
    expected_resolution_lower_by_axis: Mapping[str, float | None]
    axis_observation_counts: Mapping[str, int]
    excluded_counts: Mapping[str, int]
    event_ids: tuple[str, ...]
    calibration_id: str

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "test_signature": self.test_signature,
            "problem_shell": self.problem_shell,
            "target_generation": self.target_generation,
            "attempt_count": self.attempt_count,
            "usable_count": self.usable_count,
            "reliability_lower_bound": self.reliability_lower_bound,
            "compute_upper_seconds": self.compute_upper_seconds,
            "expected_resolution_lower_by_axis": dict(self.expected_resolution_lower_by_axis),
            "axis_observation_counts": dict(self.axis_observation_counts),
            "excluded_counts": dict(self.excluded_counts),
            "event_ids": list(self.event_ids),
            "calibration_id": self.calibration_id,
        }


@dataclass(frozen=True)
class ExperimentCalibrationSnapshot:
    target_generation: int
    problem_shell: str
    min_attempts: int
    min_axis_observations: int
    one_sided_z: float
    calibrations: tuple[TestCalibration, ...]
    excluded_global_counts: Mapping[str, int]
    fingerprint: str

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "model_version": MODEL_VERSION,
            "target_generation": self.target_generation,
            "problem_shell": self.problem_shell,
            "min_attempts": self.min_attempts,
            "min_axis_observations": self.min_axis_observations,
            "one_sided_z": self.one_sided_z,
            "calibrations": [c.to_dict() for c in self.calibrations],
            "excluded_global_counts": dict(self.excluded_global_counts),
            "fingerprint": self.fingerprint,
        }

    def save(self, path: str | Path) -> None:
        p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True)+"\n", encoding="utf-8")

    @classmethod
    def from_dict(cls, obj: Mapping[str, object]) -> "ExperimentCalibrationSnapshot":
        calibrations=[]
        for c in obj.get("calibrations", ()):
            if not isinstance(c, Mapping): continue
            calibrations.append(TestCalibration(
                test_id=str(c["test_id"]), test_signature=str(c["test_signature"]), problem_shell=str(c["problem_shell"]),
                target_generation=int(c["target_generation"]), attempt_count=int(c["attempt_count"]), usable_count=int(c["usable_count"]),
                reliability_lower_bound=None if c.get("reliability_lower_bound") is None else float(c["reliability_lower_bound"]),
                compute_upper_seconds=None if c.get("compute_upper_seconds") is None else float(c["compute_upper_seconds"]),
                expected_resolution_lower_by_axis={str(k):(None if v is None else float(v)) for k,v in dict(c.get("expected_resolution_lower_by_axis",{})).items()},
                axis_observation_counts={str(k):int(v) for k,v in dict(c.get("axis_observation_counts",{})).items()},
                excluded_counts={str(k):int(v) for k,v in dict(c.get("excluded_counts",{})).items()},
                event_ids=tuple(str(x) for x in c.get("event_ids",())), calibration_id=str(c["calibration_id"]),
            ))
        return cls(
            target_generation=int(obj["target_generation"]), problem_shell=str(obj["problem_shell"]),
            min_attempts=int(obj["min_attempts"]), min_axis_observations=int(obj["min_axis_observations"]),
            one_sided_z=float(obj["one_sided_z"]), calibrations=tuple(calibrations),
            excluded_global_counts={str(k):int(v) for k,v in dict(obj.get("excluded_global_counts",{})).items()},
            fingerprint=str(obj["fingerprint"]),
        )

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentCalibrationSnapshot":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def lookup(self, test_id: str, test_signature: str) -> TestCalibration | None:
        for c in self.calibrations:
            if c.test_id == test_id and c.test_signature == test_signature and c.problem_shell == self.problem_shell:
                return c
        return None


def _wilson_lower(successes: int, total: int, z: float) -> float | None:
    if total <= 0: return None
    p=successes/total
    z2=z*z
    center=(p+z2/(2*total))/(1+z2/total)
    half=z*math.sqrt((p*(1-p)+z2/(4*total))/total)/(1+z2/total)
    return max(0.0, center-half)


def _mean_lower(values: Sequence[float], z: float) -> float | None:
    if not values: return None
    mean=statistics.fmean(values)
    if len(values) == 1: return max(0.0, min(1.0, mean))
    sd=statistics.stdev(values)
    return max(0.0, min(1.0, mean-z*sd/math.sqrt(len(values))))


def _fingerprint(payload: Mapping[str, object]) -> str:
    raw=json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def compile_calibration_snapshot(
    ledger: ExperimentTelemetryLedger | Iterable[ExperimentRunRecord], *, target_generation: int,
    problem_shell: str, min_attempts: int = 5, min_axis_observations: int = 5,
    one_sided_z: float = 1.645,
) -> ExperimentCalibrationSnapshot:
    """Compile future-generation, exact-shell conservative test calibrations."""
    if target_generation < 0: raise ValueError("target_generation must be non-negative")
    if min_attempts < 1 or min_axis_observations < 1: raise ValueError("minimum support must be >= 1")
    if one_sided_z <= 0 or not math.isfinite(one_sided_z): raise ValueError("one_sided_z must be positive")
    events=list(ledger.events if isinstance(ledger, ExperimentTelemetryLedger) else ledger)
    excluded={
        "same_or_future_generation":0, "protected_validation":0, "not_calibration_eligible":0,
        "wrong_shell":0,
    }
    eligible=[]
    for e in events:
        if e.release_generation >= target_generation:
            excluded["same_or_future_generation"]+=1; continue
        if e.evidence_role == EvidenceRole.PROTECTED_VALIDATION:
            excluded["protected_validation"]+=1; continue
        if not e.calibration_eligible:
            excluded["not_calibration_eligible"]+=1; continue
        if e.problem_shell != problem_shell:
            excluded["wrong_shell"]+=1; continue
        eligible.append(e)

    groups: dict[tuple[str,str], list[ExperimentRunRecord]]={}
    for e in eligible: groups.setdefault((e.test_id,e.test_signature),[]).append(e)
    calibrations=[]
    for (test_id,signature), rows in sorted(groups.items()):
        rows=sorted(rows,key=lambda e:e.event_id)
        usable=[e for e in rows if e.usable_measurement]
        local_excluded={
            "failed_or_censored":sum(e.run_status != "COMPLETE" for e in rows),
            "invalid_measurement":sum(e.run_status == "COMPLETE" and not e.measurement_valid for e in rows),
            "unknown_backreaction":sum(e.measurement_backreaction is None for e in rows),
            "unadjusted_backreaction":sum(e.measurement_backreaction is True and not e.backreaction_adjusted for e in rows),
        }
        reliability=_wilson_lower(len(usable),len(rows),one_sided_z) if len(rows) >= min_attempts else None
        compute_values=[float(e.compute_seconds) for e in rows if e.compute_seconds is not None]
        compute_upper=max(compute_values) if len(compute_values) >= min_attempts else None
        axes=sorted(set().union(*(set(e.before_uncertainty_by_axis)|set(e.after_uncertainty_by_axis) for e in usable)) if usable else set())
        resolutions={}; counts={}
        for axis in axes:
            vals=[]
            for e in usable:
                if axis not in e.before_uncertainty_by_axis or axis not in e.after_uncertainty_by_axis: continue
                before=float(e.before_uncertainty_by_axis[axis]); after=float(e.after_uncertainty_by_axis[axis])
                if before <= 0: continue
                vals.append(max(0.0,min(1.0,(before-after)/before)))
            counts[axis]=len(vals)
            resolutions[axis]=_mean_lower(vals,one_sided_z) if len(vals) >= min_axis_observations else None
        core={
            "model_version":MODEL_VERSION,"target_generation":target_generation,"problem_shell":problem_shell,
            "test_id":test_id,"test_signature":signature,"min_attempts":min_attempts,
            "min_axis_observations":min_axis_observations,"one_sided_z":one_sided_z,
            "event_ids":[e.event_id for e in rows],"reliability":reliability,"compute_upper":compute_upper,
            "resolutions":resolutions,
        }
        cid=_fingerprint(core)
        calibrations.append(TestCalibration(
            test_id=test_id, test_signature=signature, problem_shell=problem_shell, target_generation=target_generation,
            attempt_count=len(rows), usable_count=len(usable), reliability_lower_bound=reliability,
            compute_upper_seconds=compute_upper, expected_resolution_lower_by_axis=resolutions,
            axis_observation_counts=counts, excluded_counts=local_excluded,
            event_ids=tuple(e.event_id for e in rows), calibration_id=cid,
        ))
    snap_core={
        "model_version":MODEL_VERSION,"target_generation":target_generation,"problem_shell":problem_shell,
        "min_attempts":min_attempts,"min_axis_observations":min_axis_observations,"one_sided_z":one_sided_z,
        "calibrations":[c.to_dict() for c in calibrations],"excluded_global_counts":excluded,
    }
    fp=_fingerprint(snap_core)
    return ExperimentCalibrationSnapshot(
        target_generation=target_generation, problem_shell=problem_shell, min_attempts=min_attempts,
        min_axis_observations=min_axis_observations, one_sided_z=one_sided_z,
        calibrations=tuple(calibrations), excluded_global_counts=excluded, fingerprint=fp,
    )


def hydrate_contract_from_calibration(contract: ExperimentContract, snapshot: ExperimentCalibrationSnapshot) -> ExperimentContract:
    """Fill only UNKNOWN routing fields from a matching frozen calibration snapshot."""
    if snapshot.target_generation != contract.search_generation:
        raise ValueError("calibration target generation does not match experiment contract")
    if snapshot.problem_shell != contract.problem_shell:
        raise ValueError("calibration shell does not match experiment contract")
    tests=[]
    for t in contract.tests:
        signature=getattr(t,"test_signature",None)
        cal=snapshot.lookup(t.test_id,signature) if signature else None
        if cal is None:
            tests.append(t); continue
        expected=dict(t.expected_resolution_by_axis)
        for axis in {a.axis_id for a in contract.axes}:
            if expected.get(axis) is None and axis in cal.expected_resolution_lower_by_axis:
                expected[axis]=cal.expected_resolution_lower_by_axis[axis]
        compute=t.compute_seconds if t.compute_seconds is not None else cal.compute_upper_seconds
        reliability=t.reliability if t.reliability is not None else cal.reliability_lower_bound
        calibration_id=t.calibration_id or f"AUTO_R5:{cal.calibration_id}"
        notes=(t.notes+" | " if t.notes else "")+f"R5_AUTO_CALIBRATION:{snapshot.fingerprint[:16]}"
        tests.append(replace(
            t, expected_resolution_by_axis=expected, compute_seconds=compute, reliability=reliability,
            calibration_id=calibration_id, notes=notes,
        ))
    return replace(contract, tests=tuple(tests), provenance=tuple(contract.provenance)+(f"experiment_calibration_snapshot:{snapshot.fingerprint}",))


def record_from_round(
    contract: ExperimentContract, plan: ExperimentPlan, outcome: ExperimentOutcome, *, event_id: str,
    compute_seconds: float | None, calibration_eligible: bool, measurement_valid: bool = True,
    run_status: str = "COMPLETE", release_generation: int | None = None, shell_tags: Sequence[str] = (),
    provenance: Sequence[str] = (),
) -> ExperimentRunRecord:
    """Create a standardized telemetry row from an already-frozen experiment round."""
    if plan.contract_fingerprint != contract.fingerprint(): raise ValueError("plan/contract fingerprint mismatch")
    if plan.selected_test_id != outcome.test_id: raise ValueError("outcome is not for the frozen selected test")
    test=next((t for t in contract.tests if t.test_id == outcome.test_id),None)
    if test is None: raise ValueError("selected test missing from contract")
    signature=getattr(test,"test_signature",None)
    if not signature: raise ValueError("automatic telemetry requires test_signature")
    before={a.axis_id:a.uncertainty for a in contract.axes}
    after=dict(before); after.update({str(k):float(v) for k,v in outcome.realized_uncertainty_by_axis.items()})
    return ExperimentRunRecord(
        event_id=event_id, decision_id=contract.decision_id, test_id=test.test_id, test_signature=signature,
        problem_shell=contract.problem_shell, shell_tags=tuple(str(x) for x in shell_tags),
        search_generation=contract.search_generation, selection_round=contract.selection_round,
        release_generation=contract.search_generation if release_generation is None else int(release_generation),
        release_round=outcome.release_round, contract_fingerprint=contract.fingerprint(),
        evidence_role=outcome.role, calibration_eligible=bool(calibration_eligible),
        measurement_backreaction=test.measurement_backreaction, backreaction_adjusted=test.backreaction_adjusted,
        before_uncertainty_by_axis=before, after_uncertainty_by_axis=after,
        compute_seconds=compute_seconds, run_status=run_status, measurement_valid=measurement_valid,
        provenance=tuple(str(x) for x in provenance)+tuple(outcome.provenance),
    )
