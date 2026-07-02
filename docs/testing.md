# Testing Strategy

## Required Coverage Areas

- Daily OHLCV validation.
- Strategy signal generation.
- Backtest result normalization.
- Metric and drawdown calculation.
- JSON contract compatibility with the frontend.
- Future VectorBT adapter conversion using deterministic fixtures.
- Future QuestDB provider queries using opt-in integration tests.

## Golden Data

Use small ETF fixture datasets under `tests/fixtures` for fast deterministic tests. Do not make tests depend on Futu OpenD availability.

## Live Integrations

Futu OpenD integration tests should be opt-in and skipped by default unless credentials and local OpenD connectivity are explicitly configured.

QuestDB integration tests should also be opt-in and skipped by default unless a local QuestDB instance is explicitly configured. Unit tests must continue to use fixture data and must not require Docker.
