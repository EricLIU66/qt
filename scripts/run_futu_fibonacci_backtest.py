from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Metrics:
    total_return: float
    buy_hold_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe: float | None
    max_drawdown: float
    exposure: float
    trades: int
    win_rate: float | None


def fetch_futu_daily_bars(code: str, start: str, end: str) -> list[dict[str, Any]]:
    try:
        from futu import AuType, KLType, OpenQuoteContext, RET_OK, Session
    except ModuleNotFoundError as exc:
        raise RuntimeError("futu-api is not installed") from exc

    ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
    try:
        page_req_key = None
        frames = []
        while True:
            ret, data, page_req_key = ctx.request_history_kline(
                code,
                start=start,
                end=end,
                ktype=KLType.K_DAY,
                autype=AuType.QFQ,
                max_count=1000,
                page_req_key=page_req_key,
                session=Session.NONE,
            )
            if ret != RET_OK:
                raise RuntimeError(f"Futu request_history_kline failed: {data}")
            frames.append(data)
            if page_req_key is None:
                break

        import pandas as pd

        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        records: list[dict[str, Any]] = []
        for row in df.to_dict(orient="records"):
            records.append(
                {
                    "date": str(row["time_key"])[:10],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["volume"]),
                    "turnover": float(row.get("turnover", 0.0)),
                }
            )
        return records
    finally:
        ctx.close()


