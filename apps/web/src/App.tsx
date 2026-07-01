import { Activity, BarChart3, History, Play, RefreshCw, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { FibonacciParams, FibonacciRun, MarketBar } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const COLORS = ["#0f766e", "#7c3aed", "#c2410c", "#2563eb", "#be123c", "#047857"];

const defaultParams: FibonacciParams = {
  symbol: "SPY",
  lookback: 252,
  sma_window: 200,
  entry_ratio: 0.618,
  resistance_ratio: 0.236,
  stop_ratio: 0.786,
  initial_cash: 100000
};

function formatPercent(value: number | null): string {
  return value === null ? "n/a" : `${(value * 100).toFixed(2)}%`;
}

function formatNumber(value: number | null): string {
  return value === null ? "n/a" : value.toFixed(2);
}

export function App() {
  const [bars, setBars] = useState<MarketBar[]>([]);
  const [runs, setRuns] = useState<FibonacciRun[]>([]);
  const [params, setParams] = useState<FibonacciParams>(defaultParams);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const applyRuns = useCallback((nextRuns: FibonacciRun[]) => {
    setRuns(nextRuns);
    if (nextRuns.length > 0) {
      setSelectedRunId((current) => current ?? nextRuns[nextRuns.length - 1].run_id);
    }
  }, []);

  const loadRuns = useCallback(async () => {
    const response = await fetch(`${API_BASE}/backtests`);
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const payload = (await response.json()) as { runs: FibonacciRun[] };
    applyRuns(payload.runs);
  }, [applyRuns]);

  const loadHistory = useCallback(async () => {
    const [marketResponse, runsResponse] = await Promise.all([
      fetch(`${API_BASE}/market/history?symbol=${params.symbol}`),
      fetch(`${API_BASE}/backtests`)
    ]);
    if (!marketResponse.ok) {
      throw new Error(await marketResponse.text());
    }
    if (!runsResponse.ok) {
      throw new Error(await runsResponse.text());
    }
    const marketPayload = (await marketResponse.json()) as { bars: MarketBar[] };
    const runsPayload = (await runsResponse.json()) as { runs: FibonacciRun[] };
    setBars(marketPayload.bars);
    applyRuns(runsPayload.runs);
  }, [applyRuns, params.symbol]);

  const runBacktest = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/backtests/fibonacci`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params)
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as { run: FibonacciRun; runs: FibonacciRun[] };
      applyRuns(payload.runs);
      setSelectedRunId(payload.run.run_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run backtest");
    } finally {
      setLoading(false);
    }
  }, [applyRuns, params]);

  useEffect(() => {
    setError(null);
    loadHistory().catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to load QuestDB history");
    });
  }, [loadHistory]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      loadRuns().catch(() => {
        // Keep the current UI usable if the API is briefly unavailable.
      });
    }, 2000);
    return () => window.clearInterval(timer);
  }, [loadRuns]);

  const selectedRun =
    runs.find((run) => run.run_id === selectedRunId) ?? runs[runs.length - 1] ?? null;

  const chartData = useMemo(() => {
    const data = new Map<string, Record<string, string | number>>();
    for (const bar of bars) {
      data.set(bar.date, {
        date: bar.date,
        "SPY close": bar.close_index
      });
    }
    for (const run of runs) {
      for (const point of run.series) {
        const existing = data.get(point.date) ?? { date: point.date };
        existing["Buy & hold"] = point.buy_hold_index;
        existing[run.label] = point.strategy_index;
        data.set(point.date, existing);
      }
    }
    return Array.from(data.values()).sort((left, right) =>
      String(left.date).localeCompare(String(right.date))
    );
  }, [bars, runs]);

  const runKeys = runs.map((run) => run.label);
  const latestBar = bars[bars.length - 1];

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <BarChart3 size={24} />
          <span>Quant Research</span>
        </div>
        <nav>
          <a className="active" href="#overview">
            <Activity size={18} />
            Overview
          </a>
          <a href="#history">
            <History size={18} />
            History
          </a>
          <a href="#risk">
            <ShieldCheck size={18} />
            Risk
          </a>
        </nav>

        <section className="history-panel" id="history">
          <h2>Runs</h2>
          <div className="run-list">
            {runs.map((run) => (
              <button
                className={run.run_id === selectedRun?.run_id ? "run-item active" : "run-item"}
                key={run.run_id}
                onClick={() => setSelectedRunId(run.run_id)}
                type="button"
              >
                <span>{run.label}</span>
                <strong>{formatPercent(run.metrics.total_return)}</strong>
              </button>
            ))}
          </div>
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">QuestDB / daily_bars / {params.symbol}</p>
            <h1>Fibonacci Support Research</h1>
          </div>
          <div className="run-meta">
            <span>{bars.length.toLocaleString()} daily bars</span>
            <span>
              {bars[0]?.date ?? "n/a"} to {latestBar?.date ?? "n/a"}
            </span>
          </div>
        </header>

        <form
          className="control-band"
          aria-label="Backtest controls"
          onSubmit={(event) => {
            event.preventDefault();
            void runBacktest();
          }}
        >
          <NumberField
            label="Lookback"
            value={params.lookback}
            onChange={(lookback) => setParams({ ...params, lookback })}
          />
          <NumberField
            label="SMA"
            value={params.sma_window}
            onChange={(sma_window) => setParams({ ...params, sma_window })}
          />
          <NumberField
            label="Entry"
            step={0.001}
            value={params.entry_ratio}
            onChange={(entry_ratio) => setParams({ ...params, entry_ratio })}
          />
          <NumberField
            label="Target"
            step={0.001}
            value={params.resistance_ratio}
            onChange={(resistance_ratio) => setParams({ ...params, resistance_ratio })}
          />
          <NumberField
            label="Stop"
            step={0.001}
            value={params.stop_ratio}
            onChange={(stop_ratio) => setParams({ ...params, stop_ratio })}
          />
          <button className="run-button" data-testid="rerun" disabled={loading} type="submit">
            {loading ? <RefreshCw size={18} /> : <Play size={18} />}
            Rerun
          </button>
        </form>

        {error ? <div className="error">{error}</div> : null}

        <section className="metrics" aria-label="Backtest metrics">
          <Metric label="Strategy return" value={formatPercent(selectedRun?.metrics.total_return ?? null)} />
          <Metric label="Buy & hold" value={formatPercent(selectedRun?.metrics.buy_hold_return ?? null)} />
          <Metric label="Max drawdown" value={formatPercent(selectedRun?.metrics.max_drawdown ?? null)} />
          <Metric label="Exposure" value={formatPercent(selectedRun?.metrics.exposure ?? null)} />
        </section>

        <section className="chart-panel" id="overview">
          <div className="section-heading">
            <h2>Price and Strategy Curves</h2>
            <span>Normalized index, start = 100</span>
          </div>
          <ResponsiveContainer width="100%" height={440}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d8dee4" />
              <XAxis dataKey="date" minTickGap={36} tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} width={72} />
              <Tooltip />
              <Line
                dataKey="SPY close"
                dot={false}
                isAnimationActive={false}
                stroke="#64748b"
                strokeWidth={1.4}
                type="monotone"
              />
              <Line
                dataKey="Buy & hold"
                dot={false}
                isAnimationActive={false}
                stroke="#111827"
                strokeDasharray="6 4"
                strokeWidth={1.6}
                type="monotone"
              />
              {runKeys.map((key, index) => (
                <Line
                  dataKey={key}
                  dot={false}
                  isAnimationActive={false}
                  key={key}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  type="monotone"
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </section>

        <section className="details" id="risk">
          <div>
            <h2>Latest Levels</h2>
            <dl>
              <Row label="Close" value={formatNumber(selectedRun?.latest_levels.close ?? null)} />
              <Row label="Entry support" value={formatNumber(selectedRun?.latest_levels.entry_support ?? null)} />
              <Row label="Resistance" value={formatNumber(selectedRun?.latest_levels.resistance ?? null)} />
              <Row label="Stop support" value={formatNumber(selectedRun?.latest_levels.stop_support ?? null)} />
              <Row label="SMA" value={formatNumber(selectedRun?.latest_levels.sma ?? null)} />
              <Row label="State" value={selectedRun?.latest_levels.in_position ? "long" : "cash"} />
            </dl>
          </div>
          <div>
            <h2>Selected Run</h2>
            <dl>
              <Row label="Sharpe" value={selectedRun?.metrics.sharpe?.toFixed(2) ?? "n/a"} />
              <Row label="Ann. return" value={formatPercent(selectedRun?.metrics.annualized_return ?? null)} />
              <Row label="Ann. vol" value={formatPercent(selectedRun?.metrics.annualized_volatility ?? null)} />
              <Row label="Trades" value={`${selectedRun?.metrics.trade_events ?? 0}`} />
              <Row label="Win rate" value={formatPercent(selectedRun?.metrics.win_rate ?? null)} />
              <Row label="Run id" value={selectedRun?.run_id ?? "n/a"} />
            </dl>
          </div>
        </section>
      </section>
    </main>
  );
}

function NumberField({
  label,
  onChange,
  step = 1,
  value
}: {
  label: string;
  onChange: (value: number) => void;
  step?: number;
  value: number;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        data-testid={`param-${label.toLowerCase()}`}
        onChange={(event) => onChange(Number(event.target.value))}
        step={step}
        type="number"
        value={value}
      />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-row">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
