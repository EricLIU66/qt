# Futu OpenD Integration Notes

Futu OpenD is a future data ingestion source for v1. The first implementation should keep it behind a data provider interface and normalize output into internal daily-bar records before any strategy code sees it.

## Rules

- Never let strategy code call Futu APIs directly.
- Cache raw responses separately from normalized bars.
- Record symbol, market, timezone, adjustment mode, and retrieval timestamp.
- Tests must use fixture data by default.
- Futu connectivity checks should be explicit operational commands, not required unit tests.
