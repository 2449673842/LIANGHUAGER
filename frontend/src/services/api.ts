import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 5000,
})

type ApiEnvelope<T> = {
  success?: boolean
  data: T
  message?: string
}

export type OverviewPayload = {
  source?: string
  upstreamConnected?: boolean
  marketPulse: Array<{ label: string; value: string; tone?: 'up' | 'down' | 'neutral' }>
  watchlist: Array<{ symbol: string; price: string; change: string; signal: string }>
  positions: Array<{ strategy: string; symbol: string; side: string; pnl: string; size: string }>
  activity: Array<{ time: string; message: string; tone?: 'up' | 'down' | 'neutral' }>
  orderbook: {
    asks: Array<[string, string]>
    bids: Array<[string, string]>
    spreadText: string
  }
  controlState: {
    running: boolean
    cooldownSeconds: number
    executionMode: string
    lastSync: string
  }
}

export type ExecutionPayload = {
  source?: string
  upstreamConnected?: boolean
  mode: 'paper' | 'live'
  accounts: Array<{ name: string; venue: string; equity: string; status: string }>
  sessions: Array<{ name: string; strategy: string; symbol: string; mode: string; state: string }>
  queues: Array<{ time: string; strategy: string; symbol: string; action: string; reason: string; state: string }>
  runtime: {
    activeTasks: number
    activeSessions: number
    pendingConfirmations: number
    notificationsSent: number
  }
}

export type BacktestPayload = {
  source?: string
  upstreamConnected?: boolean
  periods: string[]
  metrics: Array<{ label: string; value: string; tone?: 'up' | 'down' | 'neutral' }>
  trades: Array<{ time: string; side: string; price: string; reason: string }>
  equityCurve: Array<{ time: string; value: number }>
}

export type StrategyBoardPayload = {
  source?: string
  upstreamConnected?: boolean
  items: Array<{
    strategyId: string
    versionId: string
    label: string
    instrumentId: string
    timeframe: string
    status: string
    updatedAt: string
  }>
}

