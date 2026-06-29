from __future__ import annotations

from datetime import date

from qt_core.contracts import BacktestRun, BenchmarkComparison, EquityPoint
from qt_core.reports import calculate_drawdowns, calculate_metric_summary

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover - exercised only without api extras
    FastAPI = None  # type: ignore[assignment]


def create_app() -> "FastAPI":
    if FastAPI is None:
        raise RuntimeError("Install api extras with: python -m pip install -e '.[api]'")

    app = FastAPI(title="Quant Research Platform API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/runs/demo")
    def demo_run() -> dict[str, object]:
        run = build_demo_run()
        return run.to_dict()

    return app


def build_demo_run() -> BacktestRun:
    equity_curve = (
        EquityPoint(date=date(2024, 1, 2), equity=100_000.0, cash=20_000.0, exposure=0.8),
        EquityPoint(date=date(2024, 1, 3), equity=101_200.0, cash=20_000.0, exposure=0.8),
        EquityPoint(date=date(2024, 1, 4), equity=100_700.0, cash=20_000.0, exposure=0.8),
        EquityPoint(date=date(2024, 1, 5), equity=102_400.0, cash=20_000.0, exposure=0.8),
    )
    metrics = calculate_metric_summary(equity_curve)
    return BacktestRun(
        strategy_name="demo_moving_average",
        symbols=("SPY",),
        start=equity_curve[0].date,
        end=equity_curve[-1].date,
        metrics=metrics,
        equity_curve=equity_curve,
        drawdowns=calculate_drawdowns(equity_curve),
        benchmark=BenchmarkComparison(
            benchmark_symbol="SPY",
            strategy_total_return=metrics.total_return,
            benchmark_total_return=0.018,
            excess_return=metrics.total_return - 0.018,
        ),
        parameters={"fast_window": 20, "slow_window": 100},
    )


app = create_app() if FastAPI is not None else None
