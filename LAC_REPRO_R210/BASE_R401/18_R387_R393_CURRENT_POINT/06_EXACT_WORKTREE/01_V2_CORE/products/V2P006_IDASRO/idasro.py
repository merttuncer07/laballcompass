from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Sequence

import numpy as np

# Reuse the exact packaged P025 consumer envelope.  The K068 neutral
# directional-robust mechanism is derived and implemented independently here;
# the monolithic LCB prototype module is intentionally not imported.
_REPO = Path(__file__).resolve().parents[3]
_P025 = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products" / "P025_IDRE"
if str(_P025) not in sys.path:
    sys.path.insert(0, str(_P025))

from idre import IdentificationRobustnessResult, identification_driven_envelope  # noqa: E402


@dataclass(frozen=True)
class DirectionalRobustDecision:
    nominal_decision: tuple[float, ...]
    robust_decision: tuple[float, ...] | None
    normalized_shift_direction: tuple[float, ...] | None
    persistence_radius: float
    mean_space_radius: float | None
    nominal_worst_case_objective: float | None
    robust_worst_case_objective: float | None
    worst_case_objective_gain: float | None
    sensitivity_provenance: str | None
    sensitivity_shell_certified: bool
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class IDASROResult:
    identification_envelope: IdentificationRobustnessResult
    decision: DirectionalRobustDecision
    status: str

    def to_dict(self) -> dict:
        return {
            "identification_envelope": self.identification_envelope.to_dict(),
            "decision": self.decision.to_dict(),
            "status": self.status,
        }


def _worst_case_objective(mu: np.ndarray, w: np.ndarray, direction: np.ndarray, radius: float) -> float:
    """Worst objective over mu + delta*direction, |delta| <= radius."""
    return float(mu @ w - 0.5 * (w @ w) - float(radius) * abs(float(direction @ w)))


def _solve_directional_quadratic(mu: np.ndarray, direction: np.ndarray, radius: float) -> np.ndarray:
    """Exact optimizer of mu'w - .5||w||^2 - radius*|direction'w|.

    For a unit direction v, the orthogonal part is unchanged.  The scalar
    parallel coefficient is soft-thresholded by radius.  This is the exact
    K068 primitive for the declared one-dimensional shift shell, not a copy of
    the historical numerical optimizer.
    """
    parallel = float(direction @ mu)
    orthogonal = mu - parallel * direction
    shrunk = float(np.sign(parallel) * max(abs(parallel) - float(radius), 0.0))
    return orthogonal + shrunk * direction


