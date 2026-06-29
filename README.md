# Quant Research Platform

Production-grade, single-user research and backtesting software for daily-bar US broad-market ETF strategies.

## V1 Scope

- Python-first strategy authoring.
- Daily-bar ETF research and backtesting.
- VectorBT as the intended production backtesting engine.
- Internal result contracts that keep the UI independent from any single backtesting library.
- Human-friendly result dashboard.
- Documentation, tests, and reproducible fixtures from the start.

## Non-goals

- Live trading, paper trading, or automatic order placement.
- Minute/tick/order-book backtesting.
- Multi-user permissions or SaaS deployment.
- UI low-code strategy authoring.
- NautilusTrader as a v1 dependency.

## Repository Layout

```text
apps/web              React UI for backtest result exploration
services/api          Backend API boundary
services/worker       Backtest job runner boundary
packages/qt_core      Core contracts, data normalization, metrics, strategies
tests                 Unit and integration tests
docs                  Product, architecture, and operating documentation
scripts               Local quality gates
```

## Quick Start

Use Python 3.11 or 3.12. Python 3.13 is intentionally excluded until the quantitative stack fully supports it.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,backtest,api]"
python -m unittest discover -s tests
```

Frontend:

```powershell
cd apps/web
npm install
npm run dev
```

## Current Status

This is a hardened project skeleton with executable core contracts and tests. The VectorBT adapter is represented by a stable internal boundary so the first production implementation can be added without coupling UI code to framework-native objects.
