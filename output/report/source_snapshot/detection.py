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


# Units: sampling_frequency is in Hz; estimated BPM is in beats per minute.
def estimate_bpm(
    amplitudes: np.ndarray,
    sampling_frequency: float,
) -> DetectionResult:
    """Estimate BPM from the median time between detected peaks."""
    # Check the sampling rate before converting sample positions to seconds.
    if not math.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be positive and finite")

    # Check that the measurements form one array of finite amplitudes.
    sample_values = np.asarray(amplitudes, dtype=float)
    if sample_values.ndim != 1 or not np.all(np.isfinite(sample_values)):
        raise ValueError("amplitudes must be a finite one-dimensional array")

    # Use the same unfiltered detector for every case. Flat peaks count once;
    # their midpoint is rounded down, and endpoint peaks are excluded.
    peak_indices, _ = signal.find_peaks(sample_values)

    # Convert peak positions to seconds relative to the first sample.
    peak_times_seconds = peak_indices / sampling_frequency
    peak_count = len(peak_indices)

    # At least two peaks are needed to measure a time interval.
    if peak_count < 2:
        return DetectionResult(
            estimated_bpm=None,
            peak_indices=peak_indices,
            peak_count=peak_count,
            status="insufficient_peaks",
            peak_times_seconds=peak_times_seconds,
        )

    # Convert the median interval in seconds to beats per minute.
    peak_intervals_seconds = np.diff(peak_times_seconds)
    estimated_bpm = float(60 / np.median(peak_intervals_seconds))

    # 'ok' means enough peaks were found; missed beats can still bias the BPM.
    return DetectionResult(
        estimated_bpm=estimated_bpm,
        peak_indices=peak_indices,
        peak_count=peak_count,
        status="ok",
        peak_times_seconds=peak_times_seconds,
    )
