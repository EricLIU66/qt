from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from qt_core.contracts import BacktestRun


@dataclass(frozen=True, slots=True)
class BacktestRequest:
    strategy_name: str
    symbols: tuple[str, ...]
    start: date
    end: date
    parameters: dict[str, float | int | str | bool] = field(default_factory=dict)


class BacktestEngine(Protocol):
    name: str

    def run(self, request: BacktestRequest) -> BacktestRun:
        """Run a backtest and return the normalized internal result contract."""
