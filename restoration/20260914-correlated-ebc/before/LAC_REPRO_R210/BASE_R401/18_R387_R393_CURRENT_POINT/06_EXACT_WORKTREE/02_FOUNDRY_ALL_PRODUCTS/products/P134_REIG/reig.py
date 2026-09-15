"""Relational-Evidence Integrity Gate (REIG) v0.1.

REL localizes relationally inconsistent records. REIG converts REL's *conditional*
source-suspect marginals into an explicit historical-borrowing power gate before
calling EBC. The gate activates only when REL observes at least one declared
consistency violation.

This does NOT interpret REL posterior mass as an unconditional fraud probability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Sequence

if __package__:
    from .parents.rel import EvidenceRecord, ConsistencyRelation, RelationalEvidenceLocalizer
else:
    from parents.rel import EvidenceRecord, ConsistencyRelation, RelationalEvidenceLocalizer
if __package__:
    from .parents.ebc import HistoricalEstimate, BorrowingResult, borrow_evidence, coalesce_history
else:
    from parents.ebc import HistoricalEstimate, BorrowingResult, borrow_evidence, coalesce_history


@dataclass(frozen=True)
class IntegrityContribution:
    name: str
    conditional_suspect_probability: float | None
    integrity_multiplier: float
    declared_maximum_power: float
    gated_maximum_power: float


@dataclass(frozen=True)
class IntegrityBorrowingResult:
    observed_violations: tuple[str, ...]
    integrity_gate_active: bool
    posterior_semantics: str
    integrity_exponent: float
    contributions: tuple[IntegrityContribution, ...]
    ungated: BorrowingResult
    gated: BorrowingResult
    observation_aliases: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict:
        return {
            "observed_violations": list(self.observed_violations),
            "integrity_gate_active": self.integrity_gate_active,
            "posterior_semantics": self.posterior_semantics,
            "integrity_exponent": self.integrity_exponent,
            "contributions": [asdict(x) for x in self.contributions],
            "ungated": self.ungated.to_dict(),
            "gated": self.gated.to_dict(),
            "observation_aliases": dict(self.observation_aliases),
        }


def _marginal_conditional_suspect(localization: dict) -> dict[str, float]:
    marginals: dict[str, float] = {}
    for candidate in localization["ranking"]:
        p = float(candidate["posterior"])
        for name in candidate["records"]:
            marginals[name] = marginals.get(name, 0.0) + p
    return marginals


def gate_and_borrow(
    *,
    current_estimate: float,
    current_standard_error: float,
    evidence_records: Sequence[EvidenceRecord],
    relations: Sequence[ConsistencyRelation],
    historical: Sequence[HistoricalEstimate],
    max_colluding_records: int = 2,
    integrity_exponent: float = 1.0,
    compatibility_scale: float = 1.5,
    borrowing_cap_ratio: float = 2.0,
    current_observation_id: str | None = None,
) -> IntegrityBorrowingResult:
    """Run REL integrity localization, then EBC with source-specific gated powers.

    The source-name sets must match exactly. When no declared relational violation
    is observed, integrity gating is inactive and EBC receives original powers.
    When violations exist, the declared policy is
        gated_power = declared_power * (1 - p_suspect_conditional)**integrity_exponent.
    """
    if integrity_exponent <= 0:
        raise ValueError("integrity_exponent must be positive")
    records = tuple(evidence_records)
    history = tuple(historical)
    record_names = {r.name for r in records}
    history_names = {h.name for h in history}
    if len(record_names) != len(records) or len(history_names) != len(history):
        raise ValueError("source names must be unique")
    if record_names != history_names:
        raise ValueError("evidence-record names must match historical-estimate names exactly")

    localizer = RelationalEvidenceLocalizer()
    # Identity must survive BOTH stages: otherwise duplicate records would
    # alter REL's priors/relations before EBC had a chance to collapse them.
    unique_history, aliases = coalesce_history(history)
    record_map = {r.name:r for r in records}
    localizer.violation_pattern(record_map, relations)
    for record in records:
        representative = record_map[aliases[record.name]]
        if (record.value, record.alteration_prior) != (representative.value, representative.alteration_prior):
            raise ValueError('Observation aliases must have identical REL values and alteration priors')
    unique_records = tuple(record_map[h.name] for h in unique_history)
    unique_relations = tuple(ConsistencyRelation(r.name,aliases[r.left],aliases[r.right],r.tolerance)
                             for r in relations if aliases[r.left] != aliases[r.right])
    localized = localizer.localize(unique_records, unique_relations, max_colluding_records=max_colluding_records)
    violations = tuple(localized["observed_violations"])
    active = bool(violations)
    marginals = _marginal_conditional_suspect(localized) if active else {}

    gated_history: list[HistoricalEstimate] = []
    integrity_rows: list[IntegrityContribution] = []
    for item in history:
        if active:
            p = min(1.0, max(0.0, float(marginals.get(aliases[item.name], 0.0))))
            multiplier = (1.0 - p) ** integrity_exponent
            conditional: float | None = p
        else:
            multiplier = 1.0
            conditional = None
        gated_power = item.maximum_power * multiplier
        gated_history.append(replace(item, maximum_power=gated_power))
        integrity_rows.append(
            IntegrityContribution(
                name=item.name,
                conditional_suspect_probability=conditional,
                integrity_multiplier=float(multiplier),
                declared_maximum_power=float(item.maximum_power),
                gated_maximum_power=float(gated_power),
            )
        )

    kwargs = dict(compatibility_scale=compatibility_scale, borrowing_cap_ratio=borrowing_cap_ratio,
                  current_observation_id=current_observation_id)
    ungated = borrow_evidence(current_estimate, current_standard_error, history, **kwargs)
    gated = borrow_evidence(current_estimate, current_standard_error, gated_history, **kwargs)
    return IntegrityBorrowingResult(
        observed_violations=violations,
        integrity_gate_active=active,
        posterior_semantics=(
            "REL marginal suspect probabilities are conditional on the enumerated culprit-set hypothesis space including no altered records; "
            "they are used only as a declared borrowing-power gate, not as unconditional fraud probabilities."
        ),
        integrity_exponent=float(integrity_exponent),
        contributions=tuple(integrity_rows),
        ungated=ungated,
        gated=gated,
        observation_aliases=tuple(sorted(aliases.items())),
    )
