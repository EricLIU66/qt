from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4

try:
    import pandas as pd
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover - exercised only without api extras
    FastAPI = None  # type: ignore[assignment]


class FibonacciParams(BaseModel):
    symbol: str = Field(default="SPY")
    lookback: int = Field(default=252, ge=50, le=1000)
    sma_window: int = Field(default=200, ge=20, le=500)
    entry_ratio: float = Field(default=0.618, ge=0.0, le=1.0)
    resistance_ratio: float = Field(default=0.236, ge=0.0, le=1.0)
    stop_ratio: float = Field(default=0.786, ge=0.0, le=1.0)
    initial_cash: float = Field(default=100_000.0, gt=0)


RUN_HISTORY: list[dict[str, Any]] = []


def create_app() -> "FastAPI":
    if FastAPI is None:
        raise RuntimeError("Install api extras with: python -m pip install -e '.[api]'")

    app = FastAPI(title="Quant Research Platform API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/market/history")
    def market_history(symbol: str = "SPY") -> dict[str, Any]:
        bars = load_daily_bars(symbol)
        return {
            "symbol": symbol.upper(),
            "rows": len(bars),
            "start": bars[0]["date"] if bars else None,
            "end": bars[-1]["date"] if bars else None,
            "bars": bars,
        }

    @app.get("/backtests")
    def backtest_history() -> dict[str, Any]:
        return {"runs": RUN_HISTORY}

    @app.post("/backtests/fibonacci")
    def run_fibonacci(params: FibonacciParams) -> dict[str, Any]:
        bars = load_daily_bars(params.symbol)
        if not bars:
            raise HTTPException(status_code=404, detail=f"No QuestDB bars found for {params.symbol}")
        run = run_fibonacci_backtest(bars, params)
        RUN_HISTORY.append(run)
        return {"run": run, "runs": RUN_HISTORY}

    return app


def questdb_http_url() -> str:
    return os.environ.get("QUESTDB_HTTP_URL", "http://localhost:9000").rstrip("/")


def questdb_exec(query: str) -> dict[str, Any]:
    url = f"{questdb_http_url()}/exec?{urlencode({'query': query})}"
    try:
        with urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - endpoint should surface connection failures clearly
        raise HTTPException(status_code=503, detail=f"QuestDB unavailable: {exc}") from exc
    if "error" in data:
        raise HTTPException(status_code=500, detail=f"QuestDB query failed: {data['error']}")
    return data


def load_daily_bars(symbol: str) -> list[dict[str, Any]]:
    safe_symbol = symbol.upper().replace("'", "''")
    result = questdb_exec(
        f"""
        SELECT ts, open, high, low, close, volume
        FROM daily_bars
        WHERE symbol = '{safe_symbol}'
        ORDER BY ts
        """
    )
    bars: list[dict[str, Any]] = []
    for row in result.get("dataset", []):
        bars.append(
            {
                "date": str(row[0])[:10],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": int(row[5]),
            }
        )

    if not bars:
        return []

    first_close = bars[0]["close"]
    for bar in bars:
        bar["close_index"] = bar["close"] / first_close * 100.0
    return bars


