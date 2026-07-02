from __future__ import annotations

from qt_core.backtest.engine import BacktestRequest
from qt_core.contracts import BacktestRun


class VectorBtAdapter:
    name = "vectorbt"

    def run(self, request: BacktestRequest) -> BacktestRun:
        raise NotImplementedError(
            "VectorBT execution is intentionally isolated behind this adapter. "
            "Install the backtest extras and implement conversion to BacktestRun here."
        )
