"""Reference reconstruction of V2P058 SACATRC.
Not canonical bytes. ATRC defines a target-loss-safe deletion set; SACPS redundancy only chooses within that safe set.
"""
import numpy as np
from dataclasses import dataclass

@dataclass(frozen=True)
class Eviction:
    index:int; safe_set:tuple[int,...]; redundancy:tuple[float,...]

def choose_eviction(deletion_losses, fingerprints, support_mask, tolerance:float)->Eviction:
    losses=np.asarray(deletion_losses,float); fp=np.asarray(fingerprints,float); mask=np.asarray(support_mask,float)
    if losses.ndim!=1 or not losses.size or not np.all(np.isfinite(losses)) or fp.ndim!=2 or not fp.shape[1] or not np.all(np.isfinite(fp)) or len(losses)!=fp.shape[0]: raise ValueError('item/fingerprint alignment')
    if mask.shape!=(fp.shape[1],fp.shape[1]): raise ValueError('support alignment')
    if not np.all(np.isin(mask,[0,1])) or not np.array_equal(mask,mask.T) or not np.all(np.diag(mask)): raise ValueError('support must be symmetric binary with diagonal')
    if not np.isfinite(tolerance) or tolerance<0: raise ValueError('tolerance')
    best=float(np.min(losses)); safe=tuple(int(i) for i,x in enumerate(losses) if x<=best+tolerance+1e-12)
    if not safe: raise RuntimeError('no ATRC-safe eviction')
    if tolerance==0 or np.allclose(mask,np.eye(mask.shape[0])):
        # exact ATRC collapse: deterministic minimum deletion loss
        i=min(safe,key=lambda j:(losses[j],j)); return Eviction(i,safe,tuple(0.0 for _ in safe))
    sub=fp[list(safe)]
    cov=np.atleast_2d(np.cov(sub,rowvar=False,bias=False)) if len(safe)>1 else np.zeros((fp.shape[1],fp.shape[1]))
    cov=cov*mask
    # redundancy of an item = absolute covariance-weighted similarity to other safe fingerprints
    red=[]
    for a,i in enumerate(safe):
        s=0.0
        for b,j in enumerate(safe):
            if i==j: continue
            s+=abs(float(sub[a]@cov@sub[b]))
        red.append(s)
    # safe-set authority remains primary; SACPS only breaks within it
    k=max(range(len(safe)),key=lambda a:(red[a],-losses[safe[a]],-safe[a]))
    return Eviction(safe[k],safe,tuple(float(x) for x in red))