def run_fibonacci_backtest(bars: list[dict[str, Any]], params: FibonacciParams) -> dict[str, Any]:
    df = pd.DataFrame(bars)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    rolling_high = df["high"].rolling(params.lookback).max().shift(1)
    rolling_low = df["low"].rolling(params.lookback).min().shift(1)
    price_range = rolling_high - rolling_low

    entry_level = rolling_high - params.entry_ratio * price_range
    resistance_level = rolling_high - params.resistance_ratio * price_range
    stop_level = rolling_high - params.stop_ratio * price_range
    sma = df["close"].rolling(params.sma_window).mean().shift(1)

    close = df["close"]
    prior_close = close.shift(1)
    entry_signal = (prior_close <= entry_level) & (close > entry_level) & (close > sma)
    exit_signal = (close >= resistance_level) | (close < stop_level) | (close < sma)

    in_position = False
    position_close: list[float] = []
    trade_events: list[dict[str, Any]] = []
    for index, row in df.iterrows():
        if in_position and bool(exit_signal.iloc[index]):
            in_position = False
            trade_events.append(
                {"date": row["date"].date().isoformat(), "side": "sell", "price": float(row["close"])}
            )
        elif not in_position and bool(entry_signal.iloc[index]):
            in_position = True
            trade_events.append(
                {"date": row["date"].date().isoformat(), "side": "buy", "price": float(row["close"])}
            )
        position_close.append(1.0 if in_position else 0.0)

    df["position_close"] = position_close
    df["position"] = df["position_close"].shift(1).fillna(0.0)
    df["daily_return"] = df["close"].pct_change().fillna(0.0)
    df["strategy_return"] = df["position"] * df["daily_return"]
    df["equity"] = params.initial_cash * (1.0 + df["strategy_return"]).cumprod()
    df["buy_hold_equity"] = params.initial_cash * (df["close"] / df["close"].iloc[0])
    df["drawdown"] = df["equity"] / df["equity"].cummax() - 1.0
    df["strategy_index"] = df["equity"] / params.initial_cash * 100.0
    df["buy_hold_index"] = df["buy_hold_equity"] / params.initial_cash * 100.0

    returns = df["strategy_return"]
    total_return = float(df["equity"].iloc[-1] / params.initial_cash - 1.0)
    buy_hold_return = float(df["buy_hold_equity"].iloc[-1] / params.initial_cash - 1.0)
    years = max((df["date"].iloc[-1] - df["date"].iloc[0]).days / 365.25, 1e-9)
    annualized_return = float((1.0 + total_return) ** (1.0 / years) - 1.0)
    volatility = float(returns.std(ddof=0) * math.sqrt(252))
    sharpe = float(returns.mean() / returns.std(ddof=0) * math.sqrt(252)) if volatility > 0 else None

    round_trips = []
    current_buy: dict[str, Any] | None = None
    for event in trade_events:
        if event["side"] == "buy":
            current_buy = event
        elif event["side"] == "sell" and current_buy is not None:
            round_trips.append(event["price"] / current_buy["price"] - 1.0)
            current_buy = None

    run_id = str(uuid4())[:8]
    created_at = datetime.now(tz=timezone.utc).isoformat()
    latest = df.iloc[-1]
    series = [
        {
            "date": row["date"].date().isoformat(),
            "strategy_index": float(row["strategy_index"]),
            "buy_hold_index": float(row["buy_hold_index"]),
            "position": float(row["position"]),
        }
        for row in df.to_dict(orient="records")
    ]
    return {
        "run_id": run_id,
        "label": f"fib {params.lookback}/{params.sma_window} #{len(RUN_HISTORY) + 1}",
        "created_at": created_at,
        "symbol": params.symbol.upper(),
        "params": params.model_dump(),
        "metrics": {
            "total_return": total_return,
            "buy_hold_return": buy_hold_return,
            "annualized_return": annualized_return,
            "annualized_volatility": volatility,
            "sharpe": sharpe,
            "max_drawdown": float(df["drawdown"].min()),
            "exposure": float(df["position"].mean()),
            "trade_events": len(trade_events),
            "win_rate": float(sum(item > 0 for item in round_trips) / len(round_trips))
            if round_trips
            else None,
        },
        "latest_levels": {
            "date": latest["date"].date().isoformat(),
            "close": float(latest["close"]),
            "entry_support": clean_number(entry_level.iloc[-1]),
            "resistance": clean_number(resistance_level.iloc[-1]),
            "stop_support": clean_number(stop_level.iloc[-1]),
            "sma": clean_number(sma.iloc[-1]),
            "in_position": bool(latest["position_close"] == 1.0),
        },
        "trade_events": trade_events[-20:],
        "series": series,
    }


def clean_number(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


app = create_app() if FastAPI is not None else None
