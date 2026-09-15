"""Leakage-resistant relevance learning for the LabAllCompass search engine.

This module does not turn benchmark outcomes into scientific evidence. It learns a
small, bounded retrieval prior for *future search generations*.

Contract:
    SEARCH GENERATION g FREEZES RELEVANCE SNAPSHOT
      -> candidates are retrieved / composed / evaluated
      -> outcomes are appended to the feedback ledger
      -> same-generation outcomes cannot alter generation g search
      -> only explicitly LEARN_AFTER_GENERATION events released before g+1 may
         influence generation g+1
      -> PROTECTED_VALIDATION and DIAGNOSTIC_ONLY events never train retrieval

The learned prior is intentionally weak relative to direct mechanism relevance.
It can break ties / improve ordering inside a relevant region, but it is bounded
so historical success cannot make an irrelevant mechanism dominate a new query.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import hashlib
import json
import math

LEARN_AFTER_GENERATION = "LEARN_AFTER_GENERATION"
PROTECTED_VALIDATION = "PROTECTED_VALIDATION"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
VALID_ROLES = frozenset({LEARN_AFTER_GENERATION, PROTECTED_VALIDATION, DIAGNOSTIC_ONLY})

HELPED = "HELPED"
HURT = "HURT"
NEUTRAL = "NEUTRAL"
INCONCLUSIVE = "INCONCLUSIVE"
OUTCOME_VALUE = {HELPED: 1.0, HURT: -1.0, NEUTRAL: 0.0}
VALID_OUTCOMES = frozenset({HELPED, HURT, NEUTRAL, INCONCLUSIVE})

SNAPSHOT_VERSION = 1
MODEL_VERSION = "LAB_RELEVANCE_R1_2026-08-26"


@dataclass(frozen=True)
class FeedbackEvent:
    event_id: str
    subject_id: str
    selection_generation: int
    release_generation: int
    problem_shell: str
    outcome: str
    weight: float = 1.0
    role: str = LEARN_AFTER_GENERATION
    shell_tags: tuple[str, ...] = ()
    consumer_id: str | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id or not self.subject_id:
            raise ValueError("event_id and subject_id are required")
        if self.selection_generation < 0 or self.release_generation < 0:
            raise ValueError("generation numbers must be non-negative")
        if self.release_generation < self.selection_generation:
            raise ValueError("release_generation cannot precede selection_generation")
        if self.role not in VALID_ROLES:
            raise ValueError(f"unknown feedback role: {self.role}")
        if self.outcome not in VALID_OUTCOMES:
            raise ValueError(f"unknown outcome: {self.outcome}")
        if not math.isfinite(self.weight) or self.weight < 0 or self.weight > 1:
            raise ValueError("weight must be finite and within [0, 1]")

    @classmethod
    def from_dict(cls, obj: Mapping[str, object]) -> "FeedbackEvent":
        tags = obj.get("shell_tags", ())
        if isinstance(tags, str):
            tags = (tags,)
        return cls(
            event_id=str(obj["event_id"]),
            subject_id=str(obj["subject_id"]),
            selection_generation=int(obj["selection_generation"]),
            release_generation=int(obj["release_generation"]),
            problem_shell=str(obj.get("problem_shell", "UNSPECIFIED")),
            outcome=str(obj["outcome"]),
            weight=float(obj.get("weight", 1.0)),
            role=str(obj.get("role", LEARN_AFTER_GENERATION)),
            shell_tags=tuple(sorted({str(x).strip().lower() for x in tags if str(x).strip()})),
            consumer_id=(str(obj["consumer_id"]) if obj.get("consumer_id") else None),
            provenance=(dict(obj.get("provenance", {})) if isinstance(obj.get("provenance", {}), Mapping) else {}),
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "subject_id": self.subject_id,
            "selection_generation": self.selection_generation,
            "release_generation": self.release_generation,
            "problem_shell": self.problem_shell,
            "shell_tags": list(self.shell_tags),
            "outcome": self.outcome,
            "weight": self.weight,
            "role": self.role,
            "consumer_id": self.consumer_id,
            "provenance": dict(self.provenance),
        }


class FeedbackLedger:
    """Append-oriented feedback event collection with duplicate-id protection."""

    def __init__(self, events: Iterable[FeedbackEvent] = ()):
        self._events: list[FeedbackEvent] = []
        self._ids: set[str] = set()
        for event in events:
            self.append(event)

    def append(self, event: FeedbackEvent) -> None:
        if event.event_id in self._ids:
            raise ValueError(f"duplicate feedback event_id: {event.event_id}")
        self._ids.add(event.event_id)
        self._events.append(event)

    @property
    def events(self) -> tuple[FeedbackEvent, ...]:
        return tuple(self._events)

    @classmethod
    def load_jsonl(cls, path: str | Path) -> "FeedbackLedger":
        p = Path(path)
        if not p.exists():
            return cls()
        events = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(FeedbackEvent.from_dict(json.loads(line)))
        return cls(events)

    def save_jsonl(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(e.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for e in self._events), encoding="utf-8")


@dataclass(frozen=True)
class RelevanceSnapshot:
    target_generation: int
    problem_shell: str
    shell_tags: tuple[str, ...]
    document_offsets: Mapping[str, float]
    supplier_offsets_by_consumer: Mapping[str, Mapping[str, float]]
    included_event_ids: tuple[str, ...]
    quarantined_events: tuple[Mapping[str, str], ...]
    model_version: str = MODEL_VERSION
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if self.target_generation < 0:
            raise ValueError("target_generation must be non-negative")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", self._compute_fingerprint())

    def _compute_fingerprint(self) -> str:
        payload = {
            "snapshot_version": SNAPSHOT_VERSION,
            "model_version": self.model_version,
            "target_generation": self.target_generation,
            "problem_shell": self.problem_shell,
            "shell_tags": list(self.shell_tags),
            "document_offsets": dict(sorted((k, float(v)) for k, v in self.document_offsets.items())),
            "supplier_offsets_by_consumer": {
                c: dict(sorted((s, float(v)) for s, v in offsets.items()))
                for c, offsets in sorted(self.supplier_offsets_by_consumer.items())
            },
            "included_event_ids": list(self.included_event_ids),
            "quarantined_events": [dict(x) for x in self.quarantined_events],
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def supplier_offsets(self, consumer_id: str) -> dict[str, float]:
        base = dict(self.document_offsets)
        for subject, bonus in self.supplier_offsets_by_consumer.get(consumer_id, {}).items():
            base[subject] = base.get(subject, 0.0) + float(bonus)
        return base

    def to_dict(self) -> dict:
        return {
            "snapshot_version": SNAPSHOT_VERSION,
            "model_version": self.model_version,
            "target_generation": self.target_generation,
            "problem_shell": self.problem_shell,
            "shell_tags": list(self.shell_tags),
            "document_offsets": dict(self.document_offsets),
            "supplier_offsets_by_consumer": {k: dict(v) for k, v in self.supplier_offsets_by_consumer.items()},
            "included_event_ids": list(self.included_event_ids),
            "quarantined_events": [dict(x) for x in self.quarantined_events],
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, obj: Mapping[str, object]) -> "RelevanceSnapshot":
        if int(obj.get("snapshot_version", -1)) != SNAPSHOT_VERSION:
            raise ValueError("unsupported relevance snapshot version")
        doc = obj.get("document_offsets", {})
        pair = obj.get("supplier_offsets_by_consumer", {})
        if not isinstance(doc, Mapping) or not isinstance(pair, Mapping):
            raise ValueError("invalid relevance snapshot offsets")
        instance = cls(
            target_generation=int(obj["target_generation"]),
            problem_shell=str(obj.get("problem_shell", "UNSPECIFIED")),
            shell_tags=tuple(str(x) for x in obj.get("shell_tags", ())),
            document_offsets={str(k): float(v) for k, v in doc.items()},
            supplier_offsets_by_consumer={
                str(c): {str(s): float(v) for s, v in offsets.items()}
                for c, offsets in pair.items() if isinstance(offsets, Mapping)
            },
            included_event_ids=tuple(str(x) for x in obj.get("included_event_ids", ())),
            quarantined_events=tuple(dict(x) for x in obj.get("quarantined_events", ()) if isinstance(x, Mapping)),
            model_version=str(obj.get("model_version", MODEL_VERSION)),
        )
        supplied = str(obj.get("fingerprint", ""))
        if supplied and supplied != instance.fingerprint:
            raise ValueError("relevance snapshot fingerprint mismatch")
        return instance

    @classmethod
    def load(cls, path: str | Path) -> "RelevanceSnapshot":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _shell_match(event: FeedbackEvent, target_shell: str, target_tags: frozenset[str]) -> float:
    if event.problem_shell.strip().lower() == target_shell.strip().lower():
        return 1.0
    etags = frozenset(event.shell_tags)
    if not etags or not target_tags:
        return 0.0
    inter = len(etags & target_tags)
    if not inter:
        return 0.0
    jaccard = inter / len(etags | target_tags)
    return 0.35 * jaccard


def _posterior_bonus(sum_signed: float, total_weight: float, *, scale: float, prior_strength: float, cap: float) -> float:
    if total_weight <= 0:
        return 0.0
    value = scale * sum_signed / (prior_strength + total_weight)
    return max(-cap, min(cap, value))


def compile_relevance_snapshot(
    ledger: FeedbackLedger,
    documents: Iterable[object],
    *,
    target_generation: int,
    problem_shell: str,
    shell_tags: Sequence[str] = (),
) -> RelevanceSnapshot:
    """Compile an immutable, shell-scoped prior for one future search generation.

    `documents` need only expose document_id and family attributes. Unknown event
    subjects are quarantined rather than silently ignored.
    """
    docs = tuple(documents)
    by_id = {str(getattr(d, "document_id")): d for d in docs}
    target_tags = frozenset(str(x).strip().lower() for x in shell_tags if str(x).strip())

    direct: dict[str, list[float]] = {}
    family_stats: dict[str, list[float]] = {}
    family_subjects: dict[str, set[str]] = {}
    pair: dict[str, dict[str, list[float]]] = {}
    included: list[str] = []
    quarantined: list[dict[str, str]] = []

    for event in ledger.events:
        reason = None
        if event.role == PROTECTED_VALIDATION:
            reason = "PROTECTED_VALIDATION_NEVER_TRAINS"
        elif event.role == DIAGNOSTIC_ONLY:
            reason = "DIAGNOSTIC_ONLY_NEVER_TRAINS"
        elif event.release_generation >= target_generation or event.selection_generation >= target_generation:
            reason = "SAME_OR_FUTURE_GENERATION_QUARANTINE"
        elif event.outcome == INCONCLUSIVE or event.weight == 0:
            reason = "INCONCLUSIVE_OR_ZERO_WEIGHT"
        elif event.subject_id not in by_id:
            reason = "UNKNOWN_SUBJECT"
        else:
            shell_weight = _shell_match(event, problem_shell, target_tags)
            if shell_weight <= 0:
                reason = "OUT_OF_SCOPE_SHELL"

        if reason is not None:
            quarantined.append({"event_id": event.event_id, "reason": reason})
            continue

        shell_weight = _shell_match(event, problem_shell, target_tags)
        signed = OUTCOME_VALUE[event.outcome] * event.weight * shell_weight
        effective_weight = event.weight * shell_weight
        included.append(event.event_id)

        if event.consumer_id:
            pair.setdefault(event.consumer_id, {}).setdefault(event.subject_id, [0.0, 0.0])
            pair[event.consumer_id][event.subject_id][0] += signed
            pair[event.consumer_id][event.subject_id][1] += effective_weight
        else:
            direct.setdefault(event.subject_id, [0.0, 0.0])
            direct[event.subject_id][0] += signed
            direct[event.subject_id][1] += effective_weight
            family = str(getattr(by_id[event.subject_id], "family", ""))
            family_stats.setdefault(family, [0.0, 0.0])
            family_stats[family][0] += signed
            family_stats[family][1] += effective_weight
            family_subjects.setdefault(family, set()).add(event.subject_id)

    family_bonus: dict[str, float] = {}
    for family, (signed, total) in family_stats.items():
        # Do not generalize a family from one mechanism only.
        if len(family_subjects.get(family, ())) < 2:
            continue
        family_bonus[family] = _posterior_bonus(signed, total, scale=0.45, prior_strength=5.0, cap=0.35)

    doc_offsets: dict[str, float] = {}
    for doc_id, doc in by_id.items():
        value = family_bonus.get(str(getattr(doc, "family", "")), 0.0)
        if doc_id in direct:
            signed, total = direct[doc_id]
            value += _posterior_bonus(signed, total, scale=1.6, prior_strength=2.0, cap=1.25)
        value = max(-1.5, min(1.5, value))
        if abs(value) > 1e-15:
            doc_offsets[doc_id] = value

    supplier_offsets: dict[str, dict[str, float]] = {}
    for consumer, rows in pair.items():
        out = {}
        for subject, (signed, total) in rows.items():
            value = _posterior_bonus(signed, total, scale=1.5, prior_strength=2.0, cap=1.10)
            if abs(value) > 1e-15:
                out[subject] = value
        if out:
            supplier_offsets[consumer] = out

    return RelevanceSnapshot(
        target_generation=target_generation,
        problem_shell=problem_shell,
        shell_tags=tuple(sorted(target_tags)),
        document_offsets=doc_offsets,
        supplier_offsets_by_consumer=supplier_offsets,
        included_event_ids=tuple(sorted(included)),
        quarantined_events=tuple(sorted(quarantined, key=lambda x: (x["event_id"], x["reason"]))),
    )


def compile_snapshot_from_paths(
    ledger_path: str | Path,
    corpus_path: str | Path,
    *,
    target_generation: int,
    problem_shell: str,
    shell_tags: Sequence[str] = (),
) -> RelevanceSnapshot:
    from lab_search_engine import load_search_corpus
    return compile_relevance_snapshot(
        FeedbackLedger.load_jsonl(ledger_path),
        load_search_corpus(corpus_path),
        target_generation=target_generation,
        problem_shell=problem_shell,
        shell_tags=shell_tags,
    )
