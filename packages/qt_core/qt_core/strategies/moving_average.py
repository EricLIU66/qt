from __future__ import annotations


def moving_average_signal(closes: list[float], fast_window: int, slow_window: int) -> list[bool]:
    if fast_window <= 0 or slow_window <= 0:
        raise ValueError("windows must be positive")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window")
    if len(closes) < slow_window:
        raise ValueError("not enough close values for slow_window")

    signals: list[bool] = []
    for index in range(len(closes)):
        if index + 1 < slow_window:
            signals.append(False)
            continue
        fast = sum(closes[index + 1 - fast_window : index + 1]) / fast_window
        slow = sum(closes[index + 1 - slow_window : index + 1]) / slow_window
        signals.append(fast > slow)
    return signals
