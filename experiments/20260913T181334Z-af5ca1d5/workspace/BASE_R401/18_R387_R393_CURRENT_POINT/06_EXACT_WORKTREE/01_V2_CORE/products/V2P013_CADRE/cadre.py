from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
from typing import Sequence, Mapping
_REPO=Path(__file__).resolve().parents[3]
_PARENT=_REPO/'02_FOUNDRY_ALL_PRODUCTS'/'parent_products'/'CURRENT_PRODUCTS'/'IM334_IM094_DRE'
if str(_PARENT) not in sys.path: sys.path.insert(0,str(_PARENT))
from dre import GaussianArm, DecisionRelevantExplorer

@dataclass(frozen=True)
class CADREResult:
    compressed_choice:str
    compressed_score_margin:float
    compression_decision_bound:float
    compression_certified:bool
    final_choice:str|None
    used_full_resolution:bool
    status:str
    def to_dict(self): return asdict(self)

def compression_aware_dre(*, compressed_arms:Sequence[GaussianArm], compression_error_bounds:Mapping[str,float], remaining_decisions:int, full_resolution_arms:Sequence[GaussianArm]|None=None)->CADREResult:
    if len(compressed_arms)<2: raise ValueError('at least two compressed arms required')
    if set(a.name for a in compressed_arms)!=set(compression_error_bounds): raise ValueError('compression bound names must match arms')
    if any(float(v)<0 for v in compression_error_bounds.values()): raise ValueError('compression bounds must be nonnegative')
    explorer=DecisionRelevantExplorer(); scores=explorer.score(compressed_arms,remaining_decisions)
    margin=float(scores[0].total_score-scores[1].total_score)
    bound=float(compression_error_bounds[scores[0].arm])+float(compression_error_bounds[scores[1].arm])
    if margin>bound:
        return CADREResult(scores[0].arm,margin,bound,True,scores[0].arm,False,'COMPRESSED_DRE_DECISION_CERTIFIED')
    if full_resolution_arms is None:
        return CADREResult(scores[0].arm,margin,bound,False,None,False,'COMPRESSION_TIPPING_REQUIRES_DECOMPRESSION_OR_ABSTENTION')
    if set(a.name for a in full_resolution_arms)!=set(a.name for a in compressed_arms): raise ValueError('full-resolution arms must match names')
    full_choice=explorer.choose(full_resolution_arms,remaining_decisions)
    return CADREResult(scores[0].arm,margin,bound,False,full_choice,True,'COMPRESSION_TIPPING_TRIGGERED_FULL_RESOLUTION_DRE')
