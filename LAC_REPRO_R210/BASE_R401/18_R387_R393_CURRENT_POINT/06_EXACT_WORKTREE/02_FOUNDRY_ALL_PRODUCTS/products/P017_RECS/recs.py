"""Relational-evidence-conditioned safeguards (RECS) v0.1."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

if __package__:
    from .parents.csid import ContractSafeguardDesigner, FailureMode, Safeguard
else:
    from parents.csid import ContractSafeguardDesigner, FailureMode, Safeguard
if __package__:
    from .parents.rel import ConsistencyRelation, EvidenceRecord, RelationalEvidenceLocalizer
else:
    from parents.rel import ConsistencyRelation, EvidenceRecord, RelationalEvidenceLocalizer


def marginal_culprit_probabilities(localization: Mapping[str, Any]) -> dict[str, float]:
    marginals: dict[str, float] = {}
    for candidate in localization["ranking"]:
        for name in candidate["records"]:
            marginals[name] = marginals.get(name, 0.0) + float(candidate["posterior"])
    return marginals


class RelationalEvidenceConditionedSafeguards:
    def __init__(self, *, max_colluding_records: int = 2) -> None:
        if max_colluding_records < 1:
            raise ValueError("max_colluding_records must be positive")
        self.max_colluding_records = int(max_colluding_records)

    def design(
        self,
        *,
        records: Sequence[EvidenceRecord],
        relations: Sequence[ConsistencyRelation],
        consequences: Mapping[str, float],
        safeguards: Sequence[Safeguard],
        budget: float,
    ) -> dict[str, Any]:
        names = {record.name for record in records}
        if names != set(consequences):
            raise ValueError("consequence names must match evidence record names exactly")
        localizer = RelationalEvidenceLocalizer()
        localization = localizer.localize(
            records,
            relations,
            max_colluding_records=self.max_colluding_records,
        )
        posterior = marginal_culprit_probabilities(localization)
        posterior_failures = [
            FailureMode(name, posterior.get(name, 0.0), float(consequences[name]))
            for name in sorted(names)
        ]
        prior_failures = [
            FailureMode(record.name, record.alteration_prior, float(consequences[record.name]))
            for record in records
        ]
        prior_designer = ContractSafeguardDesigner(prior_failures, safeguards)
        posterior_designer = ContractSafeguardDesigner(posterior_failures, safeguards)
        prior_design = prior_designer.design(budget)["selected"]
        posterior_design = posterior_designer.design(budget)["selected"]
        by_name = {safeguard.name: safeguard for safeguard in safeguards}
        prior_selection = [by_name[name] for name in prior_design["safeguards"]]
        prior_under_posterior = posterior_designer.evaluate(prior_selection).as_dict()
        reduction = (
            0.0
            if prior_under_posterior["objective"] == 0
            else 1.0 - posterior_design["objective"] / prior_under_posterior["objective"]
        )
        return {
            "localization": localization,
            "posterior_culprit_probability_by_record": posterior,
            "prior_portfolio": prior_design,
            "evidence_conditioned_portfolio": posterior_design,
            "prior_portfolio_objective_under_posterior": prior_under_posterior["objective"],
            "posterior_objective_reduction_vs_prior_design": float(reduction),
            "posterior_semantics": (
                "conditional on REL's enumerated culprit-set hypothesis space including no altered records; "
                "not an unconditional fraud probability"
            ),
        }
