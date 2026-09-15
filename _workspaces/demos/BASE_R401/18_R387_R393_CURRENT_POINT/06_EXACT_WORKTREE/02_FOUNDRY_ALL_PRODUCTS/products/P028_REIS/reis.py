from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations


@dataclass(frozen=True)
class EvidenceImpactResult:
    posterior_impact: dict[str, float]
    posterior_priority: tuple[str, ...]
    impact_priority: tuple[str, ...]
    selected_safeguards: tuple[str, ...]
    total_expected_impact_covered: float


def allocate_relational_safeguards(
    posterior_culprit: dict[str, float],
    empirical_consequence: dict[str, float],
    safeguard_cost: dict[str, float],
    *,
    budget: float,
) -> EvidenceImpactResult:
    keys=set(posterior_culprit)
    if keys != set(empirical_consequence) or keys != set(safeguard_cost): raise ValueError('record sets must align')
    risk={k:posterior_culprit[k]*empirical_consequence[k] for k in keys}
    feasible=[]
    ordered=sorted(keys)
    for n in range(len(ordered)+1):
        for subset in combinations(ordered,n):
            if sum(safeguard_cost[k] for k in subset)<=budget+1e-12:
                feasible.append((sum(risk[k] for k in subset),subset))
    value,selected=max(feasible,key=lambda x:(x[0],tuple(reversed(x[1]))))
    return EvidenceImpactResult(risk,tuple(sorted(keys,key=posterior_culprit.get,reverse=True)),tuple(sorted(keys,key=risk.get,reverse=True)),selected,value)
