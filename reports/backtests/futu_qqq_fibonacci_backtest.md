# QQQ Fibonacci Support/Resistance Backtest

- Generated at: 2026-06-30T08:12:12
- Data source: Futu OpenD `request_history_kline`, daily K, forward-adjusted prices.
- Requested range: 1997-01-01 to 2026-06-30
- Actual data returned: 2006-06-15 to 2026-06-29 (5040 rows)
- Instrument: `US.QQQ`

## Strategy

- Rolling lookback: 252 trading days.
- Fibonacci levels use the prior day's rolling high/low to avoid look-ahead bias.
- Entry: close crosses above the 61.8% retracement support and close is above prior 200-day SMA.
- Exit: close reaches 23.6% resistance, breaks below 78.6% support, or closes below prior 200-day SMA.
- Positioning: long/cash only, no shorting, no leverage, no fees/slippage in this first pass.
- Signal timing: close generates signal; position is applied to the next day's return.

## Performance

- Strategy total return: 7.91%
- Buy-and-hold total return: 2134.70%
- Annualized return: 0.38%
- Annualized volatility: 3.49%
- Sharpe, rf=0: 0.13
- Max drawdown: -8.49%
- Exposure: 2.70%
- Trade events: 10
- Round-trip win rate: 40.00%

## Latest Fibonacci Levels

- Date: 2026-06-29
- Close: 724.08
- 23.6% resistance: 698.53
- 38.2% level: 668.03
- 50.0% level: 643.38
- 61.8% support: 618.73
- 78.6% stop support: 583.63
- 200-day SMA: 630.66
- Current strategy state: cash

## Recent Trade Events

| Date | Side | Price |
|---|---:|---:|
| 2009-05-04 | buy | 29.64 |
| 2009-05-13 | sell | 27.88 |
| 2009-05-26 | buy | 29.41 |
| 2009-09-04 | sell | 34.28 |
| 2020-03-10 | buy | 195.86 |
| 2020-03-11 | sell | 187.30 |
| 2023-02-01 | buy | 294.48 |
| 2023-03-10 | sell | 282.38 |
| 2023-03-15 | buy | 292.53 |
| 2023-04-27 | sell | 313.98 |

## Caveats

- Futu returned data starting at the actual coverage date above, not 1997.
- This first pass excludes commissions, spreads, slippage, tax, and dividend cash-flow modeling beyond Futu's forward-adjusted price series.
- This is research output, not investment advice and not a live trading signal.
