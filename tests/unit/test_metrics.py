from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "qt_core"))

from qt_core.contracts import EquityPoint
from qt_core.reports import calculate_drawdowns, calculate_metric_summary


class MetricsTests(unittest.TestCase):
    def test_drawdowns_track_peak_to_trough_loss(self) -> None:
        curve = (
            EquityPoint(date(2024, 1, 2), 100.0, 0.0, 1.0),
            EquityPoint(date(2024, 1, 3), 110.0, 0.0, 1.0),
            EquityPoint(date(2024, 1, 4), 99.0, 0.0, 1.0),
        )

        drawdowns = calculate_drawdowns(curve)

        self.assertEqual(drawdowns[0].drawdown, 0.0)
        self.assertEqual(drawdowns[1].drawdown, 0.0)
        self.assertAlmostEqual(drawdowns[2].drawdown, -0.10)

    def test_metric_summary_contains_core_risk_fields(self) -> None:
        curve = (
            EquityPoint(date(2024, 1, 2), 100.0, 0.0, 0.7),
            EquityPoint(date(2024, 1, 3), 105.0, 0.0, 0.8),
            EquityPoint(date(2024, 1, 4), 102.0, 0.0, 0.9),
        )

        metrics = calculate_metric_summary(curve)

        self.assertAlmostEqual(metrics.total_return, 0.02)
        self.assertLessEqual(metrics.max_drawdown, 0.0)
        self.assertAlmostEqual(metrics.exposure, 0.8)


if __name__ == "__main__":
    unittest.main()
