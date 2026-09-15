"""Reference reconstruction of V2P057 REOC.
Not canonical bytes. RECS risk weights observability geometry before sensor selection.
"""
import numpy as np
from dataclasses import dataclass
from pathlib import Path
import sys
_lab_root=next(p for p in Path(__file__).resolve().parents if (p/"lab_kernels.py").exists())
if str(_lab_root) not in sys.path:sys.path.insert(0,str(_lab_root))
from lab_kernels import ObservabilityCoveragePlannerV0

@dataclass(frozen=True)
class Selection:
    sensors:tuple[int,...]; score:float

def _check_alignment(risk,H):
    r=np.asarray(risk,float); h=np.asarray(H,float)
    if h.ndim!=2 or not h.shape[1] or not np.all(np.isfinite(h)) or r.shape!=(h.shape[1],): raise ValueError('record/state alignment required')
    if np.any(r<0) or not np.all(np.isfinite(r)): raise ValueError('risk')
    return r,h

def select(risk,H,budget:int)->Selection:
    r,h=_check_alignment(risk,H)
    if not isinstance(budget,(int,np.integer)) or not 0<=budget<=h.shape[0]: raise ValueError('budget')
    # Risk reweights state columns before the actual rank/conditioning planner.
    weighted=h*np.sqrt(r)[None,:]
    planned=ObservabilityCoveragePlannerV0.select(weighted,budget)
    idx=tuple(sorted(planned['selected_indices']))
    return Selection(idx,float(np.sum(weighted[list(idx)]**2)))

def removal_control(H,budget:int)->Selection:
    h=np.asarray(H,float); return select(np.ones(h.shape[1]),h,budget)
def actual_task_score(selection:Selection,H,truth_importance)->float:
    h=np.asarray(H,float); t=np.asarray(truth_importance,float)
    return float(np.sum((h[list(selection.sensors)]**2)*t[None,:]))
