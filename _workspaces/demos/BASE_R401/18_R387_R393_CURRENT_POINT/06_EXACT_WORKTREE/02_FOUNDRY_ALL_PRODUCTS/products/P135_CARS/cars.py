from dataclasses import asdict, dataclass
from .parents.tsrc import TargetSufficientReductionCertifier, FeatureSpec
from .parents.acra import AdaptiveConsequenceResolutionAllocator, DecisionRegion, ResolutionOption

@dataclass(frozen=True)
class CARSResult:
    certificate: dict
    allocation: dict
    consequence_weights: dict[str,float]
    status: str
    def to_dict(self): return asdict(self)

def allocate_certificate_aware_resolution(features, *, protected_margin, options, budget, reserve=0.0):
    certifier=TargetSufficientReductionCertifier(features)
    cert=certifier.optimize(protected_margin, reserve)
    deleted=set(cert.deleted_features)
    weights={f.name:(0.0 if f.name in deleted else max(f.target_error_bound,1e-12)) for f in features}
    regions=[DecisionRegion(f.name,1.0,0.0,weights[f.name]) for f in features]
    alloc=AdaptiveConsequenceResolutionAllocator(regions, options).allocate(budget)
    return CARSResult(cert.as_dict(), alloc, weights, 'CERTIFICATE_AWARE_RESOLUTION_ALLOCATED')
