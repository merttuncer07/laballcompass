from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp


@dataclass(frozen=True)
class IdentificationRobustnessResult:
    persistence: float
    persistence_se: float
    nominal_flip_index: float
    conservative_flip_index: float
    nominal_certified: bool
    conservative_certified: bool
    status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _finite_horizon_gain(rate: float, horizon: float) -> float:
    if abs(rate) < 1e-12:
        return horizon
    return (exp(rate * horizon) - 1.0) / rate


def identification_driven_envelope(
    persistence: float,
    persistence_se: float,
    *,
    horizon: float,
    disturbance_bound: float,
    decision_gap: float,
    z_score: float = 1.96,
) -> IdentificationRobustnessResult:
    """Carry identification uncertainty into a same-input decision envelope."""
    if persistence_se < 0 or horizon <= 0 or disturbance_bound < 0 or decision_gap <= 0:
        raise ValueError("invalid uncertainty/envelope inputs")
    nominal = disturbance_bound * _finite_horizon_gain(persistence, horizon) / decision_gap
    conservative_rate = persistence + z_score * persistence_se
    conservative = disturbance_bound * _finite_horizon_gain(conservative_rate, horizon) / decision_gap
    nominal_ok = nominal < 1.0
    conservative_ok = conservative < 1.0
    if nominal_ok and not conservative_ok:
        status = "IDENTIFICATION_UNCERTAINTY_REVOKES_ACTION_CERTIFICATE"
    elif conservative_ok:
        status = "ACTION_CERTIFIED_UNDER_IDENTIFICATION_UNCERTAINTY"
    else:
        status = "ACTION_FLIP_CANNOT_BE_EXCLUDED"
    return IdentificationRobustnessResult(
        persistence,
        persistence_se,
        nominal,
        conservative,
        nominal_ok,
        conservative_ok,
        status,
    )
