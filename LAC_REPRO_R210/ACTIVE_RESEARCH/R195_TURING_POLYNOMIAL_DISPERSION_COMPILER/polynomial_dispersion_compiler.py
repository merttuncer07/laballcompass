from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

import numpy as np


def _trim(coefficients: np.ndarray, tol: float = 1e-14) -> np.ndarray:
    c = np.asarray(coefficients, dtype=float).copy()
    while len(c) > 1 and abs(c[-1]) <= tol:
        c = c[:-1]
    return c


def real_roots_in_interval(coefficients, lower: float, upper: float, tol: float = 1e-9):
    c = _trim(np.asarray(coefficients, dtype=float))
    if len(c) <= 1:
        return []
    roots = np.polynomial.polynomial.polyroots(c)
    out = []
    for root in roots:
        if abs(root.imag) <= tol * (1.0 + abs(root.real)):
            value = float(root.real)
            if lower - tol <= value <= upper + tol:
                out.append(float(np.clip(value, lower, upper)))
    return out


@dataclass(frozen=True)
class CompiledModeDesign:
    target_mode: int
    q: float
    length: float
    base_target_rate: float
    base_rival_rate: float
    rival_mode: int
    separation_margin: float
    additive_quench: float
    target_quench_rate: float
    worst_rival_quench_rate: float
    candidate_count: int
    robust_interval: bool = False


@dataclass(frozen=True)
class CompiledShapeDesign:
    target_mode: int
    q: float
    length: float
    worst_case_rival_mode: int
    certified_separation_margin: float
    max_symmetric_microprobe_error: float
    candidate_count: int


