# Effects of Sampling Rate on BPM Detection Accuracy

This project investigates how sampling frequency affects a peak-based BPM detector.
It currently uses a fake rectangular-pulse signal so sampling and detection can be
tested before the team generator is connected. It does not record a microphone or
process a music file.

**Progress-report status:** sampling, detection, independent tests, and a demo are
implemented. Team-generator integration and full accuracy analysis are future work.

## Start here

```text
Fake signal (later Matthew's generator)
    -> sampler: timestamps and amplitudes
    -> detector: peaks and estimated BPM
```

- **Collan:** sampling and BPM estimation, in `sampling.py` and `detection.py`.
- **Matthew:** team signal generation. `reference_signal.py` is a test fixture.
- **Zhengyuan:** error analysis, comparison plots, and optimization.

## Download and setup

Install Python 3.10 or newer. Clone the repo, or use GitHub's **Code -> Download
ZIP**, extract it, and open that folder in VS Code. Select **Terminal -> New
Terminal**. Commands must run from the folder containing `requirements.txt`.

```sh
git clone https://github.com/CollanH/EECS-50-GROUP-Project.git
cd EECS-50-GROUP-Project
```

On macOS or Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For subsequent commands, Windows users can replace `python` with
`.\.venv\Scripts\python.exe`. Select the `.venv` Python interpreter in VS Code
if prompted. The first install needs package-registry access; examples run offline
after installation, without Matthew's code or external audio files.

## Run one editable example

```sh
python example.py
```

Expected output with the unchanged settings:

```text
True BPM: 120
Sampling frequency: 200 Hz
Sample count: 1000
First 5 sample times (seconds): [0.    0.005 0.01  0.015 0.02 ]
First 5 amplitudes: [1. 1. 1. 1. 1.]
Detected peaks: 9
Estimated BPM: 120.0
Status: ok
```

Edit the constants at the top of `example.py` to try other conditions. For an
alignment comparison, use 60 BPM, 25 ms pulses, 5 Hz, and 5 seconds. Offset `0.0`
gives 60 BPM and four peaks. Offset `0.1` gives `None`, zero peaks, and
`insufficient_peaks`. At 5 Hz, measurements are 0.2 seconds apart.

## Run the visual demo

```sh
python demo.py
```

Expected terminal output:

```text
Favorable detection: estimate=120.00, status=ok, peaks=9
Complete pulse misses: estimate=none, status=insufficient_peaks, peaks=0
Same low rate, favorable alignment: estimate=60.00, status=ok, peaks=4
Saved results/demo.png
```

**Open `results/demo.png` in VS Code.** No graph window opens automatically.
Gray curves show the reference signal, blue dots are measurements, and red crosses
are detected peaks. The dense reference curve is only for visualization.

```sh
python demo.py --duration 8 --output results/eight_second_demo.png
```

This shows all eight seconds. Expected peak counts are 15, 0, and 7, with the same
estimates and statuses as above. Boundary pulses are excluded by the detector.

## Run the independent test harness

```sh
python -m unittest discover -s tests -v
```

Expected ending; execution time varies:

```text
Ran 18 tests in ...s

OK
```

- `test_core.py` checks timestamps, pulse boundaries, known tempos, complete misses,
  alignment, plateaus, recording boundaries, invalid inputs, and a separate callable.
  Its favorable-grid test covers all 12 BPM/width pairs at 200 Hz with a conservative
  4 BPM tolerance. This is a test tolerance, not an accuracy guarantee for the grid.
- `test_experiment.py` checks CSV values, insufficient-detection rows, and protection
  of previous files when validation or generation fails.

## File guide