def run_backtest(records: list[dict[str, Any]], lookback: int, initial_cash: float) -> dict[str, Any]:
    import numpy as np
    import pandas as pd

    df = pd.DataFrame(records)
    if df.empty:
        raise RuntimeError("No data returned from Futu OpenD")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)

    rolling_high = df["high"].rolling(lookback).max().shift(1)
    rolling_low = df["low"].rolling(lookback).min().shift(1)
    price_range = rolling_high - rolling_low

    df["fib_236"] = rolling_high - 0.236 * price_range
    df["fib_382"] = rolling_high - 0.382 * price_range
    df["fib_500"] = rolling_high - 0.500 * price_range
    df["fib_618"] = rolling_high - 0.618 * price_range
    df["fib_786"] = rolling_high - 0.786 * price_range
    df["sma_200"] = df["close"].rolling(200).mean().shift(1)

    close = df["close"]
    prior_close = close.shift(1)

    bounce_from_support = (prior_close <= df["fib_618"]) & (close > df["fib_618"])
    trend_ok = close > df["sma_200"]
    entry_signal = bounce_from_support & trend_ok

    take_profit = close >= df["fib_236"]
    support_break = close < df["fib_786"]
    trend_break = close < df["sma_200"]
    exit_signal = take_profit | support_break | trend_break

    position = []
    in_position = False
    trade_events: list[dict[str, Any]] = []
    for index, row in df.iterrows():
        if in_position and bool(exit_signal.iloc[index]):
            in_position = False
            trade_events.append(
                {"date": row["date"].date().isoformat(), "side": "sell", "price": row["close"]}
            )
        elif not in_position and bool(entry_signal.iloc[index]):
            in_position = True
            trade_events.append(
                {"date": row["date"].date().isoformat(), "side": "buy", "price": row["close"]}
            )
        position.append(1.0 if in_position else 0.0)

    df["position_close"] = position
    df["position"] = df["position_close"].shift(1).fillna(0.0)
    df["daily_return"] = df["close"].pct_change().fillna(0.0)
    df["strategy_return"] = df["position"] * df["daily_return"]
    df["equity"] = initial_cash * (1.0 + df["strategy_return"]).cumprod()
    df["buy_hold_equity"] = initial_cash * (df["close"] / df["close"].iloc[0])
    df["drawdown"] = df["equity"] / df["equity"].cummax() - 1.0

    returns = df["strategy_return"].dropna()
    total_return = df["equity"].iloc[-1] / initial_cash - 1.0
    buy_hold_return = df["buy_hold_equity"].iloc[-1] / initial_cash - 1.0
    years = max((df["date"].iloc[-1] - df["date"].iloc[0]).days / 365.25, 1e-9)
    annualized_return = (1.0 + total_return) ** (1.0 / years) - 1.0
    annualized_volatility = float(returns.std(ddof=0) * np.sqrt(252))
    sharpe = (
        float(returns.mean() / returns.std(ddof=0) * np.sqrt(252))
        if returns.std(ddof=0) > 0.0
        else None
    )

    round_trips = []
    current_buy = None
    for event in trade_events:
        if event["side"] == "buy":
            current_buy = event
        elif event["side"] == "sell" and current_buy is not None:
            round_trips.append(event["price"] / current_buy["price"] - 1.0)
            current_buy = None

    metrics = Metrics(
        total_return=float(total_return),
        buy_hold_return=float(buy_hold_return),
        annualized_return=float(annualized_return),
        annualized_volatility=annualized_volatility,
        sharpe=sharpe,
        max_drawdown=float(df["drawdown"].min()),
        exposure=float(df["position"].mean()),
        trades=len(trade_events),
        win_rate=float(sum(item > 0 for item in round_trips) / len(round_trips))
        if round_trips
        else None,
    )

    latest = df.iloc[-1]
    return {
        "metrics": asdict(metrics),
        "coverage": {
            "requested_start": "1997-01-01",
            "actual_start": df["date"].iloc[0].date().isoformat(),
            "actual_end": df["date"].iloc[-1].date().isoformat(),
            "rows": int(len(df)),
        },
        "latest_levels": {
            "date": latest["date"].date().isoformat(),
            "close": float(latest["close"]),
            "fib_236_resistance": float(latest["fib_236"]),
            "fib_382": float(latest["fib_382"]),
            "fib_500": float(latest["fib_500"]),
            "fib_618_support": float(latest["fib_618"]),
            "fib_786_stop_support": float(latest["fib_786"]),
            "sma_200": float(latest["sma_200"]),
            "in_position": bool(latest["position_close"] == 1.0),
        },
        "trade_events": trade_events,
        "equity_curve": [
            {
                "date": row["date"].date().isoformat(),
                "equity": float(row["equity"]),
                "buy_hold_equity": float(row["buy_hold_equity"]),
                "drawdown": float(row["drawdown"]),
                "position": float(row["position"]),
            }
            for row in df.to_dict(orient="records")
        ],
        "frame": df,
    }


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def write_report(result: dict[str, Any], output_dir: Path) -> Path:
    metrics = result["metrics"]
    coverage = result["coverage"]
    levels = result["latest_levels"]
    report_path = output_dir / "futu_qqq_fibonacci_backtest.md"
    trade_tail = result["trade_events"][-10:]

    lines = [
        "# QQQ Fibonacci Support/Resistance Backtest",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "- Data source: Futu OpenD `request_history_kline`, daily K, forward-adjusted prices.",
        f"- Requested range: 1997-01-01 to {date.today().isoformat()}",
        f"- Actual data returned: {coverage['actual_start']} to {coverage['actual_end']} ({coverage['rows']} rows)",
        "- Instrument: `US.QQQ`",
        "",
        "## Strategy",
        "",
        "- Rolling lookback: 252 trading days.",
        "- Fibonacci levels use the prior day's rolling high/low to avoid look-ahead bias.",
        "- Entry: close crosses above the 61.8% retracement support and close is above prior 200-day SMA.",
        "- Exit: close reaches 23.6% resistance, breaks below 78.6% support, or closes below prior 200-day SMA.",
        "- Positioning: long/cash only, no shorting, no leverage, no fees/slippage in this first pass.",
        "- Signal timing: close generates signal; position is applied to the next day's return.",
        "",
        "## Performance",
        "",
        f"- Strategy total return: {pct(metrics['total_return'])}",
        f"- Buy-and-hold total return: {pct(metrics['buy_hold_return'])}",
        f"- Annualized return: {pct(metrics['annualized_return'])}",
        f"- Annualized volatility: {pct(metrics['annualized_volatility'])}",
        f"- Sharpe, rf=0: {metrics['sharpe']:.2f}" if metrics["sharpe"] is not None else "- Sharpe, rf=0: n/a",
        f"- Max drawdown: {pct(metrics['max_drawdown'])}",
        f"- Exposure: {pct(metrics['exposure'])}",
        f"- Trade events: {metrics['trades']}",
        f"- Round-trip win rate: {pct(metrics['win_rate'])}",
        "",
        "## Latest Fibonacci Levels",
        "",
        f"- Date: {levels['date']}",
        f"- Close: {levels['close']:.2f}",
        f"- 23.6% resistance: {levels['fib_236_resistance']:.2f}",
        f"- 38.2% level: {levels['fib_382']:.2f}",
        f"- 50.0% level: {levels['fib_500']:.2f}",
        f"- 61.8% support: {levels['fib_618_support']:.2f}",
        f"- 78.6% stop support: {levels['fib_786_stop_support']:.2f}",
        f"- 200-day SMA: {levels['sma_200']:.2f}",
        f"- Current strategy state: {'long' if levels['in_position'] else 'cash'}",
        "",
        "## Recent Trade Events",
        "",
    ]

    if trade_tail:
        lines.extend(["| Date | Side | Price |", "|---|---:|---:|"])
        for event in trade_tail:
            lines.append(f"| {event['date']} | {event['side']} | {event['price']:.2f} |")
    else:
        lines.append("No trade events generated.")

    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- Futu returned data starting at the actual coverage date above, not 1997.",
            "- This first pass excludes commissions, spreads, slippage, tax, and dividend cash-flow modeling beyond Futu's forward-adjusted price series.",
            "- This is research output, not investment advice and not a live trading signal.",
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", default="US.QQQ")
    parser.add_argument("--start", default="1997-01-01")
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument("--lookback", type=int, default=252)
    parser.add_argument("--initial-cash", type=float, default=100_000.0)
    parser.add_argument("--output-dir", default="artifacts/backtests/futu_qqq_fibonacci")
    parser.add_argument("--report-dir", default="reports/backtests")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    report_dir = Path(args.report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    records = fetch_futu_daily_bars(args.code, args.start, args.end)
    result = run_backtest(records, args.lookback, args.initial_cash)

    raw_path = output_dir / "qqq_daily_futu.json"
    raw_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    frame = result.pop("frame")
    frame.to_csv(output_dir / "qqq_fibonacci_backtest_timeseries.csv", index=False)
    json_path = output_dir / "qqq_fibonacci_backtest_summary.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    report_path = write_report(result, report_dir)
    print(json.dumps({"report": str(report_path), "summary": str(json_path)}, indent=2))


if __name__ == "__main__":
    main()
