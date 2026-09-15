"""Relational Evidence Localizer: conditional scores under an explicit XOR model.

Scores are not calibrated probabilities of alteration. Different record pairs
still use a conditional-independence assumption; deduplication only removes
identical deterministic comparisons, not general evidence dependence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class EvidenceRecord:
    name: str
    party: str
    value: float
    alteration_prior: float = 0.05

    def __post_init__(self) -> None:
        if not self.name or not self.party or not math.isfinite(self.value):
            raise ValueError("record name, party and finite value are required")
        if not 0 < self.alteration_prior < 1:
            raise ValueError("alteration_prior must be between zero and one")


@dataclass(frozen=True)
class ConsistencyRelation:
    name: str
    left: str
    right: str
    tolerance: float = 0.0

    def __post_init__(self):
        if not self.name or not math.isfinite(self.tolerance) or self.tolerance < 0:
            raise ValueError("relation name and finite non-negative tolerance are required")
        if self.left == self.right:
            raise ValueError("A relation must compare two distinct records")


@dataclass(frozen=True)
class LocalizationCandidate:
    records: tuple[str, ...]
    log_likelihood: float
    posterior: float
    predicted_violations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RelationalEvidenceLocalizer:
    def __init__(
        self,
        detection_probability: float = 0.95,
        false_violation_probability: float = 0.02,
    ) -> None:
        if not 0 < detection_probability < 1:
            raise ValueError("detection_probability must be between zero and one")
        if not 0 < false_violation_probability < 1:
            raise ValueError("false_violation_probability must be between zero and one")
        self.detection = detection_probability
        self.false_violation = false_violation_probability

    @staticmethod
    def violation_pattern(
        records: Mapping[str, EvidenceRecord], relations: Sequence[ConsistencyRelation]
    ) -> dict[str, bool]:
        if len({r.name for r in relations}) != len(relations):
            raise ValueError("Relation names must be unique")
        pattern: dict[str, bool] = {}
        for relation in relations:
            if relation.left not in records or relation.right not in records:
                raise KeyError(f"Relation {relation.name} references a missing record")
            delta = abs(records[relation.left].value - records[relation.right].value)
            pattern[relation.name] = delta > relation.tolerance
        return pattern

    def localize(
        self,
        records: Sequence[EvidenceRecord],
        relations: Sequence[ConsistencyRelation],
        max_colluding_records: int = 2,
    ) -> dict[str, Any]:
        if not records:
            raise ValueError("At least one evidence record is required")
        if type(max_colluding_records) is not int or max_colluding_records < 1:
            raise ValueError("max_colluding_records must be at least one")
        record_map = {record.name: record for record in records}
        if len(record_map) != len(records):
            raise ValueError("Evidence record names must be unique")
        observed = self.violation_pattern(record_map, relations)
        # Repeating the same comparison adds no observation. Reversing its
        # endpoints also leaves abs(left - right) unchanged.
        unique = {}
        aliases = {}
        for relation in relations:
            pair = tuple(sorted((relation.left, relation.right)))
            if pair in unique and unique[pair].tolerance != relation.tolerance:
                raise ValueError("Multiple tolerances for the same record pair require a joint observation model")
            unique.setdefault(pair, relation)
            aliases.setdefault(unique[pair].name, []).append(relation.name)
        limit = min(max_colluding_records, len(records))
        if sum(math.comb(len(records), k) for k in range(limit + 1)) > 100000:
            raise ValueError("Localization exceeds 100,000 candidate subsets")
        candidates: list[tuple[tuple[str, ...], float, tuple[str, ...]]] = []

        # Include the null explanation; consistent data must not force blame.
        for size in range(limit + 1):
            for names in combinations(sorted(record_map), size):
                culprit = set(names)
                predicted: list[str] = []
                log_likelihood = sum(
                    math.log(record.alteration_prior)
                    if record.name in culprit
                    else math.log(1.0 - record.alteration_prior)
                    for record in records
                )
                for relation in unique.values():
                    # XOR represents coherent collusion: two jointly altered
                    # records can agree with each other while disagreeing with
                    # independently generated records.
                    affected = (relation.left in culprit) ^ (relation.right in culprit)
                    if affected:
                        predicted.extend(aliases[relation.name])
                    probability = (
                        self.detection
                        if affected and observed[relation.name]
                        else 1.0 - self.detection
                        if affected
                        else self.false_violation
                        if observed[relation.name]
                        else 1.0 - self.false_violation
                    )
                    log_likelihood += math.log(probability)
                # Mild sparsity prior: prefer a smaller explanation only when
                # it explains the violation pattern nearly as well.
                log_likelihood -= 0.7 * size
                candidates.append((names, log_likelihood, tuple(predicted)))

        max_log = max(row[1] for row in candidates)
        weights = [math.exp(row[1] - max_log) for row in candidates]
        normalizer = sum(weights)
        ranked = [
            LocalizationCandidate(names, score, weight / normalizer, predicted)
            for (names, score, predicted), weight in zip(candidates, weights)
        ]
        ranked.sort(key=lambda item: item.posterior, reverse=True)
        return {
            "observed_violations": [name for name, violated in observed.items() if violated],
            "passing_relations": [name for name, violated in observed.items() if not violated],
            "ranking": [candidate.as_dict() for candidate in ranked],
            "top_candidate": ranked[0].as_dict(),
            "observation_groups": aliases,
            "unique_observation_count": len(unique),
            "model": {
                "weight_interpretation": "Conditional model weights, not calibrated alteration probabilities",
                "null_candidate_included": True,
                "maximum_altered_records": limit,
                "detection_probability": self.detection,
                "false_violation_probability": self.false_violation,
                "additional_log_sparsity_penalty_per_record": 0.7,
                "assumptions": [
                    "XOR: two altered endpoints are assumed to agree coherently",
                    "Distinct record-pair observations are assumed conditionally independent; overlapping comparisons may violate this",
                    "Record priors are multiplied independently; party labels do not establish source independence",
                    "Weights are normalized only over the enumerated subsets",
                ],
            },
        }


def records_from_dict(values: Mapping[str, Mapping[str, Any]]) -> list[EvidenceRecord]:
    return [
        EvidenceRecord(
            name=name,
            party=str(item["party"]),
            value=float(item["value"]),
            alteration_prior=float(item.get("alteration_prior", 0.05)),
        )
        for name, item in values.items()
    ]
