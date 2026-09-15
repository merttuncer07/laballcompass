from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Sequence

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
_FOUNDRY_PRODUCTS = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products"
if str(_FOUNDRY_PRODUCTS) not in sys.path:
    sys.path.insert(0, str(_FOUNDRY_PRODUCTS))

from P135_CARS.cars import allocate_certificate_aware_resolution  # noqa: E402
from P135_CARS.parents.tsrc import (  # noqa: E402
    FeatureSpec,
    TargetSufficientReductionCertifier,
)
from P135_CARS.parents.acra import (  # noqa: E402
    AdaptiveConsequenceResolutionAllocator,
    DecisionRegion,
    ResolutionOption,
)


@dataclass(frozen=True)
class TransportAudit:
    accepted: bool
    residual_shift_score: float | None
    standardized_mean_shift: float | None
    log_scale_shift: float | None
    target_residual_driver_correlation: float | None
    n_source: int
    n_target: int
    threshold: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TGCARSResult:
    transport_audit: TransportAudit
    certificate: dict
    allocation: dict
    consequence_weights: dict[str, float]
    certificate_zeroing_enabled: bool
    fallback_used: bool
    status: str

    def to_dict(self) -> dict:
        return {
            "transport_audit": self.transport_audit.to_dict(),
            "certificate": self.certificate,
            "allocation": self.allocation,
            "consequence_weights": self.consequence_weights,
            "certificate_zeroing_enabled": self.certificate_zeroing_enabled,
            "fallback_used": self.fallback_used,
            "status": self.status,
        }


def audit_guarantee_transport(
    source_residuals: Sequence[float],
    target_residuals: Sequence[float],
    *,
    target_driver: Sequence[float] | None = None,
    max_transport_score: float,
    min_samples: int = 8,
    min_source_scale: float = 1e-10,
) -> TransportAudit:
    """K071-style residual/conditional-law transport audit with explicit fail-closed guards.

    The historical K071 mechanism adds three diagnostics: a source-standardized
    residual mean shift, an absolute log residual-scale ratio, and (when a
    target driver is declared) the absolute target residual/driver correlation.
    This implementation keeps that mechanism but refuses to certify transport
    when the residual shell is numerically unidentified or undersampled.
    """
    if max_transport_score < 0:
        raise ValueError("max_transport_score must be non-negative")
    if min_samples < 2:
        raise ValueError("min_samples must be at least 2")
    rs = np.asarray(source_residuals, dtype=float)
    rt = np.asarray(target_residuals, dtype=float)
    if rs.ndim != 1 or rt.ndim != 1:
        raise ValueError("residuals must be one-dimensional")
    if len(rs) < min_samples or len(rt) < min_samples:
        return TransportAudit(
            False, None, None, None, None, len(rs), len(rt), float(max_transport_score),
            "INSUFFICIENT_RESIDUAL_SUPPORT",
        )
    if not np.all(np.isfinite(rs)) or not np.all(np.isfinite(rt)):
        return TransportAudit(
            False, None, None, None, None, len(rs), len(rt), float(max_transport_score),
            "NONFINITE_RESIDUALS",
        )
    source_scale = float(np.std(rs))
    target_scale = float(np.std(rt))
    if source_scale <= min_source_scale:
        return TransportAudit(
            False, None, None, None, None, len(rs), len(rt), float(max_transport_score),
            "SOURCE_RESIDUAL_SCALE_UNIDENTIFIED",
        )

    mean_shift = abs(float(np.mean(rt) - np.mean(rs))) / source_scale
    log_scale = abs(float(np.log((target_scale + 1e-12) / (source_scale + 1e-12))))
    corr = 0.0
    if target_driver is not None:
        x = np.asarray(target_driver, dtype=float)
        if x.ndim != 1 or len(x) != len(rt):
            return TransportAudit(
                False, None, None, None, None, len(rs), len(rt), float(max_transport_score),
                "TARGET_DRIVER_SHAPE_MISMATCH",
            )
        if not np.all(np.isfinite(x)):
            return TransportAudit(
                False, None, None, None, None, len(rs), len(rt), float(max_transport_score),
                "NONFINITE_TARGET_DRIVER",
            )
        if float(np.std(x)) > 0 and target_scale > 0:
            corr = abs(float(np.corrcoef(rt, x)[0, 1]))

    score = mean_shift + log_scale + corr
    accepted = score <= float(max_transport_score)
    return TransportAudit(
        accepted=accepted,
        residual_shift_score=float(score),
        standardized_mean_shift=float(mean_shift),
        log_scale_shift=float(log_scale),
        target_residual_driver_correlation=float(corr),
        n_source=len(rs),
        n_target=len(rt),
        threshold=float(max_transport_score),
        reason="TRANSPORT_SCORE_WITHIN_DECLARED_LIMIT" if accepted else "TRANSPORT_SCORE_EXCEEDS_DECLARED_LIMIT",
    )


