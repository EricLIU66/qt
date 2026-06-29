from __future__ import annotations

from datetime import date
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "qt_core"))

from qt_core.contracts import BacktestRun, EquityPoint
from qt_core.reports import backtest_run_to_json, calculate_drawdowns, calculate_metric_summary


class ResultContractTests(unittest.TestCase):
    def test_backtest_run_serializes_to_ui_contract(self) -> None:
        equity_curve = (
            EquityPoint(date(2024, 1, 2), 100_000.0, 20_000.0, 0.8),
            EquityPoint(date(2024, 1, 3), 101_000.0, 20_000.0, 0.8),
        )
        run = BacktestRun(
            strategy_name="fixture_strategy",
            symbols=("SPY",),
            start=equity_curve[0].date,
            end=equity_curve[-1].date,
            metrics=calculate_metric_summary(equity_curve),
            equity_curve=equity_curve,
            drawdowns=calculate_drawdowns(equity_curve),
            parameters={"window": 20},
        )

        payload = json.loads(backtest_run_to_json(run))

        self.assertEqual(payload["strategy_name"], "fixture_strategy")
        self.assertEqual(payload["symbols"], ["SPY"])
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["equity_curve"][0]["date"], "2024-01-02")


if __name__ == "__main__":
    unittest.main()
