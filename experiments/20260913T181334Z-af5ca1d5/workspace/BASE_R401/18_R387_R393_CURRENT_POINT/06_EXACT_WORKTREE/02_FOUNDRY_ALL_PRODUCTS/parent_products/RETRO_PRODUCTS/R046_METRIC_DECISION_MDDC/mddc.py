"""Metric–Decision Divergence and Counterexample bench (MDDC) v0.1."""
from __future__ import annotations
from dataclasses import asdict,dataclass
from typing import Mapping,Sequence
import numpy as np

@dataclass(frozen=True)
class ApproximationScore:
    case:int; candidate:str; l1_distance:float; kl_divergence:float
    reference_action:int; approximate_action:int; decision_regret:float; action_inverted:bool
@dataclass(frozen=True)
class RankingInversion:
    case:int; metric_preferred_candidate:str; decision_preferred_candidate:str
    metric_distance_gap:float; decision_regret_gap:float
@dataclass(frozen=True)
class DivergenceResult:
    scores:tuple[ApproximationScore,...]; inversions:tuple[RankingInversion,...]
    cases:int; candidates:int; action_inversions:int; ranking_inversions:int
    strongest_decision_regret_gap:float; status:str
    def to_dict(self): return asdict(self)

def diagnose_metric_decision_divergence(reference_beliefs:Sequence[Sequence[float]],
    candidate_beliefs:Mapping[str,Sequence[Sequence[float]]],state_action_utilities:Sequence[Sequence[float]])->DivergenceResult:
    refs=np.asarray(reference_beliefs,float); utility=np.asarray(state_action_utilities,float)
    if refs.ndim!=2 or utility.ndim!=2 or utility.shape[0]!=refs.shape[1] or utility.shape[1]<2: raise ValueError('dimension mismatch')
    if not candidate_beliefs: raise ValueError('at least one candidate required')
    def valid(a): return a.shape==refs.shape and np.all(np.isfinite(a)) and np.all(a>=0) and np.allclose(a.sum(1),1,atol=1e-8)
    if not valid(refs): raise ValueError('references must be probability vectors')
    arrays={name:np.asarray(value,float) for name,value in candidate_beliefs.items()}
    if any(not valid(a) for a in arrays.values()): raise ValueError('candidates must match reference probability vectors')
    scores=[]
    for case,ref in enumerate(refs):
        values=ref@utility; ref_action=int(np.argmax(values)); best=float(np.max(values))
        for name in sorted(arrays):
            candidate=arrays[name][case]; action=int(np.argmax(candidate@utility))
            kl=float(np.sum(np.where(ref>0,ref*np.log(ref/np.maximum(candidate,1e-15)),0)))
            scores.append(ApproximationScore(case,name,float(np.sum(np.abs(ref-candidate))),kl,
                ref_action,action,float(best-values[action]),action!=ref_action))
    inversions=[]
    for case in range(len(refs)):
        local=[s for s in scores if s.case==case]
        for a in local:
            for b in local:
                if a.l1_distance+1e-12<b.l1_distance and a.decision_regret>b.decision_regret+1e-12:
                    inversions.append(RankingInversion(case,a.candidate,b.candidate,
                        float(b.l1_distance-a.l1_distance),float(a.decision_regret-b.decision_regret)))
    inversions.sort(key=lambda x:(-x.decision_regret_gap,-x.metric_distance_gap,x.case,x.metric_preferred_candidate))
    return DivergenceResult(tuple(scores),tuple(inversions),len(refs),len(arrays),
        sum(s.action_inverted for s in scores),len(inversions),
        max((i.decision_regret_gap for i in inversions),default=0.0),
        'METRIC_DECISION_RANKING_DIVERGENCE_FOUND' if inversions else 'NO_RANKING_DIVERGENCE_IN_SUPPLIED_CANDIDATES')
