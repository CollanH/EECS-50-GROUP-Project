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
    Times within four floating-point spacings of a boundary are treated as
    that boundary: starts are included and ends are excluded. This resolves
    rounding between equivalent time calculations. Width must be less than a period.
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
        # Check adjacent beats because division can round across a beat index.
        for shift in (-1, 0, 1):
            candidate = beat_index + shift
            start = first_beat_seconds + candidate * period
            end = start + width

            # Snap only rounding-sized differences, not a fraction of a sample.
            time_scale = np.maximum(1.0, np.maximum(np.abs(start), np.abs(end)))
            time_scale = np.maximum(time_scale, np.abs(times))
            boundary_tolerance = 4 * np.spacing(time_scale)
            at_start = np.abs(times - start) <= boundary_tolerance
            at_end = np.abs(times - end) <= boundary_tolerance
            high |= (
                (candidate >= 0)
                & ((times >= start) | at_start)
                & (times < end)
                & ~at_end
            )
        return high.astype(float)

    return evaluate
