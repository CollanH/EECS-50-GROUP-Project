"""Run one editable fake-signal example through the sampler and BPM detector."""

from detection import estimate_bpm
from reference_signal import rectangular_pulses
from sampling import sample_signal

TRUE_BPM = 120
PULSE_WIDTH_MS = 50
SAMPLING_FREQUENCY_HZ = 200
DURATION_SECONDS = 5
OFFSET_SECONDS = 0.0


def main():
    """Print the measurements and estimate for the settings above."""
    signal = rectangular_pulses(TRUE_BPM, PULSE_WIDTH_MS)
    times, amplitudes = sample_signal(
        signal, SAMPLING_FREQUENCY_HZ, DURATION_SECONDS, OFFSET_SECONDS,
    )
    result = estimate_bpm(amplitudes, SAMPLING_FREQUENCY_HZ)

    print(f"True BPM: {TRUE_BPM}")
    print(f"Sampling frequency: {SAMPLING_FREQUENCY_HZ} Hz")
    print(f"Sample count: {len(times)}")
    print(f"First 5 sample times (seconds): {times[:5]}")
    print(f"First 5 amplitudes: {amplitudes[:5]}")
    print(f"Detected peaks: {result.peak_count}")
    print(f"Estimated BPM: {result.estimated_bpm}")
    print(f"Status: {result.status}")


if __name__ == "__main__":
    main()
