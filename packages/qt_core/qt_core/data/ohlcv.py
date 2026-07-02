from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class OhlcvBar:
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: float | None = None


def validate_daily_bars(bars: list[OhlcvBar]) -> None:
    if not bars:
        raise ValueError("daily bars cannot be empty")

    seen: set[tuple[str, date]] = set()
    for bar in bars:
        if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
            raise ValueError(f"{bar.symbol} {bar.date} contains non-positive OHLC values")
        if bar.high < max(bar.open, bar.close, bar.low):
            raise ValueError(f"{bar.symbol} {bar.date} high is below another OHLC value")
        if bar.low > min(bar.open, bar.close, bar.high):
            raise ValueError(f"{bar.symbol} {bar.date} low is above another OHLC value")
        if bar.volume < 0:
            raise ValueError(f"{bar.symbol} {bar.date} volume is negative")

        key = (bar.symbol, bar.date)
        if key in seen:
            raise ValueError(f"duplicate bar for {bar.symbol} {bar.date}")
        seen.add(key)
