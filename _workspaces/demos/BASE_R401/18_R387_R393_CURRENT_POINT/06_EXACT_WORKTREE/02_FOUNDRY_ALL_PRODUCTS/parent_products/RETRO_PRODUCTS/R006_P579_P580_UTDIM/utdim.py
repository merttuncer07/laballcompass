"""Unequal-Transport Double-diffusive Instability Monitor (UTDIM) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ModeGrowth:
    wavenumber: float
    actual_growth_rate: float
    equal_transport_growth_rate: float


@dataclass(frozen=True)
class DoubleDiffusiveResult:
    static_stability_index: float
    diffusivity_ratio: float
    fastest_wavenumber: float
    maximum_growth_rate: float
    equal_transport_growth_at_fastest_mode: float
    e_folding_time: float | None
    unstable_wavenumber_band: tuple[float, float] | None
    fastest_mode_eigenvector_magnitudes: tuple[float, float, float]
    modes: tuple[ModeGrowth, ...]
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _matrix(
    wavenumber: float,
    viscosity: float,
    diffusivities: np.ndarray,
    buoyancy_coefficients: np.ndarray,
    background_gradients: np.ndarray,
) -> np.ndarray:
    q = wavenumber * wavenumber
    return np.array([
        [-viscosity * q, buoyancy_coefficients[0], buoyancy_coefficients[1]],
        [-background_gradients[0], -diffusivities[0] * q, 0.0],
        [-background_gradients[1], 0.0, -diffusivities[1] * q],
    ])


def monitor_double_diffusive_instability(
    *,
    viscosity: float,
    diffusivities: Sequence[float],
    buoyancy_coefficients: Sequence[float],
    background_gradients: Sequence[float],
    wavenumbers: Sequence[float],
    growth_tolerance: float = 1e-9,
) -> DoubleDiffusiveResult:
    """Scan a two-scalar Boussinesq linearization and an equal-diffusivity counterfactual."""

    d = np.asarray(diffusivities, dtype=float)
    b = np.asarray(buoyancy_coefficients, dtype=float)
    gradients = np.asarray(background_gradients, dtype=float)
    k_values = np.asarray(wavenumbers, dtype=float)
    if viscosity <= 0 or d.shape != (2,) or np.any(d <= 0) or b.shape != (2,) or gradients.shape != (2,):
        raise ValueError("viscosity/diffusivities must be positive and both scalar vectors length two")
    if k_values.ndim != 1 or k_values.size < 2 or np.any(k_values <= 0) or np.any(np.diff(k_values) <= 0):
        raise ValueError("wavenumbers must be a strictly increasing positive vector")
    if not all(np.all(np.isfinite(array)) for array in (d, b, gradients, k_values)) or growth_tolerance < 0:
        raise ValueError("all inputs must be finite and tolerance nonnegative")

    equal_d = np.full(2, float(np.mean(d)))
    actual_growth = []
    equal_growth = []
    leading_vectors = []
    for k in k_values:
        eigenvalues, eigenvectors = np.linalg.eig(_matrix(k, viscosity, d, b, gradients))
        leading = int(np.argmax(eigenvalues.real))
        actual_growth.append(float(eigenvalues[leading].real))
        vector = np.abs(eigenvectors[:, leading]); vector = vector / np.linalg.norm(vector)
        leading_vectors.append(vector)
        equal_eigenvalues = np.linalg.eigvals(_matrix(k, viscosity, equal_d, b, gradients))
        equal_growth.append(float(np.max(equal_eigenvalues.real)))
    actual = np.asarray(actual_growth); equal = np.asarray(equal_growth)
    fastest = int(np.argmax(actual))
    unstable = k_values[actual > growth_tolerance]
    band = None if unstable.size == 0 else (float(unstable[0]), float(unstable[-1]))
    max_growth = float(actual[fastest])
    static_index = float(np.dot(b, gradients))
    mismatch_specific = max_growth > growth_tolerance and float(np.max(equal)) <= growth_tolerance and static_index > 0
    if mismatch_specific:
        status = "UNEQUAL_TRANSPORT_DESTABILIZATION_DETECTED"
    elif max_growth > growth_tolerance:
        status = "INSTABILITY_NOT_UNIQUELY_ATTRIBUTABLE_TO_TRANSPORT_MISMATCH"
    else:
        status = "NO_LINEAR_INSTABILITY_IN_SCANNED_BAND"
    modes = tuple(
        ModeGrowth(float(k), float(g), float(ge))
        for k, g, ge in zip(k_values, actual, equal)
    )
    return DoubleDiffusiveResult(
        static_stability_index=static_index,
        diffusivity_ratio=float(max(d) / min(d)),
        fastest_wavenumber=float(k_values[fastest]),
        maximum_growth_rate=max_growth,
        equal_transport_growth_at_fastest_mode=float(equal[fastest]),
        e_folding_time=None if max_growth <= growth_tolerance else float(1.0 / max_growth),
        unstable_wavenumber_band=band,
        fastest_mode_eigenvector_magnitudes=tuple(map(float, leading_vectors[fastest])),
        modes=modes,
        status=status,
    )
