"""Burnout-Aware Mortgage Intervention (BAMI) v0.1.

Directed composition:
MBPF -> time-varying performing prepayment hazard -> MCRIS-style competing risks
EBC -> conflict-controlled log default multiplier
TDSX -> net-value robustness/tipping surface
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Mapping, Sequence
import math
import numpy as np

if __package__:
    from .parents.ebc import BorrowingResult, HistoricalEstimate, borrow_evidence
else:
    from parents.ebc import BorrowingResult, HistoricalEstimate, borrow_evidence
if __package__:
    from .parents.mbpf import BurnoutForecast, forecast_burnout_prepayment
else:
    from parents.mbpf import BurnoutForecast, forecast_burnout_prepayment
if __package__:
    from .parents.mcris import Intervention, InterventionResult, MonthlyTransitionRates, ScenarioResult, simulate_mortgage_intervention
else:
    from parents.mcris import Intervention, InterventionResult, MonthlyTransitionRates, ScenarioResult, simulate_mortgage_intervention
if __package__:
    from .parents.tdsx import SensitivitySurface, explore_sensitivity_surface
else:
    from parents.tdsx import SensitivitySurface, explore_sensitivity_surface


@dataclass(frozen=True)
class BorrowedDefaultEffect:
    borrowing: BorrowingResult
    posterior_log_multiplier: float
    posterior_default_multiplier: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BurnoutInterventionComparison:
    burnout_forecast: BurnoutForecast
    burnout_aware: InterventionResult
    homogeneous_parent: InterventionResult
    homogeneous_constant_prepayment_rate: float
    burnout_minus_homogeneous_net_value: float
    burnout_minus_homogeneous_defaults_avoided: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BAMIWorkbenchResult:
    borrowed_effect: BorrowedDefaultEffect
    intervention_comparison: BurnoutInterventionComparison
    sensitivity_surface: SensitivitySurface | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def borrow_default_multiplier(
    current_log_multiplier: float,
    current_standard_error: float,
    historical: Sequence[HistoricalEstimate],
    *,
    compatibility_scale: float = 1.5,
    borrowing_cap_ratio: float = 2.0,
    current_observation_id: str | None = None,
) -> BorrowedDefaultEffect:
    """Use EBC on a normal-scale log default-rate multiplier, then exponentiate."""
    borrowing = borrow_evidence(
        current_log_multiplier, current_standard_error, historical,
        compatibility_scale=compatibility_scale, borrowing_cap_ratio=borrowing_cap_ratio,
        current_observation_id=current_observation_id,
    )
    multiplier = float(math.exp(borrowing.posterior_estimate))
    return BorrowedDefaultEffect(
        borrowing=borrowing,
        posterior_log_multiplier=float(borrowing.posterior_estimate),
        posterior_default_multiplier=multiplier,
        status="EBC_LOG_EFFECT_CONVERTED_TO_POSITIVE_DEFAULT_MULTIPLIER",
    )


def _validate_static_rates(rates: MonthlyTransitionRates) -> None:
    values = [
        rates.performing_default, rates.performing_prepay, rates.performing_delinquency,
        rates.delinquent_default, rates.delinquent_prepay, rates.delinquent_cure,
    ]
    if any((not np.isfinite(value)) or value < 0 or value > 1 for value in values):
        raise ValueError("transition rates must be finite and lie in [0,1]")
    if rates.delinquent_default + rates.delinquent_prepay + rates.delinquent_cure > 1 + 1e-12:
        raise ValueError("delinquent competing rates exceed one")


def _simulate_path(
    cohort_size: int,
    prepayment_path: np.ndarray,
    rates: MonthlyTransitionRates,
    intervention: Intervention,
    balance_per_loan: float,
    recovery_fraction: float,
    prepayment_cost_fraction: float,
) -> ScenarioResult:
    if any(value < 0 for value in asdict(intervention).values()):
        raise ValueError("intervention multipliers and cost must be nonnegative")
    pd = rates.performing_default * intervention.performing_default_multiplier
    pdel = rates.performing_delinquency * intervention.performing_delinquency_multiplier
    dd = rates.delinquent_default * intervention.delinquent_default_multiplier
    dpr = rates.delinquent_prepay * intervention.delinquent_prepay_multiplier
    dc = rates.delinquent_cure * intervention.delinquent_cure_multiplier
    if dd + dpr + dc > 1 + 1e-12:
        raise ValueError("intervention delinquent competing rates exceed one")
    performing, delinquent, defaulted, prepaid = float(cohort_size), 0.0, 0.0, 0.0
    states = [(performing, delinquent, defaulted, prepaid)]
    for base_prepay in prepayment_path:
        pp = float(base_prepay) * intervention.performing_prepay_multiplier
        if pd + pp + pdel > 1 + 1e-12:
            raise ValueError("intervention performing competing rates exceed one")
        p_default = performing * pd
        p_prepay = performing * pp
        p_delinquent = performing * pdel
        d_default = delinquent * dd
        d_prepay = delinquent * dpr
        d_cure = delinquent * dc
        performing = performing - p_default - p_prepay - p_delinquent + d_cure
        delinquent = delinquent + p_delinquent - d_default - d_prepay - d_cure
        defaulted += p_default + d_default
        prepaid += p_prepay + d_prepay
        states.append((performing, delinquent, defaulted, prepaid))
    credit_loss = defaulted * balance_per_loan * (1.0 - recovery_fraction)
    prepay_cost = prepaid * balance_per_loan * prepayment_cost_fraction
    return ScenarioResult(
        performing=performing, delinquent=delinquent, cumulative_default=defaulted,
        cumulative_prepay=prepaid, probability_mass=performing + delinquent + defaulted + prepaid,
        expected_credit_loss=credit_loss, expected_prepayment_cost=prepay_cost,
        total_economic_loss=credit_loss + prepay_cost, monthly_states=tuple(states),
    )


def simulate_burnout_aware_intervention(
    *,
    cohort_size: int,
    base_monthly_prepayment_rates: Sequence[float],
    propensity_multipliers: Sequence[float],
    initial_class_weights: Sequence[float],
    baseline_rates: MonthlyTransitionRates,
    intervention: Intervention,
    balance_per_loan: float,
    recovery_fraction: float,
    prepayment_cost_fraction: float = 0.0,
) -> BurnoutInterventionComparison:
    """Use MBPF's selection-adjusted prepayment hazard inside MCRIS-style competing risks.

    MBPF is run with zero default hazard because MCRIS owns default/delinquency competition.
    MBPF's default hazard is class-neutral, so omitting it does not change relative burnout
    composition; it only avoids double-counting exits.
    """
    _validate_static_rates(baseline_rates)
    base = np.asarray(base_monthly_prepayment_rates, dtype=float)
    if base.ndim != 1 or base.size < 1:
        raise ValueError("base_monthly_prepayment_rates must be a non-empty vector")
    if cohort_size <= 0 or balance_per_loan <= 0 or not 0 <= recovery_fraction <= 1 or prepayment_cost_fraction < 0:
        raise ValueError("invalid cohort, balance, recovery, or prepayment cost")
    burnout = forecast_burnout_prepayment(
        cohort_size=cohort_size,
        base_monthly_prepayment_rates=base,
        propensity_multipliers=propensity_multipliers,
        initial_class_weights=initial_class_weights,
        monthly_default_rates=0.0,
    )
    path = np.asarray(burnout.effective_prepayment_rates, dtype=float)
    baseline_scenario = _simulate_path(
        cohort_size, path, baseline_rates, Intervention(), balance_per_loan, recovery_fraction, prepayment_cost_fraction
    )
    changed = _simulate_path(
        cohort_size, path, baseline_rates, intervention, balance_per_loan, recovery_fraction, prepayment_cost_fraction
    )
    cost = float(cohort_size * intervention.one_time_cost_per_loan)
    gross = float(baseline_scenario.total_economic_loss - changed.total_economic_loss)
    dynamic_result = InterventionResult(
        baseline=baseline_scenario, intervention=changed, intervention_cost=cost,
        defaults_avoided=float(baseline_scenario.cumulative_default - changed.cumulative_default),
        incremental_prepayments=float(changed.cumulative_prepay - baseline_scenario.cumulative_prepay),
        gross_loss_reduction=gross, net_value=float(gross - cost),
        status="INTERVENTION_CREATES_NET_VALUE" if gross - cost > 0 else "INTERVENTION_COST_EXCEEDS_MODELED_BENEFIT",
    )
    multipliers = np.asarray(propensity_multipliers, dtype=float)
    weights = np.asarray(initial_class_weights, dtype=float); weights = weights / weights.sum()
    homogeneous_rate = float(np.mean(base * float(weights @ multipliers)))
    homogeneous_rates = replace(baseline_rates, performing_prepay=homogeneous_rate)
    parent_result = simulate_mortgage_intervention(
        cohort_size=cohort_size, horizon_months=int(base.size), baseline_rates=homogeneous_rates,
        intervention=intervention, balance_per_loan=balance_per_loan, recovery_fraction=recovery_fraction,
        prepayment_cost_fraction=prepayment_cost_fraction,
    )
    return BurnoutInterventionComparison(
        burnout_forecast=burnout, burnout_aware=dynamic_result, homogeneous_parent=parent_result,
        homogeneous_constant_prepayment_rate=homogeneous_rate,
        burnout_minus_homogeneous_net_value=float(dynamic_result.net_value - parent_result.net_value),
        burnout_minus_homogeneous_defaults_avoided=float(dynamic_result.defaults_avoided - parent_result.defaults_avoided),
        status="BURNOUT_PATH_COMPARED_WITH_HOMOGENEOUS_MCRIS",
    )


def explore_intervention_net_value_surface(
    *,
    cohort_size: int,
    base_monthly_prepayment_rates: Sequence[float],
    propensity_multipliers: Sequence[float],
    initial_class_weights: Sequence[float],
    baseline_rates: MonthlyTransitionRates,
    intervention_template: Intervention,
    balance_per_loan: float,
    recovery_fraction: float,
    parameter_grids: Mapping[str, Sequence[float]],
    baseline_parameters: Mapping[str, float],
) -> SensitivitySurface:
    """TDSX over default multiplier, one-time cost, and prepayment-cost fraction."""
    required = {"default_multiplier", "cost_per_loan", "prepayment_cost_fraction"}
    if set(parameter_grids) != required or set(baseline_parameters) != required:
        raise ValueError("surface parameters must be default_multiplier, cost_per_loan, prepayment_cost_fraction")

    def evaluator(params: Mapping[str, float]) -> float:
        intervention = replace(
            intervention_template,
            performing_default_multiplier=float(params["default_multiplier"]),
            delinquent_default_multiplier=float(params["default_multiplier"]),
            one_time_cost_per_loan=float(params["cost_per_loan"]),
        )
        comparison = simulate_burnout_aware_intervention(
            cohort_size=cohort_size, base_monthly_prepayment_rates=base_monthly_prepayment_rates,
            propensity_multipliers=propensity_multipliers, initial_class_weights=initial_class_weights,
            baseline_rates=baseline_rates, intervention=intervention, balance_per_loan=balance_per_loan,
            recovery_fraction=recovery_fraction, prepayment_cost_fraction=float(params["prepayment_cost_fraction"]),
        )
        return float(comparison.burnout_aware.net_value)

    return explore_sensitivity_surface(
        evaluator, parameter_grids, baseline_parameters,
        decision_threshold=0.0, decision_direction="ABOVE",
    )


def run_bami_workbench(
    *,
    current_log_default_multiplier: float,
    current_standard_error: float,
    historical_effects: Sequence[HistoricalEstimate],
    cohort_size: int,
    base_monthly_prepayment_rates: Sequence[float],
    propensity_multipliers: Sequence[float],
    initial_class_weights: Sequence[float],
    baseline_rates: MonthlyTransitionRates,
    intervention_template: Intervention,
    balance_per_loan: float,
    recovery_fraction: float,
    prepayment_cost_fraction: float,
    compatibility_scale: float = 1.5,
    borrowing_cap_ratio: float = 2.0,
    sensitivity_grids: Mapping[str, Sequence[float]] | None = None,
    current_observation_id: str | None = None,
) -> BAMIWorkbenchResult:
    effect = borrow_default_multiplier(
        current_log_default_multiplier, current_standard_error, historical_effects,
        compatibility_scale=compatibility_scale, borrowing_cap_ratio=borrowing_cap_ratio,
        current_observation_id=current_observation_id,
    )
    intervention = replace(
        intervention_template,
        performing_default_multiplier=effect.posterior_default_multiplier,
        delinquent_default_multiplier=effect.posterior_default_multiplier,
    )
    comparison = simulate_burnout_aware_intervention(
        cohort_size=cohort_size, base_monthly_prepayment_rates=base_monthly_prepayment_rates,
        propensity_multipliers=propensity_multipliers, initial_class_weights=initial_class_weights,
        baseline_rates=baseline_rates, intervention=intervention, balance_per_loan=balance_per_loan,
        recovery_fraction=recovery_fraction, prepayment_cost_fraction=prepayment_cost_fraction,
    )
    surface = None
    if sensitivity_grids is not None:
        baseline_parameters = {
            "default_multiplier": effect.posterior_default_multiplier,
            "cost_per_loan": intervention.one_time_cost_per_loan,
            "prepayment_cost_fraction": prepayment_cost_fraction,
        }
        surface = explore_intervention_net_value_surface(
            cohort_size=cohort_size, base_monthly_prepayment_rates=base_monthly_prepayment_rates,
            propensity_multipliers=propensity_multipliers, initial_class_weights=initial_class_weights,
            baseline_rates=baseline_rates, intervention_template=intervention_template,
            balance_per_loan=balance_per_loan, recovery_fraction=recovery_fraction,
            parameter_grids=sensitivity_grids, baseline_parameters=baseline_parameters,
        )
    return BAMIWorkbenchResult(
        borrowed_effect=effect, intervention_comparison=comparison, sensitivity_surface=surface,
        status="BAMI_EVIDENCE_BURNOUT_COMPETING_RISK_WORKBENCH_READY",
    )
