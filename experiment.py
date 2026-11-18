"""Export sampled-pulse cases for Zhengyuan Liu's separate analysis."""

import argparse
import csv
from pathlib import Path
import sys

from detection import estimate_bpm
from reference_signal import rectangular_pulses
from sampling import sample_signal

DEFAULT_BPMS = (60, 90, 120, 150)
DEFAULT_WIDTHS_MS = (25, 50, 100)
DEFAULT_RATES_HZ = (5, 10, 20, 50, 100, 200)
FIELD_NAMES = (
    "true_bpm", "pulse_width_ms", "sampling_frequency_hz", "duration_seconds",
    "offset_fraction", "offset_seconds", "sample_count", "peak_count",
    "estimated_bpm", "detector_status",
)


def run_experiment(output: Path, bpms=DEFAULT_BPMS, widths=DEFAULT_WIDTHS_MS,
                   rates=DEFAULT_RATES_HZ, duration=30.0,
                   offset_count=20) -> int:
    """Write every configured case, including insufficient detections, to CSV.

    Invalid configurations raise ValueError rather than masquerading as valid
    insufficient detections. All cases use the same detector settings.
    """
    if not isinstance(offset_count, int) or offset_count <= 0:
        raise ValueError("offset_count must be a positive integer")
    if not bpms or not widths or not rates:
        raise ValueError("parameter grids must not be empty")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        for bpm in bpms:
            for width in widths:
                fixture = rectangular_pulses(bpm, width)
                for rate in rates:
                    # Validate rate and duration before computing offset/rate.
                    sample_signal(fixture, rate, duration)
                    for k in range(offset_count):
                        fraction = k / offset_count
                        offset = fraction / rate
                        times, values = sample_signal(
                            fixture, rate, duration, offset)
                        result = estimate_bpm(values, rate)
                        writer.writerow(dict(zip(FIELD_NAMES, (
                            bpm, width, rate, duration, fraction, offset,
                            len(times), result.peak_count,
                            result.estimated_bpm, result.status,
                        ))))
                        count += 1
    return count


def main():
    """Run a configurable reference-fixture grid from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path("results/experiment.csv"))
    parser.add_argument("--bpms", nargs="+", type=float, default=DEFAULT_BPMS)
    parser.add_argument("--widths-ms", nargs="+", type=float,
                        default=DEFAULT_WIDTHS_MS)
    parser.add_argument("--rates-hz", nargs="+", type=float,
                        default=DEFAULT_RATES_HZ)
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--offset-count", type=int, default=20)
    args = parser.parse_args()
    try:
        count = run_experiment(args.output, args.bpms, args.widths_ms,
                               args.rates_hz, args.duration, args.offset_count)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Wrote {count} cases to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
