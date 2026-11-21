"""Visualize favorable detection and complete pulse misses using test fixtures."""

import argparse
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from detection import estimate_bpm
from reference_signal import rectangular_pulses
from sampling import sample_signal


def make_demo(output: Path, duration: float = 5.0):
    """Save three alignment examples; detection uses sampled values only."""
    cases = ((120, 50, 200, 0.0, "Favorable detection"),
             (60, 25, 5, 0.1, "Complete pulse misses"),
             (60, 25, 5, 0.0, "Same low rate, favorable alignment"))
    figure, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    for axis, (bpm, width, rate, offset, label) in zip(axes, cases):
        fixture = rectangular_pulses(bpm, width)
        times, values = sample_signal(fixture, rate, duration, offset)
        result = estimate_bpm(values, rate)
        # This dense curve is a visual aid, never detector input.
        dense_times = np.linspace(0, duration, int(duration * 2000) + 1)
        axis.plot(dense_times, fixture(dense_times), color="0.65",
                  linewidth=1.2, label="Reference waveform (fixture)")
        axis.plot(times, values, ".", color="#1768ac", markersize=5,
                  label="Actual sampled points")
        axis.plot(times[result.peak_indices], values[result.peak_indices],
                  "x", color="#bd3518", markersize=8, label="Detected peaks")
        estimate = ("none" if result.estimated_bpm is None
                    else f"{result.estimated_bpm:.2f}")
        axis.set_title(f"{label}: true {bpm} BPM | {rate} Hz | {width} ms | "
                       f"offset {offset:g} s\n"
                       f"estimate {estimate} BPM | {result.status} | "
                       f"{result.peak_count} peaks", fontsize=10)
        axis.set_ylabel("Amplitude")
        axis.set_ylim(-0.15, 1.2)
        axis.grid(alpha=0.2)
        print(f"{label}: estimate={estimate}, status={result.status}, "
              f"peaks={result.peak_count}", file=sys.stderr)
    axes[0].legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("Absolute time (seconds, including sampling offset)")
    # Show the full recording so the displayed peaks match the reported count.
    axes[-1].set_xlim(0, duration)
    figure.tight_layout()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=160)
    plt.close(figure)
    print(f"Saved {output}", file=sys.stderr)


def main():
    """Run the standalone demo without Matthew's code or external audio."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/demo.png"))
    parser.add_argument("--duration", type=float, default=5)
    args = parser.parse_args()
    try:
        make_demo(args.output, args.duration)
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