| File | Purpose | How to use it |
| --- | --- | --- |
| `example.py` | One editable end-to-end case | Run it and change its constants |
| `sampling.py` | Measure a supplied signal | Imported by other scripts |
| `detection.py` | Estimate BPM from measurements | Imported by other scripts |
| `reference_signal.py` | Generate fake pulses for testing | Imported by examples and tests |
| `demo.py` | Run and plot three cases | Run it, then open the PNG |
| `tests/test_core.py` | Validate generation, sampling, detection | Use the test command |
| `tests/test_experiment.py` | Validate safe CSV export | Use the same test command |
| `experiment.py` | Export cases for later analysis | Optional for the progress report |

Running the sampler, detector, or generator module directly produces no output.
They define functions. `example.py` and `demo.py` call those functions.

## Function inputs and outputs

### Reference generator

```python
signal = rectangular_pulses(bpm=120, pulse_width_ms=50)
```

Returns a **function**. Call `signal(times)` with a one-dimensional NumPy timestamp
array in seconds to get matching amplitudes: 1 inside pulses, 0 between them.
Optional `first_beat_seconds` defaults to zero. BPM must be positive and finite;
pulse width must be positive, finite, and shorter than `60 / bpm` seconds.

### Sampler

```python
times, amplitudes = sample_signal(signal, 200, 5, 0)
```

| Input | Meaning | Requirement |
| --- | --- | --- |
| `signal` | Function mapping times to amplitudes | Matching one-dimensional output |
| `sampling_frequency` | Measurements per second, in Hz | Positive and finite |
| `duration` | Recording length, in seconds | Positive and finite |
| `offset_seconds` | Time of the first sample | `0 <= offset < 1 / sampling_frequency` |

Returns matching arrays of **when** measurements happened and **what** was measured.
Timestamps are `offset + n / sampling_frequency`, before the recording's end.
An offset after the recording ends produces empty arrays.

A predictable example, runnable in a Python file in the project folder:

```python
from sampling import sample_signal

times, amplitudes = sample_signal(lambda times: 2 * times + 1, 4, 1, 0.125)
print(times.tolist())       # [0.125, 0.375, 0.625, 0.875]
print(amplitudes.tolist())  # [1.25, 1.75, 2.25, 2.75]
```

### Detector

```python
result = estimate_bpm(amplitudes, sampling_frequency=200)
```

Supply the same frequency used for sampling. The detector sees no true BPM or
generator. It finds peaks, converts their positions to seconds, and calculates
`60 / median(intervals_between_peaks)` with fixed default detection settings.

| Result field | Meaning |
| --- | --- |
| `estimated_bpm` | Numeric estimate, or `None` when insufficient |
| `peak_indices` | Positions of peaks in the amplitude array |
| `peak_count` | Number of detected peaks |
| `status` | `ok` or `insufficient_peaks` |
| `peak_times_seconds` | Seconds from the first sample, excluding the offset |

**`ok` means at least two peaks were found, not that the answer is correct.**
Fewer than two peaks gives `insufficient_peaks`; invalid input raises an error.
Flat pulses contribute one midpoint peak, rounded down for even-length plateaus.
Peaks touching the first or last sample are excluded; no padding is added.
For absolute peak times, use `times[result.peak_indices]`.

```python
from detection import estimate_bpm

result = estimate_bpm([0, 1, 0, 1, 0], 2)
# BPM: 60.0; peak indices: [1, 3]; peak count: 2
# Status: 'ok'; peak times: [0.5, 1.5] seconds
print(result)
```

## Connecting Matthew's generator

Supply a function accepting a one-dimensional NumPy array of times **in seconds**
and returning one finite amplitude per timestamp. It must handle an empty array.
Replace the generator assignment in `example.py`; the sampler and detector stay
the same. The reference fixture is not imported by either core module.

If Matthew supplies recorded amplitudes instead, obtain timestamps or the original
sampling frequency **and time origin** before writing an adapter. Agree on
interpolation and out-of-range behavior rather than guessing them.

## Optional experiment export

Start with four easy-to-check cases:

```sh
python experiment.py --bpms 60 --widths-ms 25 --rates-hz 5 200 --duration 5 --offset-count 2 --output results/small_experiment.csv
```

