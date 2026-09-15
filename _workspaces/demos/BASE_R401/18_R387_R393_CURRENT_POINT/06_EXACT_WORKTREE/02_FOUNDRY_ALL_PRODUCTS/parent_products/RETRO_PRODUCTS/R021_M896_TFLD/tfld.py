"""Time-Frequency Localization Designer (TFLD) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np
from scipy.signal import windows


@dataclass(frozen=True)
class WindowCandidate:
    window_type: str
    samples: int
    duration_seconds: float
    time_spread_seconds: float
    frequency_spread_hz: float
    uncertainty_product: float
    bin_spacing_hz: float
    equivalent_noise_bandwidth_hz: float
    time_requirement_ratio: float
    frequency_requirement_ratio: float
    feasible: bool
    violation_score: float


@dataclass(frozen=True)
class LocalizationDesign:
    sample_rate_hz: float
    maximum_time_spread_seconds: float
    maximum_frequency_spread_hz: float
    selected: WindowCandidate
    feasible_candidate_count: int
    candidates: tuple[WindowCandidate, ...]
    status: str

    def to_dict(self) -> dict:
        payload=asdict(self); payload["selected"]=asdict(self.selected); payload["candidates"]=[asdict(x) for x in self.candidates]; return payload


def _window(kind: str, length: int) -> np.ndarray:
    if kind == "HANN": return windows.hann(length, sym=False)
    if kind == "HAMMING": return windows.hamming(length, sym=False)
    if kind == "GAUSSIAN": return windows.gaussian(length, std=length/6, sym=False)
    if kind == "BOXCAR": return np.ones(length)
    raise ValueError(f"unsupported window type: {kind}")


def design_localization(
    *, sample_rate_hz: float, maximum_time_spread_seconds: float, maximum_frequency_spread_hz: float,
    window_lengths: Sequence[int], window_types: Sequence[str] = ("HANN","HAMMING","GAUSSIAN"),
    fft_oversampling: int = 32,
) -> LocalizationDesign:
    if not all(np.isfinite(x) and x>0 for x in (sample_rate_hz,maximum_time_spread_seconds,maximum_frequency_spread_hz)):
        raise ValueError("sample rate and localization limits must be finite and positive")
    lengths=tuple(window_lengths); kinds=tuple(str(x).upper() for x in window_types)
    if not lengths or any(not isinstance(n,int) or n<4 for n in lengths) or not kinds or fft_oversampling<4:
        raise ValueError("provide window lengths >=4, window types, and FFT oversampling >=4")
    rows=[]
    for kind in kinds:
        for length in lengths:
            w=_window(kind,length); energy=w*w; energy/=np.sum(energy)
            time=(np.arange(length)-(length-1)/2)/sample_rate_hz
            time_spread=float(np.sqrt(np.sum(energy*time*time)))
            nfft=int(2**np.ceil(np.log2(length*fft_oversampling)))
            spectrum=np.abs(np.fft.fftshift(np.fft.fft(w,nfft)))**2; spectrum/=np.sum(spectrum)
            frequencies=np.fft.fftshift(np.fft.fftfreq(nfft,d=1/sample_rate_hz))
            frequency_spread=float(np.sqrt(np.sum(spectrum*frequencies*frequencies)))
            enbw=float(sample_rate_hz*np.sum(w*w)/(np.sum(w)**2))
            tr=time_spread/maximum_time_spread_seconds; fr=frequency_spread/maximum_frequency_spread_hz
            feasible=tr<=1+1e-12 and fr<=1+1e-12
            violation=float(max(1,tr)**2+max(1,fr)**2-2)
            rows.append(WindowCandidate(kind,length,length/sample_rate_hz,time_spread,frequency_spread,
                time_spread*frequency_spread,sample_rate_hz/length,enbw,tr,fr,feasible,violation))
    feasible=[x for x in rows if x.feasible]
    selected=min(feasible,key=lambda x:(x.uncertainty_product,x.samples)) if feasible else min(rows,key=lambda x:(x.violation_score,x.uncertainty_product))
    return LocalizationDesign(float(sample_rate_hz),float(maximum_time_spread_seconds),float(maximum_frequency_spread_hz),
                              selected,len(feasible),tuple(rows),"FEASIBLE_DESIGN_FOUND" if feasible else "JOINT_REQUIREMENT_NOT_MET")
