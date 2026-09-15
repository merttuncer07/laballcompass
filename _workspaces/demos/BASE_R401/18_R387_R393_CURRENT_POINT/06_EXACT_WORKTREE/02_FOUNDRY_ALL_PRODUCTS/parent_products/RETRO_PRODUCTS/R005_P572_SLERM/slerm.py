"""Synchronization Lock-in and Energy-transfer Risk Monitor (SLERM) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class LockInWindow:
    start_time: float
    end_time: float
    forcing_frequency: float
    response_frequency: float
    relative_detuning: float
    phase_locking_value: float
    response_rms: float
    mean_energy_transfer_rate: float
    normalized_energy_transfer: float
    locked: bool
    dangerous: bool


@dataclass(frozen=True)
class LockInMonitorResult:
    windows: tuple[LockInWindow, ...]
    locked_window_fraction: float
    dangerous_window_fraction: float
    maximum_consecutive_dangerous_duration: float
    peak_response_rms: float
    peak_mean_energy_transfer_rate: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _dominant_frequency(signal: np.ndarray, sample_rate: float) -> float:
    centered = signal - signal.mean()
    spectrum = np.abs(np.fft.rfft(centered))
    frequencies = np.fft.rfftfreq(centered.size, 1.0 / sample_rate)
    spectrum[0] = 0.0
    return float(frequencies[int(np.argmax(spectrum))])


def _analytic_phase(signal: np.ndarray, center_frequency: float, sample_rate: float) -> np.ndarray:
    centered = signal - signal.mean()
    frequencies = np.fft.fftfreq(centered.size, 1.0 / sample_rate)
    width = max(sample_rate / centered.size * 2.5, center_frequency * 0.12)
    filtered_spectrum = np.fft.fft(centered)
    keep = np.abs(np.abs(frequencies) - center_frequency) <= width
    band = np.fft.ifft(filtered_spectrum * keep).real
    spectrum = np.fft.fft(band)
    multiplier = np.zeros(centered.size)
    multiplier[0] = 1
    if centered.size % 2 == 0:
        multiplier[1:centered.size // 2] = 2; multiplier[centered.size // 2] = 1
    else:
        multiplier[1:(centered.size + 1) // 2] = 2
    analytic = np.fft.ifft(spectrum * multiplier)
    return np.angle(analytic)


def monitor_lock_in(
    forcing: Sequence[float],
    displacement_response: Sequence[float],
    *,
    sample_rate: float,
    window_samples: int,
    step_samples: int,
    maximum_relative_detuning: float = 0.05,
    minimum_phase_locking: float = 0.8,
    dangerous_response_rms: float,
    minimum_normalized_energy_transfer: float = 0.25,
) -> LockInMonitorResult:
    """Monitor synchronization and actual force-to-structure work in overlapping windows."""

    force = np.asarray(forcing, dtype=float); displacement = np.asarray(displacement_response, dtype=float)
    if force.ndim != 1 or displacement.shape != force.shape or force.size < 8 or not np.all(np.isfinite(force)) or not np.all(np.isfinite(displacement)):
        raise ValueError("forcing and displacement must be matching finite vectors")
    if sample_rate <= 0 or not isinstance(window_samples, int) or not isinstance(step_samples, int) or window_samples < 8 or step_samples <= 0 or window_samples > force.size:
        raise ValueError("invalid sample rate or window geometry")
    if maximum_relative_detuning < 0 or not 0 <= minimum_phase_locking <= 1 or dangerous_response_rms <= 0 or not -1 <= minimum_normalized_energy_transfer <= 1:
        raise ValueError("invalid monitor thresholds")

    records: list[LockInWindow] = []
    for start in range(0, force.size - window_samples + 1, step_samples):
        stop = start + window_samples
        f = force[start:stop]; x = displacement[start:stop]
        velocity = np.gradient(x) * sample_rate
        forcing_frequency = _dominant_frequency(f, sample_rate)
        response_frequency = _dominant_frequency(x, sample_rate)
        detuning = float("inf") if forcing_frequency <= 0 else abs(response_frequency - forcing_frequency) / forcing_frequency
        force_phase = _analytic_phase(f, forcing_frequency, sample_rate)
        velocity_phase = _analytic_phase(velocity, forcing_frequency, sample_rate)
        phase_locking = float(abs(np.mean(np.exp(1j * (force_phase - velocity_phase)))))
        response_rms = float(np.sqrt(np.mean((x - x.mean()) ** 2)))
        power = float(np.mean(f * velocity))
        denominator = float(np.sqrt(np.mean(f ** 2)) * np.sqrt(np.mean(velocity ** 2)))
        normalized = 0.0 if denominator <= 1e-15 else power / denominator
        locked = detuning <= maximum_relative_detuning and phase_locking >= minimum_phase_locking
        dangerous = locked and response_rms >= dangerous_response_rms and normalized >= minimum_normalized_energy_transfer
        records.append(LockInWindow(
            start_time=start / sample_rate,
            end_time=stop / sample_rate,
            forcing_frequency=forcing_frequency,
            response_frequency=response_frequency,
            relative_detuning=detuning,
            phase_locking_value=phase_locking,
            response_rms=response_rms,
            mean_energy_transfer_rate=power,
            normalized_energy_transfer=float(normalized),
            locked=locked,
            dangerous=dangerous,
        ))
    dangerous_run = current_run = 0
    for record in records:
        current_run = current_run + 1 if record.dangerous else 0
        dangerous_run = max(dangerous_run, current_run)
    fraction_locked = sum(record.locked for record in records) / len(records)
    fraction_dangerous = sum(record.dangerous for record in records) / len(records)
    if fraction_dangerous > 0:
        status = "ENERGY_TRANSFERRING_LOCK_IN_DETECTED"
    elif fraction_locked > 0:
        status = "FREQUENCY_LOCK_WITHOUT_DANGEROUS_TRANSFER"
    else:
        status = "NO_LOCK_IN_DETECTED"
    return LockInMonitorResult(
        windows=tuple(records),
        locked_window_fraction=float(fraction_locked),
        dangerous_window_fraction=float(fraction_dangerous),
        maximum_consecutive_dangerous_duration=float(dangerous_run * step_samples / sample_rate),
        peak_response_rms=max(record.response_rms for record in records),
        peak_mean_energy_transfer_rate=max(record.mean_energy_transfer_rate for record in records),
        status=status,
    )