export type CandlePoint = {
  ts: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export type CandlePayload = {
  source?: string
  instrumentId: string
  timeframe: string
  items: CandlePoint[]
}

const overviewFallback: OverviewPayload = {
  marketPulse: [
    { label: 'BTC/USDT', value: '103,842.8', tone: 'up' },
    { label: '24h 变化', value: '+2.41%', tone: 'up' },
    { label: '活跃策略', value: '12', tone: 'neutral' },
    { label: '实时告警', value: '3', tone: 'down' },
  ],
  watchlist: [
    { symbol: 'BTC/USDT', price: '103,842.8', change: '+2.41%', signal: '趋势延续' },
    { symbol: 'ETH/USDT', price: '4,978.2', change: '+1.34%', signal: '突破回踩' },
    { symbol: 'SOL/USDT', price: '238.7', change: '-0.84%', signal: '观望' },
    { symbol: 'DOGE/USDT', price: '0.2281', change: '+4.92%', signal: '量价共振' },
  ],
  positions: [
    { strategy: '趋势跟随-A', symbol: 'BTC/USDT', side: '做多', pnl: '+842.40', size: '0.75 BTC' },
    { strategy: '突破回踩-B', symbol: 'ETH/USDT', side: '做多', pnl: '+192.60', size: '8 ETH' },
    { strategy: '均值回归-C', symbol: 'SOL/USDT', side: '做空', pnl: '-54.22', size: '320 SOL' },
  ],
  activity: [
    { time: '09:42:18', message: 'BTC/USDT 触发 15m 做多加仓信号', tone: 'up' },
    { time: '09:37:06', message: 'ETH/USDT 实盘策略进入人工确认队列', tone: 'neutral' },
    { time: '09:32:44', message: 'SOL/USDT 触发保护止损', tone: 'down' },
    { time: '09:29:11', message: '邮件告警发送成功: trend-follow-btc', tone: 'neutral' },
  ],
  orderbook: {
    asks: [
      ['103845.2', '12.84'],
      ['103844.6', '9.22'],
      ['103844.1', '5.90'],
      ['103843.7', '4.11'],
      ['103843.2', '2.34'],
    ],
    bids: [
      ['103842.5', '10.71'],
      ['103842.0', '8.19'],
      ['103841.4', '7.88'],
      ['103840.9', '4.70'],
      ['103840.4', '3.16'],
    ],
    spreadText: '2.7 (0.003%)',
  },
  controlState: {
    running: true,
    cooldownSeconds: 124,
    executionMode: '人工确认',
    lastSync: '2026-05-16 09:42:24',
  },
}

const executionFallback: ExecutionPayload = {
  mode: 'paper',
  accounts: [
    { name: 'OKX 主账户', venue: 'OKX', equity: '128,420.33 USDT', status: '在线' },
    { name: 'OKX Alpha', venue: 'OKX', equity: '48,210.11 USDT', status: '待确认' },
  ],
  sessions: [
    { name: 'paper-btc-grid', strategy: '趋势跟随-A', symbol: 'BTC/USDT', mode: '模拟', state: '运行中' },
    { name: 'live-eth-breakout', strategy: '突破回踩-B', symbol: 'ETH/USDT', mode: '实盘', state: '人工确认' },
    { name: 'live-sol-mean', strategy: '均值回归-C', symbol: 'SOL/USDT', mode: '实盘', state: '告警中' },
  ],
  queues: [
    { time: '09:37:06', strategy: '突破回踩-B', symbol: 'ETH/USDT', action: '开多', reason: '1H 突破确认', state: '待确认' },
    { time: '09:34:18', strategy: '趋势跟随-A', symbol: 'BTC/USDT', action: '加仓', reason: '15m 二次放量', state: '已发送' },
    { time: '09:31:55', strategy: '均值回归-C', symbol: 'SOL/USDT', action: '平空', reason: '止盈到达', state: '待确认' },
  ],
  runtime: {
    activeTasks: 4,
    activeSessions: 7,
    pendingConfirmations: 2,
    notificationsSent: 18,
  },
}

const backtestFallback: BacktestPayload = {
  periods: ['1M', '3M', '6M', '1Y'],
  metrics: [
    { label: '净收益', value: '+24.8%', tone: 'up' },
    { label: '最大回撤', value: '-7.4%', tone: 'down' },
    { label: 'Sharpe', value: '1.82', tone: 'up' },
    { label: '胜率', value: '58.3%', tone: 'neutral' },
  ],
  trades: [
    { time: '2026-04-12 13:45', side: '买入', price: '101,224', reason: '15m 突破' },
    { time: '2026-04-13 09:30', side: '卖出', price: '103,118', reason: '止盈' },
    { time: '2026-04-15 22:10', side: '卖出', price: '100,840', reason: '反转确认' },
  ],
  equityCurve: [
    { time: '2026-04-01', value: 10000 },
    { time: '2026-04-04', value: 10180 },
    { time: '2026-04-08', value: 10340 },
    { time: '2026-04-12', value: 10490 },
    { time: '2026-04-16', value: 10680 },
    { time: '2026-04-20', value: 10810 },
    { time: '2026-04-24', value: 11140 },
    { time: '2026-04-28', value: 11410 },
    { time: '2026-05-02', value: 11760 },
    { time: '2026-05-06', value: 12110 },
    { time: '2026-05-10', value: 12390 },
    { time: '2026-05-14', value: 12480 },
  ],
}

function buildFallbackCandles(limit = 160): CandlePoint[] {
  return Array.from({ length: limit }, (_, index) => {
    const base = 96000
    const drift = (index % 11 - 5) * 82
    const open = base + drift + index * 17
    const close = open + ((index % 7) - 3) * 46
    const high = Math.max(open, close) + 110 + (index % 5) * 16
    const low = Math.min(open, close) - 95 - (index % 4) * 21
    return {
      ts: 1714550400000 + index * 900000,
      open,
      high,
      low,
      close,
      volume: 220 + (index % 9) * 38 + index * 0.8,
    }
  })
}

const candleFallback: CandlePayload = {
  source: 'fallback',
  instrumentId: 'BTC-USDT',
  timeframe: '15m',
  items: buildFallbackCandles(),
}

const strategyBoardFallback: StrategyBoardPayload = {
  source: 'fallback',
  upstreamConnected: false,
  items: [
    {
      strategyId: 'trend_follow_btc',
      versionId: 'trend_follow_btc:v1.2.0',
      label: '趋势跟随-A',
      instrumentId: 'BTC-USDT',
      timeframe: '15m',
      status: '已发布',
      updatedAt: '2026-05-16 09:20',
    },
    {
      strategyId: 'breakout_eth',
      versionId: 'breakout_eth:v0.9.4',
      label: '突破回踩-B',
      instrumentId: 'ETH-USDT',
      timeframe: '1H',
      status: '待审核',
      updatedAt: '2026-05-16 08:42',
    },
    {
      strategyId: 'mean_revert_sol',
      versionId: 'mean_revert_sol:v2.1.1',
      label: '均值回归-C',
      instrumentId: 'SOL-USDT',
      timeframe: '15m',
      status: '运行中',
      updatedAt: '2026-05-15 22:31',
    },
  ],
}

// Cache of the last successful payload per path. When a request fails, the cached
// payload will be used instead of immediately falling back to static data. This
// prevents the UI from reverting to old mock data after a transient network
// issue and keeps the live data on screen as long as possible.
const lastGoodPayload = new Map<string, unknown>()

async function withFallback<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await client.get<{ success?: boolean; data: T }>(path)
    // Only treat the response as valid when the optional success flag is not false
    // and the data property exists. Some upstream responses omit the success flag.
    if (response.data?.success !== false && response.data?.data) {
      lastGoodPayload.set(path, response.data.data)
      return response.data.data
    }
    // Fall back to last good payload when response is invalid
    const lastGood = lastGoodPayload.get(path) as T | undefined
    return lastGood ?? fallback
  } catch (error) {
    // Log the error and return the last good payload or fallback. Do not
    // propagate the error to prevent unhandled rejections in the UI.
    console.warn(`[api] request failed, keeping last good payload: ${path}`, error)
    const lastGood = lastGoodPayload.get(path) as T | undefined
    return lastGood ?? fallback
  }
}

