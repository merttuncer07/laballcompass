from __future__ import annotations
from itertools import product
import numpy as np

def support_covariance_coupled_allocation(regions, options, covariance, *, budget, coupling_penalty=1.0):
    """CATF-style allocation with a covariance-coupled exposure penalty.

    `covariance` is the upstream SACPS-style supported covariance over regions.
    Each option declares `support_exposure`, the amount of shared estimation/model risk
    carried by assigning that option to a region. Off-diagonal covariance makes choices
    interact, so this cannot be reduced to independent per-region weights.
    """
    C=np.asarray(covariance,float)
    n=len(regions)
    if C.shape!=(n,n) or not np.allclose(C,C.T) or np.min(np.linalg.eigvalsh(C)) < -1e-10:
        raise ValueError('covariance must be symmetric positive semidefinite and match regions')
    if budget < 0 or coupling_penalty < 0: raise ValueError('nonnegative budget/penalty required')
    def local_loss(r,o):
        return float(r['time_weight'])*float(o['time_spread'])+float(r['frequency_weight'])*float(o['frequency_spread'])
    feasible=[]
    for choice in product(options, repeat=n):
        cost=sum(float(o['cost']) for o in choice)
        if cost>budget: continue
        local=sum(local_loss(r,o) for r,o in zip(regions,choice))
        x=np.array([float(o.get('support_exposure',0.0)) for o in choice])
        off=C-np.diag(np.diag(C))
        coupling=float(coupling_penalty*x@np.abs(off)@x/2.0)
        feasible.append((local+coupling,local,coupling,cost,choice))
    if not feasible: raise ValueError('no feasible allocation')
    best=min(feasible,key=lambda z:(z[0],z[3],tuple(o['name'] for o in z[4])))
    # mechanism-removing control: same declared shell, covariance coupling removed
    control=min(feasible,key=lambda z:(z[1],z[3],tuple(o['name'] for o in z[4])))
    return {
      'allocation':tuple(o['name'] for o in best[4]),'objective':best[0],'local_loss':best[1],
      'covariance_penalty':best[2],'cost':best[3],
      'control_allocation':tuple(o['name'] for o in control[4]),
      'control_realized_objective':control[1]+control[2],
      'gain_vs_removed_mechanism':(control[1]+control[2])-best[0],
      'status':'SUPPORT_COVARIANCE_COUPLED_RESOLUTION_ALLOCATED'
    }
