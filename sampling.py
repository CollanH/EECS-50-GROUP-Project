"""Sample an independent signal callable at configurable times."""

import math
from typing import Callable

import numpy as np


def sample_signal(
    signal: Callable[[np.ndarray], np.ndarray],
    sampling_frequency: float,
    duration: float,
    offset_seconds: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return times in [0, duration) and matching finite signal amplitudes.

    Args:
        signal: Callable mapping a 1-D time array in seconds to amplitudes.
        sampling_frequency: Positive, finite samples per second.
        duration: Positive, finite observation duration in seconds.
        offset_seconds: Finite offset in [0, 1 / sampling_frequency).

    Raises:
        ValueError: Parameters or signal output are invalid.
        TypeError: Signal is not callable.
    """
    if not callable(signal):
        raise TypeError("signal must be callable")
    if not math.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be positive and finite")
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be positive and finite")
    if (not math.isfinite(offset_seconds)
            or not 0 <= offset_seconds < 1 / sampling_frequency):
        raise ValueError("offset_seconds must be in [0, 1 / frequency)")
    span = max(0.0, (duration - offset_seconds) * sampling_frequency)
    if not math.isfinite(span) or span >= np.iinfo(np.intp).max:
        raise ValueError("requested sample count is too large")
    # One extra candidate guards against rounding in the count calculation.
    indices = np.arange(math.ceil(span) + 1, dtype=np.int64)
    times = offset_seconds + indices / sampling_frequency
    times = times[(times >= 0) & (times < duration)]
    amplitudes = np.asarray(signal(times), dtype=float)
    if amplitudes.shape != times.shape:
        raise ValueError("signal must return an array matching the times shape")
    if not np.all(np.isfinite(amplitudes)):
        raise ValueError("signal amplitudes must all be finite")
    return times, amplitudes