def identification_admissible_shift_robust_decision(
    persistence: float,
    persistence_se: float,
    *,
    horizon: float,
    disturbance_bound: float,
    decision_gap: float,
    mean_vector_at_estimate: Sequence[float],
    mean_sensitivity_to_persistence: Sequence[float],
    z_score: float = 1.96,
    sensitivity_shell_certified: bool = False,
    sensitivity_provenance: str | None = None,
) -> IDASROResult:
    """Map P025 scalar identification uncertainty into K068's admissible direction.

    Required bridge contract
    ------------------------
    The caller must certify a local affine downstream map

        mu(a) = mu(a_hat) + s * (a - a_hat)

    over the declared identification interval.  Only under that contract does
    |a-a_hat| <= z*SE imply the exact one-dimensional mean uncertainty set
    direction=s/||s|| and radius=z*SE*||s||.

    If the affine sensitivity shell is not certified, P025 is still evaluated
    but no robust decision is emitted.  This fail-closed behavior prevents a
    persistence standard error from being silently reinterpreted as a generic
    vector uncertainty radius.
    """
    if not np.isfinite(float(z_score)) or float(z_score) < 0:
        raise ValueError("z_score must be finite and nonnegative")
    mu = np.asarray(mean_vector_at_estimate, dtype=float)
    sensitivity = np.asarray(mean_sensitivity_to_persistence, dtype=float)
    if mu.ndim != 1 or sensitivity.ndim != 1 or mu.shape != sensitivity.shape or mu.size < 1:
        raise ValueError("mean vector and persistence sensitivity must be matching nonempty vectors")
    if not np.all(np.isfinite(mu)) or not np.all(np.isfinite(sensitivity)):
        raise ValueError("mean vector and sensitivity must be finite")

    envelope = identification_driven_envelope(
        persistence,
        persistence_se,
        horizon=horizon,
        disturbance_bound=disturbance_bound,
        decision_gap=decision_gap,
        z_score=z_score,
    )
    persistence_radius = float(z_score) * float(persistence_se)

    if not sensitivity_shell_certified:
        return IDASROResult(
            identification_envelope=envelope,
            decision=DirectionalRobustDecision(
                nominal_decision=tuple(map(float, mu)),
                robust_decision=None,
                normalized_shift_direction=None,
                persistence_radius=persistence_radius,
                mean_space_radius=None,
                nominal_worst_case_objective=None,
                robust_worst_case_objective=None,
                worst_case_objective_gain=None,
                sensitivity_provenance=sensitivity_provenance,
                sensitivity_shell_certified=False,
                status="AFFINE_SENSITIVITY_SHELL_NOT_CERTIFIED_NO_ROBUST_ACTION",
            ),
            status="IDENTIFICATION_ENVELOPE_ONLY_BRIDGE_REFUSED",
        )
    if not sensitivity_provenance or not str(sensitivity_provenance).strip():
        raise ValueError("certified sensitivity shell requires nonempty provenance")

    norm = float(np.linalg.norm(sensitivity))
    if norm <= 1e-15:
        # A certified exact zero sensitivity means the identified scalar cannot
        # move this downstream mean inside the declared shell.  The robust and
        # nominal decisions coincide; no arbitrary direction is invented.
        nominal_objective = float(0.5 * (mu @ mu))
        decision = DirectionalRobustDecision(
            nominal_decision=tuple(map(float, mu)),
            robust_decision=tuple(map(float, mu)),
            normalized_shift_direction=None,
            persistence_radius=persistence_radius,
            mean_space_radius=0.0,
            nominal_worst_case_objective=nominal_objective,
            robust_worst_case_objective=nominal_objective,
            worst_case_objective_gain=0.0,
            sensitivity_provenance=str(sensitivity_provenance),
            sensitivity_shell_certified=True,
            status="CERTIFIED_ZERO_DECISION_SENSITIVITY_NOMINAL_ACTION_EXACT",
        )
        return IDASROResult(envelope, decision, "IDENTIFICATION_UNCERTAINTY_ROUTED_TO_DECLARED_SHIFT_SHELL")

    direction = sensitivity / norm
    mean_radius = persistence_radius * norm
    robust = _solve_directional_quadratic(mu, direction, mean_radius)
    nominal = mu.copy()  # unconstrained nominal optimum of mu'w - .5||w||^2
    nominal_wc = _worst_case_objective(mu, nominal, direction, mean_radius)
    robust_wc = _worst_case_objective(mu, robust, direction, mean_radius)
    gain = robust_wc - nominal_wc
    # Closed-form optimum cannot be worse except floating-point epsilon.
    if gain < -1e-10:
        raise RuntimeError("directional robust closed-form solution violated its own objective contract")

    decision = DirectionalRobustDecision(
        nominal_decision=tuple(map(float, nominal)),
        robust_decision=tuple(map(float, robust)),
        normalized_shift_direction=tuple(map(float, direction)),
        persistence_radius=persistence_radius,
        mean_space_radius=float(mean_radius),
        nominal_worst_case_objective=nominal_wc,
        robust_worst_case_objective=robust_wc,
        worst_case_objective_gain=float(gain),
        sensitivity_provenance=str(sensitivity_provenance),
        sensitivity_shell_certified=True,
        status="DIRECTIONAL_ROBUST_ACTION_CERTIFIED_FOR_DECLARED_AFFINE_SHIFT_SHELL",
    )
    return IDASROResult(envelope, decision, "IDENTIFICATION_UNCERTAINTY_ROUTED_TO_DECLARED_SHIFT_SHELL")
