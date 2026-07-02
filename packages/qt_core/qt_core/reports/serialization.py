from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from enum import Enum
from typing import Any

from qt_core.contracts import BacktestRun


class ResultEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, date | datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def backtest_run_to_json(run: BacktestRun) -> str:
    return json.dumps(asdict(run), cls=ResultEncoder, indent=2, sort_keys=True)
