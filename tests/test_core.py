"""Deterministic independent validation, runnable without network access."""

import unittest

import numpy as np

from detection import estimate_bpm
from reference_signal import rectangular_pulses
from sampling import sample_signal


class SamplingDetectionTest(unittest.TestCase):
    """Exercise analytic expectations rather than generator implementation."""

    def test_favorable_grid(self):
        # Midpoint quantization bounds interval error by <= 2 sample periods.
        # At 200 Hz and shortest period .4 s this implies < 3.85 BPM error.
        for bpm in (60, 90, 120, 150):
            for width in (25, 50, 100):
                with self.subTest(bpm=bpm, width=width):
                    _, values = sample_signal(
                        rectangular_pulses(bpm, width), 200, 30)
                    result = estimate_bpm(values, 200)
                    self.assertEqual(result.status, "ok")
                    self.assertLessEqual(abs(result.estimated_bpm - bpm), 4)

    def test_complete_miss_and_alignment(self):
        fixture = rectangular_pulses(60, 25)
        _, missed = sample_signal(fixture, 5, 5, 0.1)
        np.testing.assert_array_equal(missed, np.zeros(25))
        result = estimate_bpm(missed, 5)
        self.assertEqual(result.status, "insufficient_peaks")
        self.assertIsNone(result.estimated_bpm)
        _, aligned = sample_signal(fixture, 5, 5, 0)
        result = estimate_bpm(aligned, 5)
        np.testing.assert_array_equal(result.peak_indices, [5, 10, 15, 20])
        self.assertAlmostEqual(result.estimated_bpm, 60)

    def test_plateaus(self):
        result = estimate_bpm([0, 1, 1, 1, 0, 0, 1, 1, 0], 10)
        np.testing.assert_array_equal(result.peak_indices, [2, 6])
        self.assertEqual(result.peak_count, 2)
        self.assertAlmostEqual(result.estimated_bpm, 150)

    def test_insufficient(self):
        for values in ([], [0], np.zeros(10), [0, 1, 1, 0]):
            with self.subTest(values=values):
                result = estimate_bpm(values, 10)
                self.assertIsNone(result.estimated_bpm)
                self.assertEqual(result.status, "insufficient_peaks")

    def test_boundaries(self):
        for values in ([1, 0, 0], [0, 0, 1], [1, 1, 0, 0, 1, 1]):
            self.assertEqual(estimate_bpm(values, 10).peak_count, 0)
        result = estimate_bpm([1, 1, 0, 1, 0, 1, 1], 10)
        np.testing.assert_array_equal(result.peak_indices, [3])
        self.assertEqual(result.status, "insufficient_peaks")

    def test_independent_callable_and_timestamps(self):
        def independent_signal(times):
            return 2 * times + 1
        times, values = sample_signal(independent_signal, 4, 1, 0.125)
        np.testing.assert_array_equal(times, [0.125, 0.375, 0.625, 0.875])
        np.testing.assert_array_equal(values, [1.25, 1.75, 2.25, 2.75])
        times, values = sample_signal(
            lambda t: np.cos(2 * np.pi * t), 20, 4, 0.025)
        result = estimate_bpm(values, 20)
        np.testing.assert_allclose(
            times[result.peak_indices], result.peak_times_seconds + 0.025)

    def test_half_open_sampling_and_short_duration(self):
        times, _ = sample_signal(np.zeros_like, 10, 1)
        self.assertEqual(len(times), 10)
        self.assertTrue(np.all(times < 1))
        times, values = sample_signal(np.zeros_like, 10, 0.01, 0.05)
        self.assertEqual(len(times), 0)
        self.assertEqual(len(values), 0)

    def test_invalid_sampling_parameters(self):
        for invalid in (0, -1, np.nan, np.inf, -np.inf):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    sample_signal(np.zeros_like, invalid, 1)
                with self.assertRaises(ValueError):
                    sample_signal(np.zeros_like, 10, invalid)
                with self.assertRaises(ValueError):
                    estimate_bpm([0, 1, 0], invalid)
        for offset in (-0.1, 0.1, np.nan, np.inf):
            with self.assertRaises(ValueError):
                sample_signal(np.zeros_like, 10, 1, offset)
        with self.assertRaises(TypeError):
            sample_signal([0, 1], 10, 1)

    def test_invalid_data(self):
        for values in ([[0, 1]], [0, np.nan], [np.inf]):
            with self.assertRaises(ValueError):
                estimate_bpm(values, 10)
        for invalid_signal in (lambda t: 1, lambda t: np.zeros((len(t), 1)),
                               lambda t: np.full(t.shape, np.inf)):
            with self.assertRaises(ValueError):
                sample_signal(invalid_signal, 10, 1)

    def test_reference_half_open_intervals(self):
        fixture = rectangular_pulses(60, 25, 0.5)
        times = [0.499, 0.5, 0.524, 0.525, 1.499, 1.5, 1.525]
        np.testing.assert_array_equal(fixture(times), [0, 1, 1, 0, 0, 1, 0])
        for args in ((0, 25), (60, 0), (60, 1000), (np.nan, 25),
                     (60, np.inf), (60, 25, np.nan)):
            with self.assertRaises(ValueError):
                rectangular_pulses(*args)

    def test_missed_beats_can_yield_wrong_numeric_estimate(self):
        # Observed peaks spaced two seconds apart: detector cannot infer misses.
        result = estimate_bpm([0, 1, 0, 0, 0, 1, 0], 2)
        self.assertEqual(result.status, "ok")
        self.assertAlmostEqual(result.estimated_bpm, 30)

    def test_aligned_150_bpm_pulses_are_not_lost_to_rounding(self):
        # 150 BPM has a .4 s period, aligned with every other 5 Hz sample.
        _, values = sample_signal(rectangular_pulses(150, 25), 5, 30)
        np.testing.assert_array_equal(values[::2], np.ones(75))
        np.testing.assert_array_equal(values[1::2], np.zeros(75))
        result = estimate_bpm(values, 5)
        self.assertEqual(result.peak_count, 74)
        self.assertAlmostEqual(result.estimated_bpm, 150)

    def test_repeated_pulse_starts_and_ends(self):
        # Equivalent calculations must agree on inclusive starts and exclusive ends.
        for bpm in (60, 90, 120, 150):
            with self.subTest(bpm=bpm):
                fixture = rectangular_pulses(bpm, 25, 0.125)
                starts = 0.125 + np.arange(100) * 60 / bpm
                np.testing.assert_array_equal(fixture(starts), np.ones(100))
                np.testing.assert_array_equal(fixture(starts + 0.025), np.zeros(100))

    def test_boundary_snapping_does_not_extend_pulses_by_a_sample(self):
        fixture = rectangular_pulses(60, 25, 0.5)
        # Adjacent floating-point numbers are ambiguous; a 1 ns gap is not.
        times = [
            0.5 - 1e-9, np.nextafter(0.5, -np.inf), 0.5,
            0.525 - 1e-9, np.nextafter(0.525, -np.inf), 0.525,
            0.525 + 1e-9,
        ]
        np.testing.assert_array_equal(fixture(times), [0, 1, 1, 1, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
