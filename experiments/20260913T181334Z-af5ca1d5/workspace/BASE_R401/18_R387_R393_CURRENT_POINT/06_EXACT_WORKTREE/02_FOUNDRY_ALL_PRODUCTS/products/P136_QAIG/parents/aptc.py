"""Ambipolar Packet Transport Calculator (APTC) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class AmbipolarResult:
    ambipolar_diffusion_coefficient_neutral_limit: float
    internal_electric_field: tuple[float, ...]
    electron_flux: tuple[float, ...]
    hole_flux: tuple[float, ...]
    maximum_coupled_flux_mismatch: float
    maximum_uncoupled_flux_mismatch: float
    maximum_relative_charge_imbalance: float
    initial_packet_variance: float
    predicted_packet_variance: float | None
    predicted_rms_width: float | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_ambipolar_transport(
    positions: Sequence[float],
    electron_density: Sequence[float],
    hole_density: Sequence[float],
    *,
    electron_mobility: float,
    hole_mobility: float,
    electron_diffusivity: float,
    hole_diffusivity: float,
    forecast_time: float | None = None,
    quasineutrality_tolerance: float = 0.05,
) -> AmbipolarResult:
    """Compute the restoring field that enforces zero-current coupled electron/hole flux."""

    x = np.asarray(positions, dtype=float)
    n = np.asarray(electron_density, dtype=float)
    p = np.asarray(hole_density, dtype=float)
    if x.ndim != 1 or x.size < 5 or n.shape != x.shape or p.shape != x.shape or np.any(np.diff(x) <= 0):
        raise ValueError("positions must increase and both density profiles must match")
    if np.any(n <= 0) or np.any(p <= 0) or not all(np.all(np.isfinite(a)) for a in (x, n, p)):
        raise ValueError("density profiles must be finite and strictly positive")
    parameters = (electron_mobility, hole_mobility, electron_diffusivity, hole_diffusivity)
    if any(value <= 0 for value in parameters) or (forecast_time is not None and forecast_time < 0) or not 0 <= quasineutrality_tolerance < 1:
        raise ValueError("transport parameters must be positive and tolerances/times valid")

    dn = np.gradient(n, x)
    dp = np.gradient(p, x)
    denominator = hole_mobility * p + electron_mobility * n
    field = (hole_diffusivity * dp - electron_diffusivity * dn) / denominator
    electron_flux = -electron_mobility * n * field - electron_diffusivity * dn
    hole_flux = hole_mobility * p * field - hole_diffusivity * dp
    coupled_mismatch = float(np.max(np.abs(electron_flux - hole_flux)))
    uncoupled_electron = -electron_diffusivity * dn
    uncoupled_hole = -hole_diffusivity * dp
    uncoupled_mismatch = float(np.max(np.abs(uncoupled_electron - uncoupled_hole)))
    imbalance = float(np.max(np.abs(n - p) / ((n + p) / 2.0)))
    ambipolar_d = float(
        (electron_mobility * hole_diffusivity + hole_mobility * electron_diffusivity)
        / (electron_mobility + hole_mobility)
    )
    packet = (n + p) / 2.0
    normalization = float(np.trapezoid(packet, x))
    centroid = float(np.trapezoid(x * packet, x) / normalization)
    variance = float(np.trapezoid((x - centroid) ** 2 * packet, x) / normalization)
    predicted_variance = None if forecast_time is None else variance + 2.0 * ambipolar_d * forecast_time
    scale = max(float(np.max(np.abs(electron_flux))), float(np.max(np.abs(hole_flux))), 1e-15)
    flux_consistent = coupled_mismatch <= 1e-10 * scale + 1e-12
    status = (
        "AMBIPOLAR_PACKET_TRANSPORT_VALID"
        if imbalance <= quasineutrality_tolerance and flux_consistent
        else "QUASINEUTRAL_PACKET_ASSUMPTION_EXCEEDED"
    )
    return AmbipolarResult(
        ambipolar_diffusion_coefficient_neutral_limit=ambipolar_d,
        internal_electric_field=tuple(map(float, field)),
        electron_flux=tuple(map(float, electron_flux)),
        hole_flux=tuple(map(float, hole_flux)),
        maximum_coupled_flux_mismatch=coupled_mismatch,
        maximum_uncoupled_flux_mismatch=uncoupled_mismatch,
        maximum_relative_charge_imbalance=imbalance,
        initial_packet_variance=variance,
        predicted_packet_variance=None if predicted_variance is None else float(predicted_variance),
        predicted_rms_width=None if predicted_variance is None else float(np.sqrt(predicted_variance)),
        status=status,
    )
