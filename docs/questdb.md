# QuestDB Data Source Notes

QuestDB can be used as an optional local time-series database for market data. It is not required for unit tests or the first file-based development workflow, but it is a good fit for larger daily-bar datasets and SQL-backed research queries.

## Current Local Check

Docker was checked with:

```powershell
docker ps --format "{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Ports}}\t{{.Status}}"
```

The command could not connect to the Docker Desktop Linux engine, so no running QuestDB container was detected. Start Docker Desktop before using the commands below.

## Recommended Local Container

```powershell
docker run --name qt-questdb `
  -p 9000:9000 `
  -p 9009:9009 `
  -p 8812:8812 `
  -p 9003:9003 `
  -v qt_questdb_data:/var/lib/questdb `
  questdb/questdb:9.4.3
```

Useful endpoints:

- Web console and REST API: `http://localhost:9000`
- InfluxDB Line Protocol ingestion: `localhost:9009`
- PostgreSQL wire protocol: `localhost:8812`
- Health and metrics: `http://localhost:9003`

## Role In This Project

QuestDB should sit behind a data provider interface:

```text
QuestDB SQL query -> provider row model -> OhlcvBar validation -> strategy/backtest input
```

Rules:

- Strategy code must not query QuestDB directly.
- Provider code must validate symbol, timestamp, OHLCV integrity, adjustment mode, and timezone assumptions.
- Tests must use CSV fixtures by default.
- QuestDB integration tests must be opt-in and skipped unless the container is explicitly available.
- Query results should be converted to internal daily bars before reaching VectorBT or report generation.

## Suggested Daily Bar Table

```sql
CREATE TABLE IF NOT EXISTS daily_bars (
  ts TIMESTAMP,
  symbol SYMBOL,
  open DOUBLE,
  high DOUBLE,
  low DOUBLE,
  close DOUBLE,
  volume LONG,
  adjusted_close DOUBLE,
  provider SYMBOL,
  adjustment_mode SYMBOL
) TIMESTAMP(ts) PARTITION BY MONTH;
```

The internal application contract still uses `OhlcvBar`; this table is only one storage representation.

## References

- [QuestDB Docker deployment](https://questdb.com/docs/deployment/docker/)
- [QuestDB quick start](https://questdb.com/docs/getting-started/quick-start/)
