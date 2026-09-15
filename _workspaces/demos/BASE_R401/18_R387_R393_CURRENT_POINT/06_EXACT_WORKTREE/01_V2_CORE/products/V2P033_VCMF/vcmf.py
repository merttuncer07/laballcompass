from __future__ import annotations
from dataclasses import dataclass,asdict
@dataclass(frozen=True)
class Result:
    fine_count:int; cheap_count:int; cost:float; estimator_variance:float; worst_case_bias:float; unconstrained_choice:tuple[int,int]; unconstrained_worst_case_bias:float; status:str
    def to_dict(self): return asdict(self)

def _score(nf,nc,vf,vc,bias):
    n=nf+nc
    if n==0:return float('inf'),float('inf')
    var=(nf*vf+nc*vc)/(n*n); b=(nc/n)*bias
    return var+b*b,b

def viability_constrained_multifidelity(*,budget,fine_cost,cheap_cost,fine_variance,cheap_variance,cheap_bias_bound,viability_margin,min_fine=0):
    vals=[budget,fine_cost,cheap_cost,fine_variance,cheap_variance,cheap_bias_bound,viability_margin]
    if any(x<0 for x in vals) or fine_cost<=0 or cheap_cost<=0: raise ValueError('nonnegative parameters and positive costs required')
    maxf=int(budget//fine_cost); maxc=int(budget//cheap_cost)
    allrows=[]; safe=[]
    for nf in range(maxf+1):
      for nc in range(maxc+1):
       if nf+nc==0 or nf*fine_cost+nc*cheap_cost>budget+1e-12: continue
       mse,bias=_score(nf,nc,fine_variance,cheap_variance,cheap_bias_bound)
       n=nf+nc; variance=(nf*fine_variance+nc*cheap_variance)/(n*n)
       # Mechanism-removing comparator sees only variance/cost and ignores the
       # bounded cheap-channel bias that matters to viability.
       allrows.append((variance,nf*fine_cost+nc*cheap_cost,-n,nf,nc,bias))
       if nf>=min_fine and bias<=viability_margin+1e-12:
           safe.append((mse,nf*fine_cost+nc*cheap_cost,-n,nf,nc,bias))
    if not allrows: raise ValueError('budget cannot buy any measurement')
    u=min(allrows); uncon=(u[3],u[4])
    if not safe:return Result(0,0,0,float('inf'),float('inf'),uncon,float(u[5]),'NO_VIABILITY_SAFE_MULTIFIDELITY_PLAN')
    b=min(safe); return Result(b[3],b[4],float(b[1]),float(b[0]-b[5]*b[5]),float(b[5]),uncon,float(u[5]),'VIABILITY_CONSTRAINED_MULTIFIDELITY_PLAN')
