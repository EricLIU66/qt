from __future__ import annotations

from math import sqrt

from qt_core.contracts import DrawdownPoint, EquityPoint, MetricSummary

TRADING_DAYS_PER_YEAR = 252


def calculate_drawdowns(equity_curve: tuple[EquityPoint, ...]) -> tuple[DrawdownPoint, ...]:
    if not equity_curve:
        raise ValueError("equity curve cannot be empty")

    peak = equity_curve[0].equity
    points: list[DrawdownPoint] = []
    for point in equity_curve:
        peak = max(peak, point.equity)
        drawdown = point.equity / peak - 1.0 if peak else 0.0
        points.append(DrawdownPoint(date=point.date, drawdown=drawdown))
    return tuple(points)


def calculate_metric_summary(equity_curve: tuple[EquityPoint, ...]) -> MetricSummary:
    if len(equity_curve) < 2:
        raise ValueError("at least two equity points are required")

    returns = [
        equity_curve[index].equity / equity_curve[index - 1].equity - 1.0
        for index in range(1, len(equity_curve))
    ]
    total_return = equity_curve[-1].equity / equity_curve[0].equity - 1.0
    annualized_return = (1.0 + total_return) ** (TRADING_DAYS_PER_YEAR / len(returns)) - 1.0
    mean_return = sum(returns) / len(returns)
    variance = sum((item - mean_return) ** 2 for item in returns) / len(returns)
    annualized_volatility = sqrt(variance) * sqrt(TRADING_DAYS_PER_YEAR)
    sharpe = (
        mean_return / sqrt(variance) * sqrt(TRADING_DAYS_PER_YEAR)
        if variance > 0.0
        else None
    )
    max_drawdown = min(point.drawdown for point in calculate_drawdowns(equity_curve))
    exposure = sum(point.exposure for point in equity_curve) / len(equity_curve)

    return MetricSummary(
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility,
        sharpe=sharpe,
        max_drawdown=max_drawdown,
        exposure=exposure,
    )
