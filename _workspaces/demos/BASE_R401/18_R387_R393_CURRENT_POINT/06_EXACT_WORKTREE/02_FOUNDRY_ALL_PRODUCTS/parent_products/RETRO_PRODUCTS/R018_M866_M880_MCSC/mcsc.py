"""Monotone Comparative-Statics Certifier (MCSC) v0.1."""

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Sequence
import numpy as np

@dataclass(frozen=True)
class DifferenceWitness:
    low_action: float; high_action: float; low_parameter: float; high_parameter: float
    low_parameter_advantage: float; high_parameter_advantage: float; difference_change: float

@dataclass(frozen=True)
class ComparativeStaticsCertificate:
    action_count:int; parameter_count:int; increasing_differences:bool; decreasing_differences:bool
    maximum_increasing_differences_violation:float; maximum_decreasing_differences_violation:float
    increasing_violation_witness:DifferenceWitness|None; decreasing_violation_witness:DifferenceWitness|None
    optimal_action_sets:tuple[tuple[float,...],...]; least_optimal_selection:tuple[float,...]
    greatest_optimal_selection:tuple[float,...]; least_selection_nondecreasing:bool
    greatest_selection_nondecreasing:bool; certified_direction:str; status:str
    def to_dict(self):
        d=asdict(self); d["increasing_violation_witness"]=None if self.increasing_violation_witness is None else asdict(self.increasing_violation_witness); d["decreasing_violation_witness"]=None if self.decreasing_violation_witness is None else asdict(self.decreasing_violation_witness); return d

def certify_monotone_comparative_statics(actions:Sequence[float],parameters:Sequence[float],payoffs:Sequence[Sequence[float]],*,tolerance:float=1e-10)->ComparativeStaticsCertificate:
    a=np.asarray(actions,float); t=np.asarray(parameters,float); u=np.asarray(payoffs,float)
    if a.ndim!=1 or t.ndim!=1 or a.size<2 or t.size<2 or np.any(np.diff(a)<=0) or np.any(np.diff(t)<=0): raise ValueError("actions and parameters must be strictly increasing vectors")
    if u.shape!=(a.size,t.size) or not np.all(np.isfinite(u)) or tolerance<0: raise ValueError("payoffs must have action-by-parameter shape and finite values")
    min_change=float("inf"); max_change=float("-inf"); min_w=max_w=None
    for lo in range(a.size-1):
      for hi in range(lo+1,a.size):
       for tl in range(t.size-1):
        for th in range(tl+1,t.size):
         low=float(u[hi,tl]-u[lo,tl]); high=float(u[hi,th]-u[lo,th]); change=high-low
         w=DifferenceWitness(float(a[lo]),float(a[hi]),float(t[tl]),float(t[th]),low,high,float(change))
         if change<min_change: min_change=change; min_w=w
         if change>max_change: max_change=change; max_w=w
    inc=min_change>=-tolerance; dec=max_change<=tolerance
    sets=[]
    for j in range(t.size):
        best=np.max(u[:,j]); sets.append(tuple(map(float,a[np.isclose(u[:,j],best,atol=tolerance,rtol=0)])))
    least=tuple(x[0] for x in sets); greatest=tuple(x[-1] for x in sets)
    least_up=bool(np.all(np.diff(least)>=-tolerance)); greatest_up=bool(np.all(np.diff(greatest)>=-tolerance))
    if inc and not dec: direction="NONDECREASING"
    elif dec and not inc: direction="NONINCREASING"
    elif inc and dec: direction="PARAMETER_INDEPENDENT_DIFFERENCES"
    else: direction="NO_GLOBAL_MONOTONE_DIRECTION_CERTIFIED"
    return ComparativeStaticsCertificate(a.size,t.size,inc,dec,max(0.0,-min_change),max(0.0,max_change),
      None if inc else min_w,None if dec else max_w,tuple(sets),least,greatest,least_up,greatest_up,direction,
      "STRUCTURAL_DIRECTION_CERTIFIED" if inc or dec else "STRUCTURAL_CERTIFICATE_FAILED_WITH_WITNESS")