def _full_feature_fallback(
    features: Sequence[FeatureSpec],
    options: Sequence[ResolutionOption],
    budget: float,
) -> tuple[dict[str, float], dict]:
    # The fallback deliberately removes only P135's *zero consequence* use of
    # the deletion certificate.  It does not claim that the declared feature
    # bounds themselves have been revalidated under transport shift.
    weights = {f.name: max(float(f.target_error_bound), 1e-12) for f in features}
    regions = [DecisionRegion(f.name, 1.0, 0.0, weights[f.name]) for f in features]
    allocation = AdaptiveConsequenceResolutionAllocator(regions, options).allocate(float(budget))
    return weights, allocation


def transport_gated_certificate_aware_resolution(
    features: Sequence[FeatureSpec],
    *,
    protected_margin: float,
    options: Sequence[ResolutionOption],
    budget: float,
    source_residuals: Sequence[float],
    target_residuals: Sequence[float],
    max_transport_score: float,
    target_driver: Sequence[float] | None = None,
    reserve: float = 0.0,
    min_samples: int = 8,
) -> TGCARSResult:
    """Prevent a P135 deletion certificate from silently escaping its transport shell.

    If K071-style transport is accepted, exact P135 behavior is preserved.
    Otherwise the adapter fails closed on certificate *zeroing*: deleted
    features regain non-zero declared consequence weights before the ACRA
    allocation is solved.  This is a conservative sensing fallback, not a new
    transport certificate; re-certification remains required for the action
    guarantee itself.
    """
    features = tuple(features)
    options = tuple(options)
    if not features or not options:
        raise ValueError("features and options are required")

    # Keep the P135 deletion certificate visible in both branches so the caller
    # can see exactly which guarantee was considered for transport/reuse.
    cert = TargetSufficientReductionCertifier(features).optimize(protected_margin, reserve)
    audit = audit_guarantee_transport(
        source_residuals,
        target_residuals,
        target_driver=target_driver,
        max_transport_score=max_transport_score,
        min_samples=min_samples,
    )

    if audit.accepted:
        p135 = allocate_certificate_aware_resolution(
            features,
            protected_margin=protected_margin,
            options=options,
            budget=budget,
            reserve=reserve,
        )
        return TGCARSResult(
            transport_audit=audit,
            certificate=p135.certificate,
            allocation=p135.allocation,
            consequence_weights=p135.consequence_weights,
            certificate_zeroing_enabled=True,
            fallback_used=False,
            status="TRANSPORT_ACCEPTED_P135_CERTIFICATE_REUSE_ENABLED",
        )

    weights, allocation = _full_feature_fallback(features, options, budget)
    return TGCARSResult(
        transport_audit=audit,
        certificate=cert.as_dict(),
        allocation=allocation,
        consequence_weights=weights,
        certificate_zeroing_enabled=False,
        fallback_used=True,
        status="TRANSPORT_NOT_CERTIFIED_DELETION_ZEROING_DISABLED_REVALIDATION_REQUIRED",
    )
