"""Synthetic test fixture only; does not replace Matthew Tao's generator."""

import math
from typing import Callable

import numpy as np


def rectangular_pulses(
    bpm: float,
    pulse_width_ms: float,
    first_beat_seconds: float = 0.0,
) -> Callable[[np.ndarray], np.ndarray]:
    """Return noise-free unit pulses on [beat_start, beat_start + width).

    Beat k starts at first_beat_seconds + k * (60 / bpm), for k >= 0.
    Direct comparisons use floating-point beat starts, with no interpolation
    or tolerance expansion of pulse intervals. Width must be less than a period.
    """
    if not math.isfinite(bpm) or bpm <= 0:
        raise ValueError("bpm must be positive and finite")
    if not math.isfinite(pulse_width_ms) or not 0 < pulse_width_ms / 1000 < 60 / bpm:
        raise ValueError("pulse width must be positive and less than a period")
    if not math.isfinite(first_beat_seconds):
        raise ValueError("first_beat_seconds must be finite")
    period = 60 / bpm
    width = pulse_width_ms / 1000

    def evaluate(times: np.ndarray) -> np.ndarray:
        """Evaluate pulses directly at each supplied time in seconds."""
        times = np.asarray(times, dtype=float)
        if times.ndim != 1 or not np.all(np.isfinite(times)):
            raise ValueError("times must be a finite one-dimensional array")
        beat_index = np.floor((times - first_beat_seconds) / period)
        high = np.zeros(times.shape, dtype=bool)
        # Adjacent candidates resolve floating division rounding at beat starts.
        for shift in (-1, 0, 1):
            candidate = beat_index + shift
            start = first_beat_seconds + candidate * period
            high |= ((candidate >= 0) & (times >= start)
                     & (times < start + width))
        return high.astype(float)

    return evaluate
