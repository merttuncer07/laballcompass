"""Normal evidence with an explicit joint covariance; no covariance inference.

The conditional history likelihood is tempered after conditioning on the
current estimate. This leaves current information counted once even when its
sampling error is correlated with history. Full powers and an inactive cap
reduce to ordinary generalized least squares (GLS).
"""
from dataclasses import asdict, dataclass
import math
import numpy as np


def _covariance(value, size, positive_definite=False):
    matrix = np.asarray(value, dtype=float)
    if matrix.shape != (size,size) or not np.all(np.isfinite(matrix)):
        raise ValueError('Covariance must be a finite square matrix aligned with the named observations')
    diagonal = np.diag(matrix)
    if np.any(diagonal <= 0):
        raise ValueError('Covariance diagonal must be positive')
    scale = np.sqrt(diagonal)
    corr = matrix / scale[:,None] / scale[None,:]
    if not np.allclose(corr,corr.T,rtol=1e-10,atol=1e-12):
        raise ValueError('Covariance must be symmetric')
    eig = np.linalg.eigvalsh((corr+corr.T)/2)
    if eig[0] < -1e-10:
        raise ValueError('Covariance is not positive semidefinite; it was not repaired automatically')
    if positive_definite and eig[0] <= 1e-10:
        raise ValueError('Singular or ill-conditioned covariance after declared aliases are removed; supply an independent observation basis')
    return (matrix+matrix.T)/2


def source_covariance(loadings, covariance):
    """Propagate caller-supplied linear source loadings: A Sigma A.T.

    This is exact for linear errors, or a delta-method approximation if the
    caller supplies local derivatives. Source identities and error covariance
    are given, not inferred from a matching workbook value.
    """
    a = np.asarray(loadings,dtype=float)
    if a.ndim != 2 or min(a.shape)<1 or max(a.shape)>2000 or not np.all(np.isfinite(a)):
        raise ValueError('Loadings must be a finite nonempty matrix with at most 2000 rows/columns')
    sigma = _covariance(covariance,a.shape[1])
    return a@sigma@a.T


@dataclass(frozen=True)
class CorrelatedBorrowingResult:
    current_estimate: float
    current_standard_error: float
    posterior_estimate: float
    posterior_standard_error: float
    confidence_low: float
    confidence_high: float
    current_precision: float
    borrowed_precision: float
    borrowing_precision_ratio: float
    cap_scale: float
    current_information_share: float
    retained_names: tuple[str,...]
    linear_weights: tuple[float,...]
    conditional_powers: tuple[float,...]
    alias_mapping: tuple[tuple[str,str],...]
    conflict_z: tuple[float,...]
    interval_semantics: str = 'Conditional normal model interval with powers held fixed; adaptive weighting and estimated covariance are not calibrated confidence or a full Bayesian posterior'
    dependency_model: str = 'Caller-supplied joint sampling covariance; all estimates must concern the same scalar quantity. Distinct names do not establish independence. Weights can be negative.'

    def to_dict(self):
        return asdict(self)


