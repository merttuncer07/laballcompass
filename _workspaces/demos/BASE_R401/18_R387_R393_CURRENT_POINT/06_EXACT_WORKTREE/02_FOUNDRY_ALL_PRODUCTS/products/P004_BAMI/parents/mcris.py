"""Mortgage Competing-Risk Intervention Simulator (MCRIS) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MonthlyTransitionRates:
    performing_default: float
    performing_prepay: float
    performing_delinquency: float
    delinquent_default: float
    delinquent_prepay: float
    delinquent_cure: float


@dataclass(frozen=True)
class Intervention:
    performing_default_multiplier: float = 1.0
    performing_prepay_multiplier: float = 1.0
    performing_delinquency_multiplier: float = 1.0
    delinquent_default_multiplier: float = 1.0
    delinquent_prepay_multiplier: float = 1.0
    delinquent_cure_multiplier: float = 1.0
    one_time_cost_per_loan: float = 0.0


@dataclass(frozen=True)
class ScenarioResult:
    performing: float
    delinquent: float
    cumulative_default: float
    cumulative_prepay: float
    probability_mass: float
    expected_credit_loss: float
    expected_prepayment_cost: float
    total_economic_loss: float
    monthly_states: tuple[tuple[float, float, float, float], ...]


@dataclass(frozen=True)
class InterventionResult:
    baseline: ScenarioResult
    intervention: ScenarioResult
    intervention_cost: float
    defaults_avoided: float
    incremental_prepayments: float
    gross_loss_reduction: float
    net_value: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_rates(rates: MonthlyTransitionRates) -> None:
    values = asdict(rates)
    if any(value < 0 or value > 1 for value in values.values()):
        raise ValueError("transition rates must lie in [0, 1]")
    if rates.performing_default + rates.performing_prepay + rates.performing_delinquency > 1 + 1e-12:
        raise ValueError("performing competing rates exceed one")
    if rates.delinquent_default + rates.delinquent_prepay + rates.delinquent_cure > 1 + 1e-12:
        raise ValueError("delinquent competing rates exceed one")


def _modified(rates: MonthlyTransitionRates, intervention: Intervention) -> MonthlyTransitionRates:
    if any(value < 0 for value in asdict(intervention).values()):
        raise ValueError("intervention multipliers and cost must be nonnegative")
    changed = MonthlyTransitionRates(
        rates.performing_default * intervention.performing_default_multiplier,
        rates.performing_prepay * intervention.performing_prepay_multiplier,
        rates.performing_delinquency * intervention.performing_delinquency_multiplier,
        rates.delinquent_default * intervention.delinquent_default_multiplier,
        rates.delinquent_prepay * intervention.delinquent_prepay_multiplier,
        rates.delinquent_cure * intervention.delinquent_cure_multiplier,
    )
    _validate_rates(changed)
    return changed


def _simulate(
    cohort_size: float,
    horizon_months: int,
    rates: MonthlyTransitionRates,
    balance_per_loan: float,
    recovery_fraction: float,
    prepayment_cost_fraction: float,
) -> ScenarioResult:
    performing, delinquent, defaulted, prepaid = float(cohort_size), 0.0, 0.0, 0.0
    states = [(performing, delinquent, defaulted, prepaid)]
    for _ in range(horizon_months):
        p_default = performing * rates.performing_default
        p_prepay = performing * rates.performing_prepay
        p_delinquent = performing * rates.performing_delinquency
        d_default = delinquent * rates.delinquent_default
        d_prepay = delinquent * rates.delinquent_prepay
        d_cure = delinquent * rates.delinquent_cure
        performing = performing - p_default - p_prepay - p_delinquent + d_cure
        delinquent = delinquent + p_delinquent - d_default - d_prepay - d_cure
        defaulted += p_default + d_default
        prepaid += p_prepay + d_prepay
        states.append((performing, delinquent, defaulted, prepaid))
    credit_loss = defaulted * balance_per_loan * (1.0 - recovery_fraction)
    prepay_cost = prepaid * balance_per_loan * prepayment_cost_fraction
    return ScenarioResult(
        performing=performing,
        delinquent=delinquent,
        cumulative_default=defaulted,
        cumulative_prepay=prepaid,
        probability_mass=performing + delinquent + defaulted + prepaid,
        expected_credit_loss=credit_loss,
        expected_prepayment_cost=prepay_cost,
        total_economic_loss=credit_loss + prepay_cost,
        monthly_states=tuple(states),
    )


def simulate_mortgage_intervention(
    *,
    cohort_size: int,
    horizon_months: int,
    baseline_rates: MonthlyTransitionRates,
    intervention: Intervention,
    balance_per_loan: float,
    recovery_fraction: float,
    prepayment_cost_fraction: float = 0.0,
) -> InterventionResult:
    """Simulate default and prepayment jointly, then value an intervention against baseline."""

    if not isinstance(cohort_size, int) or cohort_size <= 0 or not isinstance(horizon_months, int) or horizon_months <= 0:
        raise ValueError("cohort_size and horizon_months must be positive integers")
    if balance_per_loan <= 0 or not 0 <= recovery_fraction <= 1 or prepayment_cost_fraction < 0:
        raise ValueError("invalid balance, recovery, or prepayment cost")
    _validate_rates(baseline_rates)
    intervention_rates = _modified(baseline_rates, intervention)
    baseline = _simulate(cohort_size, horizon_months, baseline_rates, balance_per_loan, recovery_fraction, prepayment_cost_fraction)
    changed = _simulate(cohort_size, horizon_months, intervention_rates, balance_per_loan, recovery_fraction, prepayment_cost_fraction)
    cost = cohort_size * intervention.one_time_cost_per_loan
    gross = baseline.total_economic_loss - changed.total_economic_loss
    net = gross - cost
    return InterventionResult(
        baseline=baseline,
        intervention=changed,
        intervention_cost=float(cost),
        defaults_avoided=float(baseline.cumulative_default - changed.cumulative_default),
        incremental_prepayments=float(changed.cumulative_prepay - baseline.cumulative_prepay),
        gross_loss_reduction=float(gross),
        net_value=float(net),
        status="INTERVENTION_CREATES_NET_VALUE" if net > 0 else "INTERVENTION_COST_EXCEEDS_MODELED_BENEFIT",
    )
