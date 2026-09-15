"""Curvature-driven Size-Distribution Controller (CSDC) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class CoarseningState:
    time: float
    particle_count: int
    critical_radius: float
    number_mean_radius: float
    radius_coefficient_of_variation: float
    total_material_volume_proxy: float


@dataclass(frozen=True)
class CoarseningResult:
    initial_radii: tuple[float, ...]
    final_radii: tuple[float, ...]
    states: tuple[CoarseningState, ...]
    stop_time: float
    dissolved_particle_count: int
    initial_mean_radius: float
    final_mean_radius: float
    maximum_relative_volume_error: float
    target_mean_radius: float | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _state(time: float, radii: np.ndarray) -> CoarseningState:
    critical = float(np.sum(radii ** 2) / np.sum(radii))
    mean = float(np.mean(radii))
    return CoarseningState(
        time=float(time),
        particle_count=int(radii.size),
        critical_radius=critical,
        number_mean_radius=mean,
        radius_coefficient_of_variation=float(np.std(radii) / mean),
        total_material_volume_proxy=float(np.sum(radii ** 3)),
    )


def simulate_curvature_coarsening(
    initial_radii: Sequence[float],
    *,
    mobility: float,
    maximum_time: float,
    time_step: float,
    target_mean_radius: float | None = None,
    record_every_steps: int = 25,
    dissolution_radius: float = 1e-6,
) -> CoarseningResult:
    """Evolve discrete LSW radii and stop when a requested mean size is reached."""

    initial = np.asarray(initial_radii, dtype=float)
    if initial.ndim != 1 or initial.size < 2 or np.any(initial <= 0) or not np.all(np.isfinite(initial)):
        raise ValueError("initial_radii must contain at least two finite positive radii")
    if mobility <= 0 or maximum_time <= 0 or time_step <= 0 or time_step > maximum_time or dissolution_radius <= 0:
        raise ValueError("mobility, times, and dissolution_radius must be positive")
    if not isinstance(record_every_steps, int) or record_every_steps <= 0:
        raise ValueError("record_every_steps must be a positive integer")
    if target_mean_radius is not None and target_mean_radius <= np.mean(initial):
        raise ValueError("target_mean_radius must exceed the initial number mean")

    radii = initial.copy()
    initial_volume = float(np.sum(initial ** 3))
    states = [_state(0.0, radii)]
    max_volume_error = 0.0
    steps = int(np.ceil(maximum_time / time_step))
    status = "MAXIMUM_TIME_REACHED"
    elapsed = 0.0
    for step in range(1, steps + 1):
        dt = min(time_step, maximum_time - elapsed)
        if dt <= 0:
            break
        critical = float(np.sum(radii ** 2) / np.sum(radii))
        growth = mobility * (1.0 / critical - 1.0 / radii)
        proposed = radii + dt * growth
        radii = proposed[proposed > dissolution_radius]
        if radii.size == 0:
            raise RuntimeError("time step dissolved every particle; reduce time_step")
        raw_volume = float(np.sum(radii ** 3))
        max_volume_error = max(max_volume_error, abs(raw_volume / initial_volume - 1.0))
        radii *= (initial_volume / raw_volume) ** (1.0 / 3.0)
        elapsed += dt
        reached = target_mean_radius is not None and float(np.mean(radii)) >= target_mean_radius
        if step % record_every_steps == 0 or reached or elapsed >= maximum_time - 1e-14:
            states.append(_state(elapsed, radii))
        if reached:
            status = "TARGET_MEAN_RADIUS_REACHED"
            break
    final_volume_error = abs(float(np.sum(radii ** 3)) / initial_volume - 1.0)
    max_volume_error = max(max_volume_error, final_volume_error)
    return CoarseningResult(
        initial_radii=tuple(map(float, initial)),
        final_radii=tuple(map(float, np.sort(radii))),
        states=tuple(states),
        stop_time=float(elapsed),
        dissolved_particle_count=int(initial.size - radii.size),
        initial_mean_radius=float(np.mean(initial)),
        final_mean_radius=float(np.mean(radii)),
        maximum_relative_volume_error=float(max_volume_error),
        target_mean_radius=None if target_mean_radius is None else float(target_mean_radius),
        status=status,
    )