def borrow_correlated_evidence(current_estimate, current_standard_error, historical, *,
                              covariance, covariance_names, current_name='current',
                              compatibility_scale=1.5, borrowing_cap_ratio=2.0,
                              confidence_z=1.96, current_observation_id=None,
                              adaptive=True):
    # Import here so the existing EBC module can expose this method too.
    if __package__:
        from .ebc import coalesce_history
    else:
        from ebc import coalesce_history
    records=tuple(historical)
    numbers=[current_estimate,current_standard_error,compatibility_scale,borrowing_cap_ratio,confidence_z]
    if not all(math.isfinite(v) for v in numbers) or min(current_standard_error,compatibility_scale,confidence_z)<=0 or borrowing_cap_ratio<0:
        raise ValueError('Finite inputs, positive SE/scale/z, and a nonnegative borrowing cap are required')
    if type(adaptive) is not bool:
        raise ValueError('adaptive must be a boolean')
    if not isinstance(current_name,str) or not current_name or current_name in {r.name for r in records}:
        raise ValueError('Current name must be nonempty and distinct from historical names')
    if current_observation_id is not None and (not isinstance(current_observation_id,str) or not current_observation_id.strip()):
        raise ValueError('current_observation_id must be a nonempty string or None')
    unique,aliases=coalesce_history(records)
    names=[current_name]+[r.name for r in records]
    if len(names)>501:
        raise ValueError('Joint covariance limit: current plus 500 historical records')
    if covariance_names is None or list(covariance_names)!=names:
        raise ValueError('covariance_names must exactly match current name followed by historical input names in order')
    joint=_covariance(covariance,len(names))
    se=np.array([current_standard_error]+[r.standard_error for r in records])
    if not np.allclose(np.diag(joint)/(se*se),1,rtol=1e-8,atol=1e-10):
        raise ValueError('Covariance diagonal does not match declared standard errors')
    positions={name:i for i,name in enumerate(names)}
    for record in records:
        if current_observation_id is not None and record.observation_id==current_observation_id:
            if (record.estimate,record.standard_error)!=(current_estimate,current_standard_error):
                raise ValueError('Current observation identity conflicts with historical estimate/SE')
            aliases[record.name]=current_name
        i=positions[record.name];j=positions[aliases[record.name]]
        if i!=j and not np.allclose((joint[i]-joint[j])/(se[i]*se),0,rtol=0,atol=1e-9):
            raise ValueError('Declared aliases require identical covariance rows')
    retained=[r for r in unique if aliases[r.name]!=current_name and r.maximum_power>0]
    idx=[0]+[positions[r.name] for r in retained]
    reduced=joint[np.ix_(idx,idx)]
    _covariance(reduced,len(idx),positive_definite=True)
    variance=current_standard_error**2
    powers=[];conflicts=[]
    for i,record in enumerate(retained,1):
        difference_variance=variance+reduced[i,i]-2*reduced[i,0]
        z=abs(record.estimate-current_estimate)/math.sqrt(difference_variance)
        conflicts.append(z)
        factor=math.exp(-.5*(z/compatibility_scale)**2) if adaptive else 1.
        powers.append(record.maximum_power*factor)
    powers=np.asarray(powers)
    # Zero-powered rows contain no conditional likelihood, even if correlated.
    active=np.flatnonzero(powers>0)
    retained=[retained[i] for i in active]
    conflicts=[conflicts[i] for i in active]
    powers=powers[active]
    indices=np.r_[0,active+1]
    reduced=reduced[np.ix_(indices,indices)]
    current_precision=1/variance
    if retained:
        gamma=reduced[1:,0]/variance
        conditional=reduced[1:,1:]-np.outer(reduced[1:,0],reduced[0,1:])/variance
        _covariance(conditional,len(retained),positive_definite=True)
        a=1-gamma
        # P = sqrt(D) inv(S) sqrt(D), without explicitly inverting S.
        root_power=np.sqrt(powers)
        precision_a=root_power*np.linalg.solve(conditional,root_power*a)
        information=float(a@precision_a)
        if information<0 or not math.isfinite(information):
            raise ValueError('Conditional information is numerically invalid')
        cap_scale=min(1.,borrowing_cap_ratio*current_precision/information) if information else 1.
        history_weights=cap_scale*precision_a
        current_weight=current_precision-float(history_weights@gamma)
        borrowed=cap_scale*information
    else:
        history_weights=np.array([]);current_weight=current_precision;borrowed=0.;cap_scale=1.
    total=current_precision+borrowed
    weights=np.r_[current_weight,history_weights]/total
    values=np.array([current_estimate]+[r.estimate for r in retained])
    estimate=float(weights@values);posterior_se=math.sqrt(1/total)
    return CorrelatedBorrowingResult(
        current_estimate,current_standard_error,estimate,posterior_se,
        estimate-confidence_z*posterior_se,estimate+confidence_z*posterior_se,
        current_precision,borrowed,borrowed/current_precision,cap_scale,current_precision/total,
        tuple([current_name]+[r.name for r in retained]),tuple(float(w) for w in weights),
        tuple(float(p) for p in powers),tuple(sorted(aliases.items())),tuple(conflicts))
