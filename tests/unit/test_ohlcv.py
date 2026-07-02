from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "qt_core"))

from qt_core.data import OhlcvBar, validate_daily_bars


class OhlcvValidationTests(unittest.TestCase):
    def test_valid_daily_bars_pass(self) -> None:
        bars = [
            OhlcvBar("SPY", date(2024, 1, 2), 100.0, 102.0, 99.0, 101.0, 1_000_000),
            OhlcvBar("SPY", date(2024, 1, 3), 101.0, 103.0, 100.0, 102.0, 1_100_000),
        ]

        validate_daily_bars(bars)

    def test_duplicate_symbol_date_fails(self) -> None:
        bars = [
            OhlcvBar("SPY", date(2024, 1, 2), 100.0, 102.0, 99.0, 101.0, 1_000_000),
            OhlcvBar("SPY", date(2024, 1, 2), 101.0, 103.0, 100.0, 102.0, 1_100_000),
        ]

        with self.assertRaisesRegex(ValueError, "duplicate bar"):
            validate_daily_bars(bars)


if __name__ == "__main__":
    unittest.main()
