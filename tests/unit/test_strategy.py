from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "qt_core"))

from qt_core.strategies import moving_average_signal


class MovingAverageStrategyTests(unittest.TestCase):
    def test_signal_turns_on_when_fast_average_exceeds_slow_average(self) -> None:
        signals = moving_average_signal([10, 10, 10, 11, 12], fast_window=2, slow_window=3)

        self.assertEqual(signals, [False, False, False, True, True])

    def test_fast_window_must_be_smaller_than_slow_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "fast_window"):
            moving_average_signal([10, 11, 12], fast_window=3, slow_window=3)


if __name__ == "__main__":
    unittest.main()