export const getOverview = () => withFallback('/workbench/overview', overviewFallback)
export const getExecution = () => withFallback('/execution/state', executionFallback)
export const getBacktestWorkbench = () => withFallback('/backtests/workbench', backtestFallback)
export const getMarketCandles = (instrumentId = 'BTC-USDT', timeframe = '15m', limit = 160) =>
  withFallback(`/market/candles?instrument_id=${instrumentId}&timeframe=${timeframe}&limit=${limit}`, candleFallback)
export const getStrategyBoard = (limit = 12) => withFallback(`/strategies/board?limit=${limit}`, strategyBoardFallback)

// -------------------------
// Watchlist and monitoring
//
// These helper functions call the new backend endpoints added to support
// user‑customizable watchlists and monitoring state.  They do not use
// `withFallback` because the responses are simple and should not fall back
// to cached data when a call fails.  Instead, errors are thrown so the
// caller can handle them appropriately (e.g. by showing a toast).

/** Fetch the current watchlist symbols. */
export async function getWatchlistSymbols(): Promise<string[]> {
  const response = await client.get<ApiEnvelope<string[]>>('/watchlist')
  return response.data.data
}

/** Add a symbol to the watchlist.  The symbol may include '/' or '-'. */
export async function addWatchlistSymbol(symbol: string): Promise<string[]> {
  const response = await client.post<ApiEnvelope<string[]>>('/watchlist', { symbol })
  return response.data.data
}

/** Remove a symbol from the watchlist via query string. */
export async function removeWatchlistSymbol(symbol: string): Promise<string[]> {
  const response = await client.delete<ApiEnvelope<string[]>>('/watchlist', { params: { symbol } })
  return response.data.data
}

/** Get the current monitoring state from the backend. */
export async function getMonitoringState(): Promise<{ running: boolean }> {
  const response = await client.get<ApiEnvelope<{ running: boolean }>>('/monitoring/state')
  return response.data.data
}

/** Set the monitoring state to running or stopped. */
export async function setMonitoringState(running: boolean): Promise<{ running: boolean }> {
  const response = await client.post<ApiEnvelope<{ running: boolean }>>('/monitoring/state', { running })
  return response.data.data
}

// -----------------------------------------------------------------------------
// Execution page helper functions
// These functions call the new execution endpoints for managing accounts and
// queue items.  They return the updated lists directly without applying
// fallback caching.

/** Fetch all execution accounts. */
export async function getAccounts() {
  const response = await client.get<ApiEnvelope<Array<{ name: string; venue: string; equity: string; status: string }>>>('/execution/accounts')
  return response.data.data
}

/** Add a new execution account.  Fields are optional; defaults will be provided. */
export async function addAccount(account: { name?: string; venue?: string; equity?: string; status?: string }) {
  const response = await client.post<ApiEnvelope<Array<{ name: string; venue: string; equity: string; status: string }>>>('/execution/accounts', account)
  return response.data.data
}

/** Fetch the current execution queue. */
export async function getExecutionQueue() {
  const response = await client.get<ApiEnvelope<Array<{ time: string; strategy: string; symbol: string; action: string; reason: string; state: string }>>>('/execution/queues')
  return response.data.data
}

/** Add a new task to the execution queue.  Missing fields are defaulted. */
export async function addExecutionQueue(item: { strategy?: string; symbol?: string; action?: string; reason?: string }) {
  const response = await client.post<ApiEnvelope<Array<{ time: string; strategy: string; symbol: string; action: string; reason: string; state: string }>>>('/execution/queues', item)
  return response.data.data
}

/** Run a backtest with custom parameters.  Accepts at least a `period` field. */
export async function runBacktest(params: { period: string; [key: string]: any }): Promise<BacktestPayload> {
  const response = await client.post<ApiEnvelope<BacktestPayload>>('/backtests/run', params)
  return response.data.data
}

/** Import a new strategy.  Accepts a query object with at least a `label` field. */
export async function importStrategy(params: { [key: string]: any }): Promise<Array<{ strategyId: string; versionId: string; label: string; instrumentId: string; timeframe: string; status: string; updatedAt: string }>> {
  const response = await client.post<ApiEnvelope<Array<{ strategyId: string; versionId: string; label: string; instrumentId: string; timeframe: string; status: string; updatedAt: string }>>>('/strategies/import', null, { params })
  return response.data.data
}
