from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TradeSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class EquityPoint:
    date: date
    equity: float
    cash: float
    exposure: float


@dataclass(frozen=True, slots=True)
class DrawdownPoint:
    date: date
    drawdown: float


@dataclass(frozen=True, slots=True)
class Trade:
    symbol: str
    side: TradeSide
    date: date
    quantity: float
    price: float
    fees: float = 0.0


@dataclass(frozen=True, slots=True)
class PositionSnapshot:
    date: date
    symbol: str
    quantity: float
    market_value: float
    weight: float


@dataclass(frozen=True, slots=True)
class MetricSummary:
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe: float | None
    max_drawdown: float
    exposure: float
    win_rate: float | None = None


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    benchmark_symbol: str
    strategy_total_return: float
    benchmark_total_return: float
    excess_return: float
    correlation: float | None = None


@dataclass(frozen=True, slots=True)
class BacktestRun:
    strategy_name: str
    symbols: tuple[str, ...]
    start: date
    end: date
    metrics: MetricSummary
    equity_curve: tuple[EquityPoint, ...]
    drawdowns: tuple[DrawdownPoint, ...]
    trades: tuple[Trade, ...] = field(default_factory=tuple)
    positions: tuple[PositionSnapshot, ...] = field(default_factory=tuple)
    benchmark: BenchmarkComparison | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    engine: str = "internal"
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
