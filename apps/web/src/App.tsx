import { Activity, BarChart3, ShieldCheck } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { BacktestRun } from "./types";

const demoRun: BacktestRun = {
  run_id: "demo",
  strategy_name: "demo_moving_average",
  symbols: ["SPY"],
  start: "2024-01-02",
  end: "2024-01-05",
  engine: "internal",
  schema_version: "1.0",
  parameters: { fast_window: 20, slow_window: 100 },
  metrics: {
    total_return: 0.024,
    annualized_return: 6.39,
    annualized_volatility: 0.14,
    sharpe: 2.1,
    max_drawdown: -0.0049,
    exposure: 0.8,
    win_rate: null
  },
  equity_curve: [
    { date: "2024-01-02", equity: 100000, cash: 20000, exposure: 0.8 },
    { date: "2024-01-03", equity: 101200, cash: 20000, exposure: 0.8 },
    { date: "2024-01-04", equity: 100700, cash: 20000, exposure: 0.8 },
    { date: "2024-01-05", equity: 102400, cash: 20000, exposure: 0.8 }
  ],
  drawdowns: [
    { date: "2024-01-02", drawdown: 0 },
    { date: "2024-01-03", drawdown: 0 },
    { date: "2024-01-04", drawdown: -0.0049 },
    { date: "2024-01-05", drawdown: 0 }
  ],
  benchmark: {
    benchmark_symbol: "SPY",
    strategy_total_return: 0.024,
    benchmark_total_return: 0.018,
    excess_return: 0.006,
    correlation: null
  }
};

function formatPercent(value: number | null): string {
  return value === null ? "n/a" : `${(value * 100).toFixed(2)}%`;
}

export function App() {
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
          <a href="#risk">
            <ShieldCheck size={18} />
            Risk
          </a>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              {demoRun.engine} / schema {demoRun.schema_version}
            </p>
            <h1>{demoRun.strategy_name}</h1>
          </div>
          <div className="run-meta">
            <span>{demoRun.symbols.join(", ")}</span>
            <span>
              {demoRun.start} to {demoRun.end}
            </span>
          </div>
        </header>

        <section className="metrics" aria-label="Backtest metrics">
          <Metric label="Total return" value={formatPercent(demoRun.metrics.total_return)} />
          <Metric
            label="Annualized return"
            value={formatPercent(demoRun.metrics.annualized_return)}
          />
          <Metric label="Max drawdown" value={formatPercent(demoRun.metrics.max_drawdown)} />
          <Metric label="Sharpe" value={demoRun.metrics.sharpe?.toFixed(2) ?? "n/a"} />
        </section>

        <section className="chart-panel" id="overview">
          <div className="section-heading">
            <h2>Equity Curve</h2>
            <span>Daily ETF research view</span>
          </div>
          <ResponsiveContainer width="100%" height={360}>
            <AreaChart data={demoRun.equity_curve}>
              <defs>
                <linearGradient id="equity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0f766e" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#0f766e" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#d8dee4" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} width={84} />
              <Tooltip />
              <Area type="monotone" dataKey="equity" stroke="#0f766e" fill="url(#equity)" />
            </AreaChart>
          </ResponsiveContainer>
        </section>

        <section className="details" id="risk">
          <div>
            <h2>Benchmark</h2>
            <p>
              Excess return vs {demoRun.benchmark?.benchmark_symbol}:{" "}
              <strong>{formatPercent(demoRun.benchmark?.excess_return ?? null)}</strong>
            </p>
          </div>
          <div>
            <h2>Parameters</h2>
            <pre>{JSON.stringify(demoRun.parameters, null, 2)}</pre>
          </div>
        </section>
      </section>
    </main>
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
