from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys

import numpy as np

# Reuse the exact P144 persistence estimator / decision-value controller as the
# consumer implementation.  K048's neutral budget-allocation mechanism is
# implemented below rather than importing the monolithic prototype library.
_REPO = Path(__file__).resolve().parents[3]
_FOUNDRY_PRODUCTS = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products"
if str(_FOUNDRY_PRODUCTS) not in sys.path:
    sys.path.insert(0, str(_FOUNDRY_PRODUCTS))

from P144_DPAI.parents.dfdpe import estimate_affine_dynamics  # noqa: E402
from P144_DPAI.parents.aicc import AdaptiveInformationController, InformationChannel  # noqa: E402


@dataclass(frozen=True)
class FidelityIdentificationChannel:
    name: str
    noise_variance: float
    cost: float


@dataclass(frozen=True)
class MFPDResult:
    persistence_estimate: float
    persistence_standard_error: float
    validation_rollout_rmse: float | None
    current_action: str
    acquisition_family: str | None
    fine_net_value: float
    cheap_net_value: float
    mode: str
    n_fine: int
    n_cheap: int
    spent_budget: float
    variance_proxy: float | None
    status: str

    def to_dict(self):
        return asdict(self)


def _single_measurement_value(mu: float, variance: float, *, stability_threshold: float,
                              channel: FidelityIdentificationChannel) -> float:
    """P144/AICC decision value of one declared persistence measurement."""
    ctl = AdaptiveInformationController(
        np.array([float(mu)]),
        np.array([[float(variance)]]),
        np.array([[-1.0], [1.0]]),
        np.array([float(stability_threshold), -float(stability_threshold)]),
        [InformationChannel(
            channel.name,
            np.array([1.0]),
            float(channel.noise_variance),
            float(channel.cost),
        )],
    )
    return float(ctl.rank_channels()[0].net_value)


