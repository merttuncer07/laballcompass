from dataclasses import asdict, dataclass
import numpy as np
from .parents.lcm import LiquidityConversionMap
from .parents.ric import certify_total_unimodularity

@dataclass(frozen=True)
class DLICResult:
    lcm_result: dict
    constraint_matrix: tuple[tuple[float,...],...]
    tu_certificate: dict
    integer_rhs: bool
    discrete_unit_interpretation_certified: bool
    status: str
    def to_dict(self): return asdict(self)

def audit_liquidity_integrality(claims,channels,*,horizon_days=0,max_dimension=10):
    lcm=LiquidityConversionMap(claims,channels)
    solved=lcm.solve(horizon_days)
    pairs=[(i,j) for i,c in enumerate(claims) for j,ch in enumerate(channels) if lcm._eligible(c,ch,horizon_days)]
    if not pairs:
        return DLICResult(solved,tuple(),{},False,False,'NO_ELIGIBLE_ALLOCATION_GRAPH')
    rows=[]; rhs=[]
    for i,c in enumerate(claims):
        rows.append([1.0 if ii==i else 0.0 for ii,jj in pairs]); rhs.append(c.face_value)
    for j,ch in enumerate(channels):
        rows.append([ch.advance_rate if jj==j else 0.0 for ii,jj in pairs]); rhs.append(ch.liquidity_capacity)
    anchors=sorted({c.anchor for c in claims})
    for j,ch in enumerate(channels):
        for a in anchors:
            rows.append([ch.advance_rate if jj==j and claims[ii].anchor==a else 0.0 for ii,jj in pairs]); rhs.append(ch.liquidity_capacity*ch.max_anchor_fraction)
    A=np.asarray(rows,float); integer_rhs=bool(np.max(np.abs(np.asarray(rhs)-np.rint(rhs)))<=1e-10)
    cert=certify_total_unimodularity(A,integer_rhs=integer_rhs,max_dimension=max_dimension)
    discrete=bool(cert.is_totally_unimodular and cert.theorem_applies_with_integer_rhs)
    status='DISCRETE_LIQUIDITY_UNITS_CERTIFIED' if discrete else 'CONTINUOUS_ALLOCATION_ONLY_NO_DISCRETE_CERTIFICATE'
    return DLICResult(solved,tuple(tuple(map(float,r)) for r in A),asdict(cert),integer_rhs,discrete,status)
