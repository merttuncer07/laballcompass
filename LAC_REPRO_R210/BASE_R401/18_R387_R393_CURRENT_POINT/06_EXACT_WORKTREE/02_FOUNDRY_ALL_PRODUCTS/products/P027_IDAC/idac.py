from __future__ import annotations

from dataclasses import dataclass
from math import floor, isclose


@dataclass(frozen=True)
class DeployabilityIntegralityAudit:
    continuous_value: float
    integer_value: float
    integrality_gap: float
    matrix_integral: bool
    integer_rhs: bool
    theorem_certificate: bool
    observed_lp_integral: bool
    status: str


def audit_series_deployment(
    active_stock: float,
    capacities: list[float],
    yields: list[float],
) -> DeployabilityIntegralityAudit:
    """Exact audit for the series-network shell; refuses broader TU claims."""
    if len(capacities) != len(yields) or not capacities:
        raise ValueError("capacities and yields must align")
    amount = active_stock
    for capacity, yield_fraction in zip(capacities, yields):
        amount = min(amount, capacity) * yield_fraction
    continuous = amount
    integer = float(floor(continuous + 1e-12))
    matrix_integral = all(isclose(y, round(y)) and y in (0, 1) for y in yields)
    integer_rhs = isclose(active_stock, round(active_stock)) and all(isclose(c, round(c)) for c in capacities)
    theorem = matrix_integral and integer_rhs
    observed = isclose(continuous, round(continuous))
    status = "DISCRETE_DEPLOYABILITY_CERTIFIED" if theorem else "CONTINUOUS_DEPLOYMENT_ONLY"
    return DeployabilityIntegralityAudit(continuous, integer, continuous-integer, matrix_integral, integer_rhs, theorem, observed, status)
