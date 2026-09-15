"""Reference reconstruction of V2P056 SACRDSBC.
Not canonical bytes. Support-aware covariance stress modifies DSBC merge admissibility.
"""
import numpy as np
from dataclasses import dataclass

@dataclass(frozen=True)
class MergeResult:
    merge:bool; status:str; worst_distance:float

def support_covariance(errors, support_mask):
    x=np.asarray(errors,float); m=np.asarray(support_mask,float)
    if x.ndim!=2 or x.shape[0]<2 or not x.shape[1] or not np.all(np.isfinite(x)) or m.shape!=(x.shape[1],x.shape[1]): raise ValueError('alignment')
    if not np.all(np.isin(m,[0,1])) or not np.array_equal(m,m.T) or not np.all(np.diag(m)): raise ValueError('support must be symmetric binary with diagonal')
    c=np.atleast_2d(np.cov(x,rowvar=False,bias=False));supported=c*m;diagonal=np.diag(np.diag(c))
    for weight in np.linspace(0,1,101):
        candidate=(1-weight)*supported+weight*diagonal
        if np.linalg.eigvalsh(candidate).min()>=-1e-12:return candidate
    raise ValueError('no PSD covariance on declared support')

def robust_merge(b1,b2,cov,tolerance:float,stress_scale:float=1.0)->MergeResult:
    a=np.asarray(b1,float); b=np.asarray(b2,float); c=np.asarray(cov,float)
    if a.shape!=b.shape or c.shape!=(len(a),len(a)): raise ValueError('alignment')
    if not np.isfinite(tolerance) or tolerance<0 or not np.isfinite(stress_scale) or stress_scale<0: raise ValueError('tolerance/stress_scale')
    if not a.size or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or not np.all(np.isfinite(c)) or not np.allclose(c,c.T) or np.linalg.eigvalsh(c).min() < -1e-12: raise ValueError('finite beliefs and PSD covariance required')
    # conservative ellipsoidal proxy along the merge direction
    d=b-a; nominal=float(np.linalg.norm(d))
    if np.allclose(d,0):
        singleton_stress=float(stress_scale*np.sqrt(max(0.0,np.linalg.eigvalsh(c).max(initial=0.0))))
        if singleton_stress>tolerance: return MergeResult(False,'FAIL_CLOSED_SINGLETON_UNCERTIFIABLE',singleton_stress)
        return MergeResult(True,'COLLAPSE_SINGLETON',0.0)
    q=float(np.sqrt(max(0.0,d@c@d))/(np.linalg.norm(d)+1e-12))
    worst=nominal+stress_scale*q
    return MergeResult(worst<=tolerance,'MERGE' if worst<=tolerance else 'KEEP_SEPARATE',worst)

def nominal_control(b1,b2,tolerance:float)->bool:
    return float(np.linalg.norm(np.asarray(b2,float)-np.asarray(b1,float)))<=tolerance
