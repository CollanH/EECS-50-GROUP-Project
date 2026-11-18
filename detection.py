"""Simple BPM baseline; no ground truth or generator information is used."""

from dataclasses import dataclass
import math

import numpy as np
from scipy import signal


@dataclass(frozen=True)
class DetectionResult:
    """BPM estimate and observed peaks; peak times start at the first sample."""

    estimated_bpm: float | None
    peak_indices: np.ndarray
    peak_count: int
    status: str
    peak_times_seconds: np.ndarray


def estimate_bpm(amplitudes: np.ndarray,
                 sampling_frequency: float) -> DetectionResult:
    """Estimate BPM as 60 / median interval between interior local peaks.

    Flat plateaus produce one peak at their midpoint, rounded down. Endpoint
    plateaus are excluded because both surrounding lower samples are needed.
    No padding, height, prominence, distance, or width filters are used. Thus no
    seconds-to-samples threshold conversion is needed. These settings remain
    identical for every experiment. Missed beats can yield a numeric but wrong
    estimate; status 'ok' indicates enough peaks, not guaranteed accuracy.

    Args:
        amplitudes: Finite 1-D sampled values; an empty array is valid.
        sampling_frequency: Positive finite samples per second.

    Raises:
        ValueError: Data or sampling frequency is invalid.
    """
    if not math.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be positive and finite")
    values = np.asarray(amplitudes, dtype=float)
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise ValueError("amplitudes must be a finite one-dimensional array")
    peaks, _ = signal.find_peaks(values)
    peak_times = peaks / sampling_frequency
    if len(peaks) < 2:
        return DetectionResult(None, peaks, len(peaks), "insufficient_peaks",
                               peak_times)
    bpm = float(60 / np.median(np.diff(peak_times)))
    return DetectionResult(bpm, peaks, len(peaks), "ok", peak_times)
