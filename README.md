# Effects of Sampling Rate on BPM Detection Accuracy

Collan Stephen Harrington's sampling and peak detection components for EECS 50.
Matthew Tao owns the project rhythm generator. Zhengyuan Liu owns error analysis,
plots comparing estimates to ground truth, and optimization. The reference pulse
fixture here supports independent validation and is not Matthew's contribution.

## Setup and commands

Use Python 3.10 or newer from this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python demo.py
python experiment.py
```

Once dependencies are installed, tests, demo, and experiments run offline without
external audio files or Matthew's code. The single independent harness command is
`python -m unittest discover -s tests -v`.

The demo writes `results/demo.png`. The default experiment writes
`results/experiment.csv` with exactly 1,440 data rows plus a header:
4 BPMs (60, 90, 120, 150) × 3 widths (25, 50, 100 ms) × 6 rates
(5, 10, 20, **50**, 100, 200 Hz) × 20 offsets. Defaults are 30 seconds and
fractions k/20 for k=0,...,19, with offset_seconds = fraction / rate.
These duration and offset defaults are configurable implementation choices.

```sh
python demo.py --duration 8 --output results/custom_demo.png
python experiment.py --bpms 60 120 --widths-ms 25 100 --rates-hz 5 50 200 \
    --duration 10 --offset-count 10 --output results/custom_experiment.csv
```

Invalid CLI configurations produce diagnostics on stderr and exit nonzero.
The CSV preserves every valid case, including insufficient detections, using:
`true_bpm,pulse_width_ms,sampling_frequency_hz,duration_seconds,offset_fraction,offset_seconds,sample_count,peak_count,estimated_bpm,detector_status`.
Insufficient detections have an empty estimate field. Invalid configurations raise
an error instead of being labeled as insufficient observations.

## Modules and team integration

- `sampling.py`: callable-based sampling, timestamps, and input validation.
- `detection.py`: SciPy peak baseline and `DetectionResult`.
- `reference_signal.py`: clearly labeled rectangular-pulse test fixture.
- `tests/test_core.py`: deterministic independent harness.
- `demo.py`: reference curve, actual observations, and observed peaks.
- `experiment.py`: configurable CSV support for Zhengyuan's separate analysis.

Matthew can supply any callable that takes a one-dimensional NumPy time array
in seconds and returns a matching finite amplitude array. For example:

```python
import numpy as np
from sampling import sample_signal
from detection import estimate_bpm

# Independent callable example; replace this with Matthew's signal or adapter.
def matthew_signal(times):
    return np.cos(2 * np.pi * times)

times, amplitudes = sample_signal(matthew_signal, 100, 30, 0.002)
result = estimate_bpm(amplitudes, 100)
absolute_peak_times = times[result.peak_indices]
print(result.estimated_bpm, result.status)
```

The cosine above demonstrates integration only. The pulse fixture is not imported
by the sampler or detector. If Matthew provides only amplitude samples, obtain
matching timestamps, or the original sampling rate **and time origin**, before
building an adapter. Agree on interpolation and out-of-range behavior explicitly;
do not infer timestamps or silently introduce another sampling step.

## Sampling and detector conventions

Sampling uses `offset_seconds + integer_index / sampling_frequency` and retains
only timestamps in [0, duration). The frequency and duration must be positive
and finite; the offset must be finite and satisfy 0 <= offset < 1/frequency.
Empty samples are possible when the recording ends before the first sample.
Signal output must match the timestamp array shape and contain finite values.
Integer indices avoid accumulating a floating-point step.

The detector accepts only sampled amplitudes and frequency. It never sees BPM,
pulse width, beat times, offsets, or a generator. It calls `scipy.signal.find_peaks`
with default settings: no height, prominence, distance, or width restrictions.
Settings are consistent for every case; no ground-truth tuning or half/double-time
correction is applied. No time threshold needs conversion to samples.

A flat top produces a single midpoint peak (rounded down for an even number of
samples). Peaks need lower neighbors on both sides. A high pulse touching the
first or last sample is excluded, including a plateau touching an endpoint.
No synthetic padding is added and no endpoint is counted as an observed beat.

Peak times returned by the detector are `peak_index / frequency`, relative to
the first sample. Absolute plot locations use `times[peak_indices]`, including
the sampling offset. With two or more peaks, BPM = 60 / median(diff(peak_times)).
Fewer than two peaks returns status `insufficient_peaks` and estimate `None`.
Invalid input raises an exception. Status `ok` means enough peaks were found;
it does not guarantee the right BPM. Missing alternate beats can produce a
half-time estimate, and noise could add spurious peaks with this simple baseline.

The fixture evaluates unit rectangular pulses directly at supplied times,
with baseline zero and half-open intervals [start, start + width). Beat k starts
at first_beat_seconds + k × (60/BPM), k >= 0. First-beat time is configurable.
There is no coarse waveform interpolation or noise. Boundary comparisons use
ordinary floating-point arithmetic without expanding intervals by a tolerance;
values extremely close to mathematical boundaries may depend on representation.

## Validation and actual observations

Validated November 17, 2026 with Python 3, NumPy 2.4.0, SciPy 1.17.0, and
Matplotlib 3.10.8. All 11 test methods passed, including parameterized coverage of
all 12 BPM/width combinations at 200 Hz, complete misses versus aligned low-rate
sampling, flat tops, zero/one-peak recordings, boundaries, invalid inputs,
half-open pulse intervals, and an independently defined callable.

The favorable-grid tolerance is 4 BPM. Before examining errors, a conservative
2-sample-period bound on midpoint interval quantization gives at 200 Hz and the
shortest period (0.4 s): 60/(0.4 - 2/200) - 150 < 3.85 BPM. Four BPM rounds that
bound upward; it applies to favorable detection with all interior pulses sampled,
not to missed pulses or arbitrary signals.

The generated five-second demo gives:

| Case | Estimate | Peaks | Status |
| --- | ---: | ---: | --- |
| 120 BPM, 50 ms, 200 Hz, offset 0 s | 120 BPM | 9 | ok |
| 60 BPM, 25 ms, 5 Hz, offset 0.1 s | empty | 0 | insufficient_peaks |
| Same low-rate signal, offset 0 s | 60 BPM | 4 | ok |

The full default CSV contains 1,440 data rows: 1,211 `ok` and 229
`insufficient_peaks`. Verified empty estimate fields for every insufficient case.

| Sampling rate (Hz) | Numeric estimates | Insufficient | Largest absolute error among numeric estimates (BPM) |
| ---: | ---: | ---: | ---: |
| 5 | 118 | 122 | 75.0000 |
| 10 | 162 | 78 | 75.0000 |
| 20 | 211 | 29 | 75.0000 |
| 50 | 240 | 0 | 0.9091 |
| 100 | 240 | 0 | 0.4478 |
| 200 | 240 | 0 | 0.2256 |

These observations describe this grid only; they do not establish monotonic
accuracy for every offset or waveform. The experiment studies idealized beat
pulses, not raw music audio. Rectangular pulses are not band-limited, and Nyquist
alone does not guarantee reliable pulse detection. Noise robustness, complex
rhythms, audio onset detection, and optimization remain outside this baseline.

## Technical references

- [SciPy find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html): local maxima, flat tops, and detector options.
- [NumPy arange](https://numpy.org/doc/stable/reference/generated/numpy.arange.html): integer-index arrays and floating-step caveats.
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html): Python naming, docstrings, and code conventions.
