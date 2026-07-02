from __future__ import annotations

import argparse
import json
import socket
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def questdb_exec(http_url: str, query: str) -> dict[str, Any]:
    url = f"{http_url.rstrip('/')}/exec?{urlencode({'query': query})}"
    with urlopen(url, timeout=30) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if "error" in data:
        raise RuntimeError(f"QuestDB query failed: {data['error']} ({query})")
    return data


def questdb_existing_tables(http_url: str) -> list[str]:
    result = questdb_exec(http_url, "show tables")
    return [str(row[0]) for row in result.get("dataset", [])]


def reset_questdb_database(http_url: str) -> list[str]:
    dropped = questdb_existing_tables(http_url)
    for table in dropped:
        questdb_exec(http_url, f'DROP TABLE IF EXISTS "{table}"')

    questdb_exec(
        http_url,
        """
        CREATE TABLE daily_bars (
          ts TIMESTAMP,
          symbol SYMBOL,
          open DOUBLE,
          high DOUBLE,
          low DOUBLE,
          close DOUBLE,
          volume LONG,
          turnover DOUBLE,
          provider SYMBOL,
          adjustment_mode SYMBOL,
          ingested_at TIMESTAMP
        ) TIMESTAMP(ts) PARTITION BY MONTH
        """,
    )
    return dropped


def fetch_futu_daily_bars(code: str, start: str, end: str) -> list[dict[str, Any]]:
    try:
        from futu import AuType, KLType, OpenQuoteContext, RET_OK, Session
    except ModuleNotFoundError as exc:
        raise RuntimeError("futu-api is not installed") from exc

    ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
    try:
        page_req_key = None
        frames = []
        while True:
            ret, data, page_req_key = ctx.request_history_kline(
                code,
                start=start,
                end=end,
                ktype=KLType.K_DAY,
                autype=AuType.QFQ,
                max_count=1000,
                page_req_key=page_req_key,
                session=Session.NONE,
            )
            if ret != RET_OK:
                raise RuntimeError(f"Futu request_history_kline failed: {data}")
            frames.append(data)
            if page_req_key is None:
                break

        import pandas as pd

        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if df.empty:
            return []
        df = df.sort_values("time_key").drop_duplicates(subset=["time_key"])
        records: list[dict[str, Any]] = []
        for row in df.to_dict(orient="records"):
            records.append(
                {
                    "date": str(row["time_key"])[:10],
                    "symbol": code.split(".", 1)[1],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["volume"]),
                    "turnover": float(row.get("turnover", 0.0)),
                }
            )
        return records
    finally:
        ctx.close()


def ns_timestamp(day: str) -> int:
    dt = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def ilp_escape_tag(value: str) -> str:
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")


def ilp_line(record: dict[str, Any], ingested_at_ns: int) -> str:
    symbol = ilp_escape_tag(str(record["symbol"]))
    return (
        f"daily_bars,symbol={symbol},provider=FUTU,adjustment_mode=forward "
        f"open={record['open']},"
        f"high={record['high']},"
        f"low={record['low']},"
        f"close={record['close']},"
        f"volume={record['volume']}i,"
        f"turnover={record['turnover']},"
        f"ingested_at={ingested_at_ns}t "
        f"{ns_timestamp(record['date'])}"
    )


def write_ilp(host: str, port: int, records: list[dict[str, Any]]) -> None:
    ingested_at_ns = int(datetime.now(tz=timezone.utc).timestamp() * 1_000_000_000)
    payload = "\n".join(ilp_line(record, ingested_at_ns) for record in records) + "\n"
    with socket.create_connection((host, port), timeout=30) as sock:
        sock.sendall(payload.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--code", default="US.SPY")
    parser.add_argument("--start", default="1997-01-01")
    parser.add_argument("--end", default=date.today().isoformat())
    args = parser.parse_args()

    env = read_env(Path(args.env_file))
    http_url = env.get("QUESTDB_HTTP_URL", "http://localhost:9000")
    ilp_host = env.get("QUESTDB_ILP_HOST", "localhost")
    ilp_port = int(env.get("QUESTDB_ILP_PORT", "9009"))

    dropped = reset_questdb_database(http_url)
    records = fetch_futu_daily_bars(args.code, args.start, args.end)
    if not records:
        raise RuntimeError("Futu OpenD returned no SPY daily bars")

    write_ilp(ilp_host, ilp_port, records)

    # QuestDB commits ILP asynchronously; wait briefly for table visibility.
    summary = None
    for _ in range(20):
        summary = questdb_exec(
            http_url,
            """
            SELECT
              count() AS rows,
              min(ts) AS first_ts,
              max(ts) AS last_ts,
              min(close) AS min_close,
              max(close) AS max_close
            FROM daily_bars
            """,
        )
        rows = summary.get("dataset", [[0]])[0][0]
        if rows == len(records):
            break
        time.sleep(0.5)

    print(
        json.dumps(
            {
                "dropped_tables": dropped,
                "created_table": "daily_bars",
                "inserted_records": len(records),
                "requested": {"code": args.code, "start": args.start, "end": args.end},
                "actual": {
                    "start": records[0]["date"],
                    "end": records[-1]["date"],
                },
                "questdb_summary": summary,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