Expected message: `Wrote 4 cases to results/small_experiment.csv`.

| Rate Hz | Offset seconds | Samples | Peaks | Estimated BPM | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
| 5 | 0 | 25 | 4 | 60 | ok |
| 5 | 0.1 | 25 | 0 | blank | insufficient_peaks |
| 200 | 0 | 1000 | 4 | 60 | ok |
| 200 | 0.0025 | 1000 | 4 | 60 | ok |

For the full grid:

```sh
python experiment.py
```

Expected message: `Wrote 1440 cases to results/experiment.csv`.
This tests 4 BPMs (60, 90, 120, 150), 3 widths (25, 50, 100 ms), 6 rates
(5, 10, 20, 50, 100, 200 Hz), and 20 offsets, using 30-second recordings.
`offset_fraction = k / 20` and `offset_seconds = offset_fraction / sampling_frequency`.
A fraction of 0.5 means half a sampling interval, **not** half a second.

| CSV field | Meaning |
| --- | --- |
| `true_bpm` | Known generator tempo for later comparison |
| `pulse_width_ms` | Duration of one pulse, in milliseconds |
| `sampling_frequency_hz` | Measurements per second |
| `duration_seconds` | Recording length |
| `offset_fraction` | Offset as a fraction of one sampling interval |
| `offset_seconds` | Actual first-sample time |
| `sample_count` | Number of measurements |
| `peak_count` | Number of detected peaks |
| `estimated_bpm` | Numeric estimate; blank when insufficient |
| `detector_status` | `ok` or `insufficient_peaks` |

Successful runs replace the selected output. Use a new `--output` name to keep
older successful runs. Failed runs preserve the previous file: export uses a
temporary file and replaces the destination only on success. Errors go to stderr
and exit nonzero. Demo messages also go to stderr; VS Code displays these normally.

## Current evidence and numerical convention

The fixture includes pulse starts and excludes pulse ends. Timestamps within four
floating-point spacings of a boundary are treated as exactly on that boundary.
This resolves rounding between equivalent time calculations; it does not extend
pulses by a sampling interval. A one-nanosecond separation in the tested short
recording remains distinct.

The original fixture sometimes missed aligned beat starts. The November 21 fix
adds a regression case: 150 BPM, 25 ms, 5 Hz, 30 seconds, zero offset now produces
75 high samples, 74 interior peaks, and approximately 150 BPM, correcting the old
75 BPM artifact. The three default demo results are unchanged.

Regenerated November 21, 2026: all 18 tests pass. The full CSV has 1,440 cases,
1,205 numeric estimates, and 235 insufficient detections. These are output counts,
not a completed accuracy analysis. Correcting boundary classification changes some
cases without changing the sampler or detection algorithm.

**`output/report/` is the November 19 historical report and evidence.** Its old
counts and unresolved-issue wording do not describe the current code. See its
README. Use root source files and `results/` for current work.

## Progress report scope

- **Section 3:** sampler, detector, units, parameters, fixed settings, independent
  harness, and important code snapshots.
- **Section 4:** the three demo outcomes and successful tests. Broader CSV error
  analysis can follow team integration.
- **Section 5:** pending integration, noise testing, and broader analysis.
- Include actual prompts, AI assistance, revisions, and personal learning. Update
  the historical report for these fixes and the model actually used.

The proposal specifies the BPMs, widths, and rates. The duration and offset grid
are implementation choices. This studies idealized pulses, not raw music audio.
Keep the detector fixed while comparing sampling conditions; final optimization
and claims of a best rate are outside the current progress-report results.

## References

- [SciPy find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html): detection and plateau conventions.
- [NumPy arange](https://numpy.org/doc/stable/reference/generated/numpy.arange.html): index arrays and floating-step caveats.
- [NumPy median](https://numpy.org/doc/stable/reference/generated/numpy.median.html): interval summary.
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html): naming and formatting reference.
