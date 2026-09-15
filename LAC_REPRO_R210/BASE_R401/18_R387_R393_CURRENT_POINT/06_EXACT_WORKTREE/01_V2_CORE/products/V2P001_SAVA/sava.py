from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations


@dataclass(frozen=True)
class AuditCandidate:
    name: str
    nominal_liquidity: float
    pool_contributions: tuple[float, ...]


@dataclass(frozen=True)
class SAVAResult:
    mode: str
    selected_audits: tuple[str, ...]
    allocated_shared_capacity: dict[str, float]
    expected_deployable_liquidity: float
    naive_independent_value: float
    overlap_removed_value: float
    status: str

    def to_dict(self): return asdict(self)


class SharedAuditRank:
    """Monotone submodular pool-rank oracle from the LCB shared-capacity kernel."""
    def __init__(self,candidates,pool_capacities):
        self.candidates=tuple(candidates); self.capacities=tuple(float(x) for x in pool_capacities)
        if any(x<0 for x in self.capacities): raise ValueError('pool capacities must be nonnegative')
        if any(len(c.pool_contributions)!=len(self.capacities) or any(x<0 for x in c.pool_contributions) for c in self.candidates): raise ValueError('nonnegative aligned pool contributions required')

    def __call__(self,subset):
        indices=tuple(subset)
        return sum(min(cap,sum(self.candidates[i].pool_contributions[p] for i in indices)) for p,cap in enumerate(self.capacities))


def _allocate_polymatroid(rank,values,indices):
    order=sorted(indices,key=lambda i:(-values[i],i)); chosen=[]; previous=0.; allocation={i:0. for i in indices}
    for i in order:
        chosen.append(i); current=float(rank(chosen))
        if current+1e-12<previous: raise ValueError('rank oracle must be monotone')
        allocation[i]=current-previous; previous=current
    return allocation


def _scenario_value(rank,candidates,subset,culprits):
    clean=[i for i in subset if candidates[i].name not in culprits]
    values=[c.nominal_liquidity for c in candidates]
    allocation=_allocate_polymatroid(rank,values,clean)
    return sum(values[i]*allocation[i] for i in clean)


def allocate_verification_liquidity(candidates,pool_capacities,scenarios,*,audit_slots=None,exact_limit=16):
    """Compose posterior audit triage with shared-capacity polymatroid allocation.

    `scenarios` is an iterable of `(probability, culprit_names)`. For small candidate
    sets and a declared slot budget, all subsets are re-optimized exactly. Otherwise
    expected-clean values drive an exact continuous polymatroid allocation.
    """
    candidates=tuple(candidates); scenarios=tuple((float(p),set(c)) for p,c in scenarios)
    if not candidates or not scenarios or abs(sum(p for p,_ in scenarios)-1)>1e-9: raise ValueError('nonempty candidates and normalized scenarios required')
    rank=SharedAuditRank(candidates,pool_capacities); names=[c.name for c in candidates]
    clean_probability=[sum(p for p,culprits in scenarios if name not in culprits) for name in names]
    naive=sum(c.nominal_liquidity*sum(c.pool_contributions)*clean_probability[i] for i,c in enumerate(candidates))
    if audit_slots is not None and len(candidates)<=exact_limit:
        if audit_slots<0 or audit_slots>len(candidates): raise ValueError('invalid audit_slots')
        scored=[]
        for subset in combinations(range(len(candidates)),audit_slots):
            expected=sum(p*_scenario_value(rank,candidates,subset,culprits) for p,culprits in scenarios)
            scored.append((expected,tuple(-i for i in subset),subset))
        expected,_,selected=max(scored)
        expected_values=[c.nominal_liquidity*clean_probability[i] for i,c in enumerate(candidates)]
        allocation=_allocate_polymatroid(rank,expected_values,list(selected))
        mode='EXACT_POSTERIOR_SUBSET_REOPTIMIZATION'
    else:
        selected=tuple(range(len(candidates))); expected_values=[c.nominal_liquidity*clean_probability[i] for i,c in enumerate(candidates)]
        allocation=_allocate_polymatroid(rank,expected_values,list(selected)); expected=sum(expected_values[i]*allocation[i] for i in selected)
        mode='SCALABLE_POLYMATROID_EXPECTED_VALUE_ALLOCATION'
    allocated={names[i]:allocation.get(i,0.) for i in selected}
    return SAVAResult(mode,tuple(names[i] for i in selected),allocated,expected,naive,max(0.,naive-expected),'SHARED_CAPACITY_VERIFICATION_ALLOCATED_WITHOUT_ADDITIVE_DOUBLE_COUNT')
