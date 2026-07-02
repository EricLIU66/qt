from __future__ import annotations

from dataclasses import dataclass

from qt_core.backtest import BacktestEngine, BacktestRequest
from qt_core.contracts import BacktestRun


@dataclass(frozen=True, slots=True)
class BacktestJob:
    request: BacktestRequest


class BacktestWorker:
    def __init__(self, engine: BacktestEngine) -> None:
        self._engine = engine

    def run_job(self, job: BacktestJob) -> BacktestRun:
        return self._engine.run(job.request)
