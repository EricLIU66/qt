export type MarketBar = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  close_index: number;
};

export type FibonacciParams = {
  symbol: string;
  lookback: number;
  sma_window: number;
  entry_ratio: number;
  resistance_ratio: number;
  stop_ratio: number;
  initial_cash: number;
};

export type RunMetrics = {
  total_return: number;
  buy_hold_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe: number | null;
  max_drawdown: number;
  exposure: number;
  trade_events: number;
  win_rate: number | null;
};

export type RunSeriesPoint = {
  date: string;
  strategy_index: number;
  buy_hold_index: number;
  position: number;
};

export type FibonacciRun = {
  run_id: string;
  label: string;
  created_at: string;
  symbol: string;
  params: FibonacciParams;
  metrics: RunMetrics;
  latest_levels: {
    date: string;
    close: number;
    entry_support: number | null;
    resistance: number | null;
    stop_support: number | null;
    sma: number | null;
    in_position: boolean;
  };
  trade_events: Array<{
    date: string;
    side: "buy" | "sell";
    price: number;
  }>;
  series: RunSeriesPoint[];
};
