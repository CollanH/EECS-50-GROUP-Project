"""Check that CSV exports are complete and failed runs preserve previous data."""

import csv
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from experiment import FIELD_NAMES, run_experiment


class ExperimentExportTest(unittest.TestCase):
    """Verify exported values and safe replacement of an existing CSV."""

    def test_small_export_preserves_insufficient_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.csv"
            count = run_experiment(
                output, bpms=(60,), widths=(25,), rates=(5, 200),
                duration=5, offset_count=2,
            )
            with output.open(newline="") as file:
                reader = csv.DictReader(file)
                self.assertEqual(reader.fieldnames, list(FIELD_NAMES))
                rows = list(reader)
            self.assertEqual(count, 4)
            self.assertEqual(len(rows), 4)
            self.assertEqual([row["peak_count"] for row in rows], ["4", "0", "4", "4"])
            self.assertEqual(rows[1]["detector_status"], "insufficient_peaks")
            self.assertEqual(rows[1]["estimated_bpm"], "")
            for row in (rows[0], rows[2], rows[3]):
                self.assertAlmostEqual(float(row["estimated_bpm"]), 60)
            self.assertEqual(
                sorted(path.name for path in output.parent.iterdir()),
                ["results.csv"],
            )

    def test_invalid_configuration_preserves_existing_output(self):
        cases = (
            {"bpms": (60, 0)}, {"widths": (25, 1000)},
            {"rates": (5, 0)}, {"duration": 0}, {"offset_count": 0},
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.csv"
            for overrides in cases:
                with self.subTest(overrides=overrides):
                    output.write_text("previous successful results\n")
                    settings = dict(
                        bpms=(60,), widths=(25,), rates=(5,),
                        duration=5, offset_count=2,
                    )
                    settings.update(overrides)
                    with self.assertRaises(ValueError):
                        run_experiment(output, **settings)
                    self.assertEqual(
                        output.read_text(), "previous successful results\n",
                    )
                    self.assertEqual(len(list(output.parent.iterdir())), 1)

    def test_generation_failure_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.csv"
            output.write_text("previous successful results\n")
            with mock.patch(
                "experiment.estimate_bpm",
                side_effect=RuntimeError("failed detector"),
            ):
                with self.assertRaises(RuntimeError):
                    run_experiment(output, bpms=(60,), widths=(25,), rates=(5,))
            self.assertEqual(output.read_text(), "previous successful results\n")
            self.assertEqual(len(list(output.parent.iterdir())), 1)

    def test_invalid_run_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.csv"
            with self.assertRaises(ValueError):
                run_experiment(output, bpms=(60,), widths=(25,), rates=(0,))
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