class PolynomialDispersionCompiler:
    """Exact-candidate inverse design for even polynomial dispersion laws.

    The uncontrolled dispersion is

        g(k) = c0 + c1*k^2 + c2*k^4 + ...

    and an additive control `u` gives lambda(k)=g(k)+u. Allowed modes obey
    k_n = boundary_factor*n/L. With q=(boundary_factor/L)^2, every modal rate
    is a polynomial in q. The compiler enumerates all algebraic points at which
    the lower envelope of target-vs-rival margins can attain its maximum.
    """

    def __init__(self, coefficients, boundary_factor: float = 2.0 * pi):
        self.coefficients = _trim(np.asarray(coefficients, dtype=float))
        self.boundary_factor = float(boundary_factor)
        if len(self.coefficients) < 2:
            raise ValueError("at least one non-constant dispersion term is required")
        if self.boundary_factor <= 0:
            raise ValueError("boundary_factor must be positive")

    def modal_polynomial(self, mode: int) -> np.ndarray:
        if mode < 1:
            raise ValueError("mode must be positive")
        powers = np.arange(len(self.coefficients), dtype=float)
        return self.coefficients * (float(mode) ** (2.0 * powers))

    def modal_rate_q(self, mode: int, q) -> np.ndarray:
        return np.polynomial.polynomial.polyval(q, self.modal_polynomial(mode))

    def modal_rate(self, mode: int, length: float, additive_control: float = 0.0) -> float:
        q = (self.boundary_factor / float(length)) ** 2
        return float(self.modal_rate_q(mode, q) + additive_control)

    def crossing_q(self, mode_a: int, mode_b: int, q_bounds=(1e-8, 1e4)) -> list[float]:
        difference = self.modal_polynomial(mode_a) - self.modal_polynomial(mode_b)
        return [
            q
            for q in real_roots_in_interval(difference, *q_bounds)
            if q > max(0.0, q_bounds[0]) + 1e-12
        ]

    def _candidate_q(self, target: int, rivals: list[int], q_bounds) -> list[float]:
        lo, hi = map(float, q_bounds)
        if not 0 < lo < hi:
            raise ValueError("q_bounds must satisfy 0 < lower < upper")
        target_poly = self.modal_polynomial(target)
        differences = {
            rival: target_poly - self.modal_polynomial(rival) for rival in rivals
        }
        candidates = {lo, hi}
        for difference in differences.values():
            candidates.update(real_roots_in_interval(difference, lo, hi))
            derivative = np.polynomial.polynomial.polyder(difference)
            candidates.update(real_roots_in_interval(derivative, lo, hi))
        # The minimum of smooth margins can peak at a switch of the active rival.
        for i, first in enumerate(rivals):
            for second in rivals[i + 1 :]:
                rival_switch = self.modal_polynomial(first) - self.modal_polynomial(second)
                candidates.update(real_roots_in_interval(rival_switch, lo, hi))
        return sorted(q for q in candidates if lo - 1e-10 <= q <= hi + 1e-10)

    def design(self, target_mode: int, modes, q_bounds) -> CompiledModeDesign:
        modes = sorted(set(int(m) for m in modes))
        if target_mode not in modes:
            raise ValueError("target_mode must be included in modes")
        rivals = [m for m in modes if m != target_mode]
        if not rivals:
            raise ValueError("at least one rival mode is required")
        candidates = self._candidate_q(target_mode, rivals, q_bounds)
        best = None
        for q in candidates:
            target_rate = float(self.modal_rate_q(target_mode, q))
            rival_rates = {m: float(self.modal_rate_q(m, q)) for m in rivals}
            rival_mode = max(rival_rates, key=rival_rates.get)
            rival_rate = rival_rates[rival_mode]
            margin = target_rate - rival_rate
            key = (margin, -abs(np.log(q / np.sqrt(q_bounds[0] * q_bounds[1]))))
            if best is None or key > best[0]:
                best = (key, q, target_rate, rival_rate, rival_mode)
        _, q, target_rate, rival_rate, rival_mode = best
        margin = target_rate - rival_rate
        if margin <= 1e-12:
            raise ValueError("target has no strictly dominant window inside q_bounds")
        quench = -0.5 * (target_rate + rival_rate)
        length = self.boundary_factor / sqrt(q)
        return CompiledModeDesign(
            target_mode=target_mode,
            q=float(q),
            length=float(length),
            base_target_rate=float(target_rate),
            base_rival_rate=float(rival_rate),
            rival_mode=int(rival_mode),
            separation_margin=float(margin),
            additive_quench=float(quench),
            target_quench_rate=float(target_rate + quench),
            worst_rival_quench_rate=float(rival_rate + quench),
            candidate_count=len(candidates),
            robust_interval=False,
        )

    def design_interval(
        self,
        target_mode: int,
        modes,
        q_bounds,
        coefficient_lower,
        coefficient_upper,
    ) -> CompiledModeDesign:
        """Certified design for an axis-aligned coefficient uncertainty box.

        Since q>0 and mode powers are nonnegative, the smallest possible target
        rate uses every lower coefficient and the largest rival rate uses every
        upper coefficient. Maximizing their gap is again a polynomial lower-
        envelope problem, so no sampling of the uncertainty box is needed.
        """
        lower = np.asarray(coefficient_lower, dtype=float)
        upper = np.asarray(coefficient_upper, dtype=float)
        if lower.shape != self.coefficients.shape or upper.shape != self.coefficients.shape:
            raise ValueError("coefficient interval must match compiler coefficients")
        if np.any(lower > upper):
            raise ValueError("coefficient_lower must not exceed coefficient_upper")
        modes = sorted(set(int(m) for m in modes))
        if target_mode not in modes:
            raise ValueError("target_mode must be included in modes")
        rivals = [m for m in modes if m != target_mode]
        if not rivals:
            raise ValueError("at least one rival mode is required")
        lo, hi = map(float, q_bounds)
        if not 0 < lo < hi:
            raise ValueError("q_bounds must satisfy 0 < lower < upper")

        powers = np.arange(len(lower), dtype=float)
        target_low = lower * (float(target_mode) ** (2.0 * powers))
        rival_high = {
            rival: upper * (float(rival) ** (2.0 * powers)) for rival in rivals
        }
        differences = {
            rival: target_low - polynomial for rival, polynomial in rival_high.items()
        }
        candidates = {lo, hi}
        for difference in differences.values():
            candidates.update(real_roots_in_interval(difference, lo, hi))
            candidates.update(
                real_roots_in_interval(
                    np.polynomial.polynomial.polyder(difference), lo, hi
                )
            )
        for i, first in enumerate(rivals):
            for second in rivals[i + 1 :]:
                candidates.update(
                    real_roots_in_interval(
                        rival_high[first] - rival_high[second], lo, hi
                    )
                )
        candidates = sorted(q for q in candidates if lo - 1e-10 <= q <= hi + 1e-10)

        best = None
        for q in candidates:
            target_rate = float(np.polynomial.polynomial.polyval(q, target_low))
            rival_rates = {
                rival: float(np.polynomial.polynomial.polyval(q, polynomial))
                for rival, polynomial in rival_high.items()
            }
            rival_mode = max(rival_rates, key=rival_rates.get)
            rival_rate = rival_rates[rival_mode]
            margin = target_rate - rival_rate
            key = (margin, -abs(np.log(q / np.sqrt(lo * hi))))
            if best is None or key > best[0]:
                best = (key, q, target_rate, rival_rate, rival_mode)
        _, q, target_rate, rival_rate, rival_mode = best
        margin = target_rate - rival_rate
        if margin <= 1e-12:
            raise ValueError("no robust target-dominant window exists for this coefficient box")
        quench = -0.5 * (target_rate + rival_rate)
        return CompiledModeDesign(
            target_mode=target_mode,
            q=float(q),
            length=float(self.boundary_factor / sqrt(q)),
            base_target_rate=float(target_rate),
            base_rival_rate=float(rival_rate),
            rival_mode=int(rival_mode),
            separation_margin=float(margin),
            additive_quench=float(quench),
            target_quench_rate=float(target_rate + quench),
            worst_rival_quench_rate=float(rival_rate + quench),
            candidate_count=len(candidates),
            robust_interval=True,
        )

    def design_shape_interval(
        self,
        target_mode: int,
        modes,
        q_bounds,
        coefficient_lower,
        coefficient_upper,
    ) -> CompiledShapeDesign:
        """Certify target dominance while cancelling common coefficient effects.

        Unlike `design_interval`, this does not promise a fixed absolute quench.
        It certifies the target-vs-rival rate difference for every coefficient
        vector in the box. A two-rate micro-probe at the selected geometry then
        calibrates the additive quench and removes the uncertain common offset.
        """
        lower = np.asarray(coefficient_lower, dtype=float)
        upper = np.asarray(coefficient_upper, dtype=float)
        if lower.shape != self.coefficients.shape or upper.shape != self.coefficients.shape:
            raise ValueError("coefficient interval must match compiler coefficients")
        if np.any(lower > upper):
            raise ValueError("coefficient_lower must not exceed coefficient_upper")
        modes = sorted(set(int(m) for m in modes))
        if target_mode not in modes:
            raise ValueError("target_mode must be included in modes")
        rivals = [m for m in modes if m != target_mode]
        if not rivals:
            raise ValueError("at least one rival mode is required")
        lo, hi = map(float, q_bounds)
        if not 0 < lo < hi:
            raise ValueError("q_bounds must satisfy 0 < lower < upper")
        powers = np.arange(len(lower), dtype=float)
        target_factors = float(target_mode) ** (2.0 * powers)
        robust_differences = {}
        for rival in rivals:
            factors = target_factors - float(rival) ** (2.0 * powers)
            # Minimize each linear coefficient contribution over the same box.
            robust_differences[rival] = np.where(
                factors >= 0.0, lower * factors, upper * factors
            )

        candidates = {lo, hi}
        for difference in robust_differences.values():
            candidates.update(real_roots_in_interval(difference, lo, hi))
            candidates.update(
                real_roots_in_interval(
                    np.polynomial.polynomial.polyder(difference), lo, hi
                )
            )
        rival_items = list(robust_differences.items())
        for i, (_, first) in enumerate(rival_items):
            for _, second in rival_items[i + 1 :]:
                candidates.update(real_roots_in_interval(first - second, lo, hi))
        candidates = sorted(q for q in candidates if lo - 1e-10 <= q <= hi + 1e-10)

        best = None
        for q in candidates:
            margins = {
                rival: float(np.polynomial.polynomial.polyval(q, difference))
                for rival, difference in robust_differences.items()
            }
            rival_mode = min(margins, key=margins.get)
            margin = margins[rival_mode]
            key = (margin, -abs(np.log(q / np.sqrt(lo * hi))))
            if best is None or key > best[0]:
                best = (key, q, margin, rival_mode)
        _, q, margin, rival_mode = best
        if margin <= 1e-12:
            raise ValueError("no coefficient-box-robust target-dominant geometry exists")
        return CompiledShapeDesign(
            target_mode=target_mode,
            q=float(q),
            length=float(self.boundary_factor / sqrt(q)),
            worst_case_rival_mode=int(rival_mode),
            certified_separation_margin=float(margin),
            max_symmetric_microprobe_error=float(0.5 * margin),
            candidate_count=len(candidates),
        )

    @staticmethod
    def microprobe_quench(observed_target_rate: float, observed_rival_rate: float) -> float:
        """Center two observed rates around zero with a common additive control."""
        return -0.5 * (float(observed_target_rate) + float(observed_rival_rate))

    def dense_oracle(self, target_mode: int, modes, q_bounds, samples: int = 100_001):
        q = np.linspace(q_bounds[0], q_bounds[1], samples)
        target = self.modal_rate_q(target_mode, q)
        rivals = np.vstack([self.modal_rate_q(m, q) for m in modes if m != target_mode])
        margins = target - rivals.max(axis=0)
        idx = int(np.argmax(margins))
        return {"q": float(q[idx]), "margin": float(margins[idx])}


def simulate_transition(
    normalized_rates: dict[int, float],
    previous_mode: int,
    target_mode: int,
    *,
    hold_time: float = 45.0,
    dt: float = 0.01,
    cross_saturation: float = 8.0,
    disturbance_floor: float = 1e-5,
) -> dict:
    """Dimensionless competing-amplitude transition sanity model."""
    modes = sorted(normalized_rates)
    rates = np.array([normalized_rates[m] for m in modes], dtype=float)
    amp = np.full(len(modes), disturbance_floor, dtype=float)
    amp[modes.index(previous_mode)] = np.sqrt(max(normalized_rates[previous_mode], 0.2))
    for _ in range(int(round(hold_time / dt))):
        amp = np.maximum(amp, disturbance_floor)
        total2 = float(np.sum(amp**2))
        competition = cross_saturation * (total2 - amp**2)
        amp += dt * (rates * amp - amp**3 - competition * amp)
        amp = np.maximum(amp, 0.0)
    winner = modes[int(np.argmax(amp))]
    return {
        "winner": int(winner),
        "target_won": bool(winner == target_mode),
        "amplitudes": {int(m): float(a) for m, a in zip(modes, amp)},
    }
