import axios from 'axios'

function resolveApiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured) return configured
  if (typeof window === 'undefined') return 'http://127.0.0.1:8100/api'
  const host = window.location.hostname
  if (!host || host === 'localhost' || host === '127.0.0.1') {
    return 'http://127.0.0.1:8100/api'
  }
  return `${window.location.protocol}//${host}:8100/api`
}

const client = axios.create({
  baseURL: resolveApiBaseUrl(),
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
  watchlist: Array<{
    symbol: string
    price: string
    change: string
    signal: string
    high24h?: string
    low24h?: string
    volume24h?: string
  }>
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

export type InstrumentOption = {
  symbol: string
  base: string
  quote: string
  marketType: string
  marketLabel: string
  label: string
}

export type InstrumentPayload = {
  source?: string
  connected?: boolean
  items: InstrumentOption[]
}

export type AiSettingsPayload = {
  enabled: boolean
  provider: string
  baseUrl: string
  model: string
  hasApiKey: boolean
  timeoutSeconds: number
}

const overviewFallback: OverviewPayload = {
  source: 'offline',
  upstreamConnected: false,
  marketPulse: [],
  watchlist: [],
  positions: [],
  activity: [],
  orderbook: {
    asks: [],
    bids: [],
    spreadText: '--',
  },
  controlState: {
    running: false,
    cooldownSeconds: 0,
    executionMode: '未连接',
    lastSync: '--',
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

const instrumentFallback: InstrumentPayload = {
  source: 'offline',
  connected: false,
  items: [],
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

export const getOverview = (instrumentId = 'BTC-USDT') =>
  withFallback(`/workbench/overview?instrument_id=${instrumentId}`, overviewFallback)
export const getExecution = () => withFallback('/execution/state', executionFallback)
export const getBacktestWorkbench = () => withFallback('/backtests/workbench', backtestFallback)
export const getMarketCandles = (instrumentId = 'BTC-USDT', timeframe = '15m', limit = 160) =>
  withFallback(`/market/candles?instrument_id=${instrumentId}&timeframe=${timeframe}&limit=${limit}`, candleFallback)
export const getMarketInstruments = (query = '', limit = 800) =>
  withFallback(`/market/instruments?q=${encodeURIComponent(query)}&limit=${limit}`, instrumentFallback)
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

/** Import a new strategy.  Sends JSON body with strategy fields. */
export async function importStrategy(payload: { label?: string; instrumentId?: string; timeframe?: string; code?: string; strategyId?: string }): Promise<Array<{ strategyId: string; versionId: string; label: string; instrumentId: string; timeframe: string; status: string; updatedAt: string }>> {
  const response = await client.post<ApiEnvelope<Array<{ strategyId: string; versionId: string; label: string; instrumentId: string; timeframe: string; status: string; updatedAt: string }>>>('/strategies/import', payload)
  return response.data.data
}

// -----------------------------------------------------------------------------
// Execution management — queue confirmation, mode switching, retry

export async function confirmExecutionQueue(id: number) {
  const response = await client.post<ApiEnvelope<{ ok: boolean; result?: any; queues: any[] }>>(`/execution/queues/${id}/confirm`)
  return response.data.data
}

export async function rejectExecutionQueue(id: number) {
  const response = await client.post<ApiEnvelope<{ ok: boolean; queues: any[] }>>(`/execution/queues/${id}/reject`)
  return response.data.data
}

export async function retryExecutionQueue(id: number) {
  const response = await client.post<ApiEnvelope<{ ok: boolean; result?: any; queues: any[] }>>(`/execution/queues/${id}/retry`)
  return response.data.data
}

export async function getExecutionMode() {
  const response = await client.get<ApiEnvelope<{ mode: string }>>('/execution/mode')
  return response.data.data
}

export async function setExecutionMode(mode: '人工确认' | '自动执行') {
  const response = await client.post<ApiEnvelope<{ mode: string; ok?: boolean; message?: string }>>('/execution/mode', { mode })
  return response.data.data
}

// -----------------------------------------------------------------------------
// Backtest templates and archives

export async function getBacktestTemplates() {
  const response = await client.get<ApiEnvelope<any[]>>('/backtests/templates')
  return response.data.data
}

export async function saveBacktestTemplate(template: { name: string; params: any }) {
  const response = await client.post<ApiEnvelope<any[]>>('/backtests/templates', template)
  return response.data.data
}

export async function getBacktestArchives() {
  const response = await client.get<ApiEnvelope<any[]>>('/backtests/archives')
  return response.data.data
}

export async function saveBacktestArchive(record: { name: string; params: any; result: any }) {
  const response = await client.post<ApiEnvelope<any[]>>('/backtests/archives', record)
  return response.data.data
}

// -----------------------------------------------------------------------------
// Strategy code editor — get/save/check code, versions, templates, publish

export type StrategyVersionItem = {
  versionId: string
  label: string
  status: string
  updatedAt: string
  note?: string
}

export type StrategyTemplateItem = {
  id: string
  label: string
  instrumentId: string
  timeframe: string
  code: string
}

export async function getStrategyCode(strategyId: string): Promise<{ strategyId: string; label?: string; code: string }> {
  const response = await client.get<ApiEnvelope<{ strategyId: string; label?: string; code: string }>>(`/strategies/${strategyId}/code`)
  return response.data.data
}

export async function saveStrategyCode(strategyId: string, code: string) {
  const response = await client.put<ApiEnvelope<{ strategyId: string; label?: string; code: string; updatedAt: string }>>(`/strategies/${strategyId}/code`, { code })
  return response.data.data
}

export async function checkStrategyCode(code: string): Promise<{ ok: boolean; errors: string[]; warnings: string[]; checkedAt: string }> {
  const response = await client.post<ApiEnvelope<{ ok: boolean; errors: string[]; warnings: string[]; checkedAt: string }>>('/strategies/check', { code })
  return response.data.data
}

export async function getStrategyVersions(strategyId: string): Promise<StrategyVersionItem[]> {
  const response = await client.get<ApiEnvelope<StrategyVersionItem[]>>(`/strategies/${strategyId}/versions`)
  return response.data.data
}

export async function saveStrategyVersion(strategyId: string, code: string, note?: string): Promise<StrategyVersionItem> {
  const response = await client.post<ApiEnvelope<StrategyVersionItem>>(`/strategies/${strategyId}/versions`, { code, note })
  return response.data.data
}

export async function publishStrategy(strategyId: string, versionId?: string) {
  const response = await client.post<ApiEnvelope<{ strategy: StrategyBoardPayload['items'][number]; queue: any }>>('/strategies/publish', { strategyId, versionId })
  return response.data.data
}

export async function getStrategyTemplates(): Promise<StrategyTemplateItem[]> {
  const response = await client.get<ApiEnvelope<StrategyTemplateItem[]>>('/strategies/templates')
  return response.data.data
}

export async function createStrategyFromTemplate(payload: { templateId?: string; label?: string; instrumentId?: string; timeframe?: string }) {
  const response = await client.post<ApiEnvelope<StrategyBoardPayload['items']>>('/strategies/templates', payload)
  return response.data.data
}

export async function saveStrategyTemplate(payload: { name: string; code?: string; instrumentId?: string; timeframe?: string }) {
  const response = await client.post<ApiEnvelope<any[]>>('/strategies/templates/save', payload)
  return response.data.data
}

export async function renameStrategyTemplate(templateId: string, newLabel: string) {
  const response = await client.put<ApiEnvelope<any[]>>(`/strategies/templates/${encodeURIComponent(templateId)}`, { new_label: newLabel })
  return response.data.data
}

export async function deleteStrategyTemplate(templateId: string) {
  const response = await client.delete<ApiEnvelope<any[]>>(`/strategies/templates/${encodeURIComponent(templateId)}`)
  return response.data.data
}

export async function getAiSettings(): Promise<AiSettingsPayload> {
  const response = await client.get<ApiEnvelope<AiSettingsPayload>>('/settings/ai')
  return response.data.data
}

export async function saveAiSettings(payload: {
  enabled: boolean
  provider: string
  baseUrl: string
  model: string
  apiKey?: string
  timeoutSeconds: number
}): Promise<AiSettingsPayload> {
  const response = await client.post<ApiEnvelope<AiSettingsPayload>>('/settings/ai', payload)
  return response.data.data
}