def _multifidelity_allocation(total_budget: float, fine_cost: float, cheap_cost: float,
                              rho_hat: float, min_fine: int) -> dict:
    """Neutral K048 mechanism: minimize the declared variance proxy under budget.

    Fine-only is the baseline.  A correlated cheap channel is admitted only when
    a feasible mixed allocation lowers the proxy.  Unlike the old monolithic
    prototype's fine-only metadata, n_cheap is explicitly zero when no cheap
    measurements are allocated.
    """
    budget = float(total_budget)
    cf = float(fine_cost)
    cc = float(cheap_cost)
    if budget < 0 or cf <= 0 or cc <= 0 or int(min_fine) < 1:
        raise ValueError("invalid budget/channel contract")
    max_fine = int(budget // cf)
    if max_fine < 1:
        return {"mode": "none", "n_fine": 0, "n_cheap": 0, "variance_proxy": None}

    rho = min(abs(float(rho_hat)), 0.999)
    best = {
        "mode": "fine_only",
        "n_fine": max_fine,
        "n_cheap": 0,
        "variance_proxy": 1.0 / max_fine,
    }
    if max_fine < int(min_fine):
        return best

    for n_fine in range(int(min_fine), max_fine + 1):
        n_cheap = int((budget - cf * n_fine) // cc)
        if n_cheap < n_fine:
            continue
        proxy = (1.0 - rho * rho) / n_fine + (rho * rho) / n_cheap
        if proxy < best["variance_proxy"]:
            best = {
                "mode": "multifidelity",
                "n_fine": n_fine,
                "n_cheap": n_cheap,
                "variance_proxy": float(proxy),
            }
    return best


def identify_persistence_then_route_budget(
    times,
    outputs,
    inputs,
    *,
    window_duration: float,
    window_step: float,
    total_budget: float,
    fine_channel: FidelityIdentificationChannel,
    cheap_channel: FidelityIdentificationChannel,
    pilot_correlation: float,
    stability_threshold: float = 0.0,
    validation=None,
    min_fine: int = 4,
    min_correlation: float = 0.2,
) -> MFPDResult:
    """P144 boundary-sensitive acquisition gate followed by K048 budget routing.

    Scientific acquisition need is determined first from P144's persistence
    belief and decision boundary.  K048 is allowed to act only after at least one
    declared measurement channel has positive decision value.
    """
    if total_budget < 0 or fine_channel.cost <= 0 or cheap_channel.cost <= 0:
        raise ValueError("invalid budget/channel contract")
    if fine_channel.noise_variance <= 0 or cheap_channel.noise_variance <= 0:
        raise ValueError("noise variance must be positive")
    if min_fine < 1:
        raise ValueError("min_fine must be >= 1")

    fit_kwargs = {}
    if validation is not None:
        fit_kwargs = dict(
            validation_times=validation[0],
            validation_outputs=validation[1],
            validation_inputs=validation[2],
        )
    fit = estimate_affine_dynamics(
        times,
        outputs,
        inputs,
        window_duration=window_duration,
        window_step=window_step,
        robust=True,
        **fit_kwargs,
    )
    if fit.estimate is None:
        raise RuntimeError("DFDPE did not produce an identified persistence parameter")

    est = fit.estimate
    mu = float(est.persistence)
    se = float(est.standard_errors[0])
    var = se * se
    current_action = "STABLE_SIDE" if mu <= float(stability_threshold) else "UNSTABLE_SIDE"

    fine_net = _single_measurement_value(
        mu, var, stability_threshold=stability_threshold, channel=fine_channel
    )
    cheap_net = _single_measurement_value(
        mu, var, stability_threshold=stability_threshold, channel=cheap_channel
    )

    cheapest = min(float(fine_channel.cost), float(cheap_channel.cost))
    if max(fine_net, cheap_net) <= 0 or total_budget < cheapest:
        return MFPDResult(
            mu, se, est.validation_rollout_rmse, current_action, None,
            fine_net, cheap_net, "no_measurement", 0, 0, 0.0, None,
            "PERSISTENCE_DECISION_VALUE_DOES_NOT_JUSTIFY_ACQUISITION",
        )

    # If only the cheap channel has positive decision value, there is no reason
    # to force fine measurements merely to satisfy a multi-fidelity template.
    if fine_net <= 0 < cheap_net:
        n_cheap = int(float(total_budget) // float(cheap_channel.cost))
        return MFPDResult(
            mu, se, est.validation_rollout_rmse, current_action, "identification_experiment",
            fine_net, cheap_net, "cheap_only", 0, n_cheap,
            n_cheap * float(cheap_channel.cost), 1.0 / max(n_cheap, 1),
            "PERSISTENCE_CHEAP_ONLY_CHANNEL_HAS_POSITIVE_DECISION_VALUE",
        )

    baseline_n_fine = int(float(total_budget) // float(fine_channel.cost))
    proposal = _multifidelity_allocation(
        total_budget, fine_channel.cost, cheap_channel.cost, pilot_correlation, min_fine
    )
    allow_multi = (
        cheap_net > 0
        and abs(float(pilot_correlation)) >= float(min_correlation)
        and proposal["mode"] == "multifidelity"
    )

    if allow_multi:
        mode = "multifidelity"
        n_fine = int(proposal["n_fine"])
        n_cheap = int(proposal["n_cheap"])
        proxy = float(proposal["variance_proxy"])
        status = "PERSISTENCE_DECISION_GATED_MULTIFIDELITY_PROGRAM_ALLOCATED"
    else:
        mode = "fine_only"
        n_fine = baseline_n_fine
        n_cheap = 0
        proxy = None if n_fine == 0 else 1.0 / n_fine
        status = "PERSISTENCE_FINE_ONLY_ROUTER_USED_CHEAP_CHANNEL_NOT_QUALIFIED"

    spent = n_fine * float(fine_channel.cost) + n_cheap * float(cheap_channel.cost)
    return MFPDResult(
        mu, se, est.validation_rollout_rmse, current_action, "identification_experiment",
        fine_net, cheap_net, mode, n_fine, n_cheap, spent, proxy, status,
    )
