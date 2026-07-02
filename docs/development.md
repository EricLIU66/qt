# Development Guide

## Python Environment

Use Python 3.11 or 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,api,backtest]"
```

## Run Tests

```powershell
python -m unittest discover -s tests
```

Optional quality gates after installing dev extras:

```powershell
ruff check .
mypy packages/qt_core services/api services/worker
```

## Run API

```powershell
uvicorn qt_api.app:app --reload
```

## Run UI

```powershell
cd apps/web
npm install
npm run dev
```

## Adding a Strategy

Strategies should be plain Python modules with deterministic inputs and outputs. Keep data loading, parameter selection, and report rendering outside strategy logic so strategies can be tested directly.
