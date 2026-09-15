from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Sequence

_REPO = Path(__file__).resolve().parents[3]
_FOUNDRY_PRODUCTS = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products"
if str(_FOUNDRY_PRODUCTS) not in sys.path:
    sys.path.insert(0, str(_FOUNDRY_PRODUCTS))

from P140_BOSA.bosa import audit_burnout_support  # noqa: E402


@dataclass(frozen=True)
class SGMBResult:
    month: int
    effective_sample_fraction: float
    max_normalized_weight: float
    support_status: str
    pilot_correlation: float
    mode: str
    n_fine: int
    n_cheap: int
    spent_budget: float
    variance_proxy: float
    support_gate_open: bool
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _multifidelity_allocation(total_budget, fine_cost, cheap_cost, rho_hat, min_fine):
    """Independent corrected K048 count allocator."""
    C = float(total_budget)
    cf = float(fine_cost)
    cc = float(cheap_cost)
    if C < 0 or cf <= 0 or cc <= 0 or int(min_fine) < 1:
        raise ValueError("invalid budget/cost contract")
    max_fine = int(C // cf)
    if max_fine < 1:
        return {"mode": "unfunded", "n_fine": 0, "n_cheap": 0, "variance_proxy": float("inf")}
    rh = min(abs(float(rho_hat)), 0.999)
    best = {"mode": "fine_only", "n_fine": max_fine, "n_cheap": 0, "variance_proxy": 1.0 / max_fine}
    if max_fine < int(min_fine):
        return best
    for nf in range(int(min_fine), max_fine + 1):
        nc = int((C - cf * nf) // cc)
        if nc < nf or nc <= 0:
            continue
        var = (1.0 - rh * rh) / nf + (rh * rh) / nc
        if var < best["variance_proxy"]:
            best = {"mode": "multifidelity", "n_fine": nf, "n_cheap": nc, "variance_proxy": float(var)}
    return best


def support_gated_multifidelity_monitoring(
    *,
    cohort_size: int,
    base_rates: Sequence[float],
    propensity_multipliers: Sequence[float],
    initial_class_weights: Sequence[float],
    month: int,
    total_budget: float,
    fine_cost: float,
    cheap_cost: float,
    pilot_correlation: float,
    min_fine: int = 20,
    min_correlation: float = 0.2,
    fragile_ess_fraction: float = 0.8,
    monthly_default_rates: float | Sequence[float] = 0.0,
) -> SGMBResult:
    """BOSA support gate followed by K048-style multi-fidelity routing.

    A high pilot correlation is not enough to justify a cheap channel if the
    target survivor population is no longer adequately supported by the
    original cohort.  When BOSA reports fragile overlap, cheap acquisition is
    disabled and the same budget is routed fine-only.  When support remains
    usable, the corrected K048 allocation is preserved, subject to a declared
    minimum correlation.
    """
    if month < 0:
        raise ValueError("month must be non-negative")
    audit = audit_burnout_support(
        cohort_size=cohort_size,
        base_rates=base_rates,
        propensity_multipliers=propensity_multipliers,
        initial_class_weights=initial_class_weights,
        months_to_audit=[int(month)],
        fragile_ess_fraction=fragile_ess_fraction,
        monthly_default_rates=monthly_default_rates,
    )
    p = audit.points[0]
    proposal = _multifidelity_allocation(total_budget, fine_cost, cheap_cost, pilot_correlation, min_fine)
    max_fine = int(float(total_budget) // float(fine_cost)) if fine_cost > 0 else 0

    if p.support_status != "SUPPORT_USABLE":
        mode = "fine_only" if max_fine > 0 else "unfunded"
        nf = max_fine
        nc = 0
        var = 1.0 / nf if nf > 0 else float("inf")
        return SGMBResult(
            int(month), p.effective_sample_fraction, p.max_normalized_weight,
            p.support_status, float(pilot_correlation), mode, nf, nc,
            nf * float(fine_cost), var, False,
            "SUPPORT_FRAGILE_CHEAP_CHANNEL_DISABLED_FINE_ONLY_FALLBACK",
        )

    if abs(float(pilot_correlation)) < float(min_correlation) or proposal["mode"] != "multifidelity":
        mode = "fine_only" if max_fine > 0 else "unfunded"
        nf = max_fine
        nc = 0
        var = 1.0 / nf if nf > 0 else float("inf")
        return SGMBResult(
            int(month), p.effective_sample_fraction, p.max_normalized_weight,
            p.support_status, float(pilot_correlation), mode, nf, nc,
            nf * float(fine_cost), var, True,
            "SUPPORT_USABLE_BUT_CHEAP_CHANNEL_NOT_CORRELATION_QUALIFIED",
        )

    nf = proposal["n_fine"]
    nc = proposal["n_cheap"]
    return SGMBResult(
        int(month), p.effective_sample_fraction, p.max_normalized_weight,
        p.support_status, float(pilot_correlation), "multifidelity", nf, nc,
        nf * float(fine_cost) + nc * float(cheap_cost), proposal["variance_proxy"], True,
        "SUPPORT_AND_CORRELATION_QUALIFIED_MULTIFIDELITY_PROGRAM",
    )
