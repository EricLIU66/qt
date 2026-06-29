export type EquityPoint = {
  date: string;
  equity: number;
  cash: number;
  exposure: number;
};

export type DrawdownPoint = {
  date: string;
  drawdown: number;
};

export type MetricSummary = {
  total_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe: number | null;
  max_drawdown: number;
  exposure: number;
  win_rate: number | null;
};

export type BenchmarkComparison = {
  benchmark_symbol: string;
  strategy_total_return: number;
  benchmark_total_return: number;
  excess_return: number;
  correlation: number | null;
};

export type BacktestRun = {
  run_id: string;
  strategy_name: string;
  symbols: string[];
  start: string;
  end: string;
  metrics: MetricSummary;
  equity_curve: EquityPoint[];
  drawdowns: DrawdownPoint[];
  benchmark: BenchmarkComparison | null;
  parameters: Record<string, string | number | boolean>;
  engine: string;
  schema_version: string;
};
