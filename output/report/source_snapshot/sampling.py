"""Sample an independent signal callable at configurable times."""

import math
from typing import Callable

import numpy as np


# Units: sampling_frequency is in Hz; duration and offset_seconds are in seconds.
def sample_signal(
    signal: Callable[[np.ndarray], np.ndarray],
    sampling_frequency: float,
    duration: float,
    offset_seconds: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Measure a signal and return timestamps in seconds and matching amplitudes."""
    # Check that the supplied signal can be called as a function.
    if not callable(signal):
        raise TypeError("signal must be callable")

    # Check the sampling rate, recording duration, and starting offset.
    if not math.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be positive and finite")
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be positive and finite")
    if (
        not math.isfinite(offset_seconds)
        or not 0 <= offset_seconds < 1 / sampling_frequency
    ):
        raise ValueError("offset_seconds must be in [0, 1 / frequency)")

    # Calculate how many sampling intervals fit after the starting offset.
    sample_span = max(0.0, (duration - offset_seconds) * sampling_frequency)

    # Reject counts that cannot be represented as array indices.
    if not math.isfinite(sample_span) or sample_span >= np.iinfo(np.intp).max:
        raise ValueError("requested sample count is too large")

    # Number the samples, allowing one extra candidate for rounding.
    sample_indices = np.arange(math.ceil(sample_span) + 1, dtype=np.int64)

    # Convert sample numbers to measurement times in seconds.
    times = offset_seconds + sample_indices / sampling_frequency

    # Keep only times before the recording ends, excluding the endpoint.
    times = times[(times >= 0) & (times < duration)]

    # Ask the supplied generator for the amplitude at each sample time.
    amplitudes = np.asarray(signal(times), dtype=float)

    # Check that the signal returned one valid amplitude per timestamp.
    if amplitudes.shape != times.shape:
        raise ValueError("signal must return an array matching the times shape")
    if not np.all(np.isfinite(amplitudes)):
        raise ValueError("signal amplitudes must all be finite")

    return times, amplitudes
