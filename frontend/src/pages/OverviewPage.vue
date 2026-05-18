<template>
  <section class="page">
    <Transition name="toast">
      <div v-if="toast.visible" class="toast" :class="`toast--${toast.tone}`">
        {{ toast.message }}
      </div>
    </Transition>

    <div class="page__header">
      <div class="page__title">
        <h1>总览终端</h1>
        <p>把 K 线、盘口、信号、持仓、运行动态收进一个工作台首页。</p>
      </div>
      <div class="page__actions">
        <span class="mini-badge">{{ selectedInstrument }}</span>
        <span class="mini-badge">{{ sourceLabel(overview.source) }}</span>
        <span class="mini-badge">行情 0.5s / K线 1s</span>
        <button class="button" @click="openAddSymbol">添加自选</button>
        <button class="button" @click="manualRefresh()">{{ refreshing ? '刷新中' : '同步数据' }}</button>
        <button class="button button--primary" @click="toggleMonitoring">
          {{ monitoring ? '停止监控' : '启动监控' }}
        </button>
      </div>
    </div>

    <div class="market-marquee" aria-label="自选行情">
      <div class="market-track">
      <button
        v-for="item in marketRows"
        :key="`${item.symbol}-${item.repeatKey}`"
        class="market-card"
        :class="[
          marketToneClass(item.change),
          { 'market-card--active': normalizeSymbol(item.symbol) === selectedInstrument },
        ]"
        @click="selectInstrument(item.symbol)"
      >
        <div class="market-card__top">
          <strong>{{ item.symbol }}</strong>
          <span :class="changeToneClass(item.change)">{{ item.change }}</span>
        </div>
        <div class="market-card__price" :class="changeToneClass(item.change)">{{ item.price }}</div>
        <div class="market-card__details">
          <span>高 {{ item.high24h || '--' }}</span>
          <span>低 {{ item.low24h || '--' }}</span>
          <span>额 {{ item.volume24h || '--' }}</span>
        </div>
      </button>
      </div>
    </div>

    <div class="activity-marquee" aria-label="运行动态">
      <div class="activity-track">
        <div v-for="item in activityRows" :key="`${item.time}-${item.message}-${item.repeatKey}`" class="activity-card">
          <div>
            <strong>{{ item.time }}</strong>
            <span>{{ item.message }}</span>
          </div>
          <em :class="changeToneClass(item.tone === 'down' ? '-' : item.tone === 'up' ? '+' : '')">●</em>
        </div>
      </div>
    </div>

    <TerminalOverview
      :overview="overview"
      :candles="candles.items"
      :instrument-label="candles.instrumentId.replace('-', '/')"
      :timeframe-label="candles.timeframe"
      :selected-instrument="selectedInstrument"
      :selected-timeframe="selectedTimeframe"
      :candle-source="sourceLabel(candles.source)"
      :last-refresh-text="lastRefreshText"
      :refreshing="refreshing"
      :watchlist-busy="watchlistBusy"
      @refresh-candles="handleRefreshCandles"
      @select-instrument="selectInstrument"
      @remove-symbol="removeSymbol"
      @change-timeframe="changeTimeframe"
      @toggle-monitoring="toggleMonitoring"
    />

    <ModalDialog
      :visible="addSymbolVisible"
      title="添加自选标的"
      subtitle="输入币种或交易对，实时查询 OKX 可交易标的"
      :hide-confirm="true"
      width="560px"
      @cancel="addSymbolVisible = false"
    >
      <div class="instrument-search">
        <div class="instrument-search__box">
          <input
            v-model="symbolSearch"
            placeholder="输入 L / BTC / ETH / LAB..."
            @input="queueInstrumentSearch"
            @keyup.enter="addFirstInstrument"
          />
          <span class="mini-badge">{{ instrumentLoading ? '查询中' : instrumentSourceLabel }}</span>
        </div>
        <div class="instrument-results">
          <button
            v-for="item in instrumentResults"
            :key="`${item.symbol}-${item.marketType}`"
            class="instrument-result"
            @click="addInstrument(item.symbol)"
          >
            <div>
              <strong>{{ item.symbol }}</strong>
              <span>{{ item.base }}/{{ item.quote }}</span>
            </div>
            <em>{{ item.marketLabel }}</em>
          </button>
          <div v-if="!instrumentLoading && instrumentResults.length === 0" class="instrument-empty">
            {{ symbolSearch.trim() ? '没有查到 OKX 标的，或当前 OKX 标的接口暂不可用' : '输入关键词后开始查询 OKX 标的' }}
          </div>
        </div>
      </div>
      <div class="modal-card__actions">
        <button class="button" @click="addSymbolVisible = false">关闭</button>
      </div>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import TerminalOverview from '../components/terminal/TerminalOverview.vue'
import ModalDialog from '../components/cards/ModalDialog.vue'
import {
  getMarketCandles,
  getMarketInstruments,
  getOverview,
  getMonitoringState,
  setMonitoringState,
  addWatchlistSymbol,
  removeWatchlistSymbol,
  type InstrumentOption,
  type CandlePayload,
  type OverviewPayload,
} from '../services/api'

const overview = ref<OverviewPayload>({
  marketPulse: [],
  watchlist: [],
  positions: [],
  activity: [],
  orderbook: { asks: [], bids: [], spreadText: '--' },
  controlState: { running: false, cooldownSeconds: 0, executionMode: '--', lastSync: '--' },
})
const candles = ref<CandlePayload>({
  instrumentId: 'BTC-USDT',
  timeframe: '15m',
  items: [],
})
const selectedInstrument = ref('BTC-USDT')
const selectedTimeframe = ref('15m')
const refreshing = ref(false)
const lastRefreshText = ref('--')
const symbolSearch = ref('')
const instrumentResults = ref<InstrumentOption[]>([])
const instrumentLoading = ref(false)
const instrumentSource = ref('offline')
const watchlistBusy = ref(false)
let searchTimer: number | null = null
let timer: number | null = null
let candleTimer: number | null = null
let toastTimer: number | null = null
let overviewLoading = false
let candleLoading = false

const monitoring = ref(false)
const toast = reactive({
  visible: false,
  message: '',
  tone: 'neutral' as 'neutral' | 'success' | 'error',
})

const marketRows = computed(() => [
  ...overview.value.watchlist.map((item, index) => ({ ...item, repeatKey: `a-${index}` })),
  ...overview.value.watchlist.map((item, index) => ({ ...item, repeatKey: `b-${index}` })),
])

const activityRows = computed(() => [
  ...overview.value.activity.map((item, index) => ({ ...item, repeatKey: `a-${index}` })),
  ...overview.value.activity.map((item, index) => ({ ...item, repeatKey: `b-${index}` })),
])

const instrumentSourceLabel = computed(() => {
  if (instrumentSource.value === 'okx-cli') return 'OKX CLI'
  if (instrumentSource.value === 'okx-public') return 'OKX REST'
  if (instrumentSource.value === 'offline') return '等待查询'
  if (instrumentSource.value === 'fallback') return '接口不可用'
  return instrumentSource.value
})

function normalizeSymbol(symbol: string) {
  return symbol.replace(/\//g, '-').toUpperCase()
}

function parseSymbolInput(value: string) {
  return normalizeSymbol(value.split('·')[0].trim().split(/\s+/)[0] || value)
}

function stampRefresh() {
  lastRefreshText.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

function sourceLabel(source?: string) {
  if (!source) return '连接中'
  if (source === 'offline') return '后端未连接'
  if (source === 'fallback') return '等待实时行情'
  if (source === 'okx-cli') return 'OKX CLI'
  if (source === 'okx-public') return 'OKX REST'
  if (source === 'upstream') return '上游平台'
  return source
}

function changeToneClass(change: string) {
  if (change.startsWith('-')) return 'tone-down'
  if (change.startsWith('+')) return 'tone-up'
  return 'tone-neutral'
}

function marketToneClass(change: string) {
  if (change.startsWith('-')) return 'market-card--down'
  if (change.startsWith('+')) return 'market-card--up'
  return 'market-card--neutral'
}

function makePendingWatchRow(symbol: string) {
  return {
    symbol: symbol.replace(/-/g, '/'),
    price: '--',
    change: '--',
    high24h: '--',
    low24h: '--',
    volume24h: '--',
    signal: '等待行情',
  }
}

function mergeWatchlistSymbols(symbols: string[]) {
  const currentRows = new Map(overview.value.watchlist.map((item) => [normalizeSymbol(item.symbol), item]))
  overview.value = {
    ...overview.value,
    watchlist: symbols.map((symbol) => {
      const normalized = normalizeSymbol(symbol)
      return currentRows.get(normalized) || makePendingWatchRow(normalized)
    }),
  }
}

function showToast(message: string, tone: 'neutral' | 'success' | 'error' = 'neutral') {
  toast.message = message
  toast.tone = tone
  toast.visible = true
  if (toastTimer !== null) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toast.visible = false
  }, 2600)
}

function mergeOverviewPayload(current: OverviewPayload, next: OverviewPayload): OverviewPayload {
  return {
    ...current,
    ...next,
    marketPulse: next.marketPulse.length ? next.marketPulse : current.marketPulse,
    watchlist: next.watchlist.length ? next.watchlist : current.watchlist,
    positions: next.positions.length ? next.positions : current.positions,
    activity: next.activity.length ? next.activity : current.activity,
    orderbook: next.orderbook?.asks?.length || next.orderbook?.bids?.length ? next.orderbook : current.orderbook,
    controlState: {
      ...current.controlState,
      ...next.controlState,
      running: next.source === 'offline' ? current.controlState.running : next.controlState.running,
    },
  }
}

async function loadOverview() {
  if (overviewLoading) return
  overviewLoading = true
  try {
  const overviewData = await getOverview(selectedInstrument.value)
  overview.value = mergeOverviewPayload(overview.value, overviewData)
  if (overviewData.source !== 'offline') {
    monitoring.value = Boolean(overviewData.controlState?.running)
  }
  stampRefresh()
  } finally {
    overviewLoading = false
  }
}

async function loadCandles() {
  if (candleLoading) return
  candleLoading = true
  try {
  const candleData = await getMarketCandles(selectedInstrument.value, selectedTimeframe.value)
  candles.value = candleData
  stampRefresh()
  } finally {
    candleLoading = false
  }
}

async function manualRefresh(showDoneToast = true) {
  refreshing.value = true
  try {
    await Promise.all([loadOverview(), loadCandles()])
    if (showDoneToast) showToast('总览数据已同步', 'success')
  } catch (error) {
    showToast('同步失败，请检查后端服务', 'error')
  } finally {
    refreshing.value = false
  }
}

async function handleRefreshCandles() {
  refreshing.value = true
  try {
    await loadCandles()
    showToast('K 线已刷新', 'success')
  } catch (error) {
    showToast('K 线刷新失败', 'error')
  } finally {
    refreshing.value = false
  }
}

async function loadMonitoring() {
  const state = await getMonitoringState()
  monitoring.value = state.running
}

async function toggleMonitoring() {
  const newState = !monitoring.value
  await setMonitoringState(newState)
  monitoring.value = newState
  await loadOverview()
  showToast(newState ? '监控已启动' : '监控已停止', 'success')
}

async function selectInstrument(symbol: string) {
  selectedInstrument.value = normalizeSymbol(symbol)
  await manualRefresh()
}

async function changeTimeframe(timeframe: string) {
  selectedTimeframe.value = timeframe
  await handleRefreshCandles()
}

async function removeSymbol(symbol: string) {
  const normalized = normalizeSymbol(symbol)
  watchlistBusy.value = true
  try {
    const symbols = await removeWatchlistSymbol(normalized)
    mergeWatchlistSymbols(symbols)
    if (selectedInstrument.value === normalized) {
      selectedInstrument.value = normalizeSymbol(overview.value.watchlist[0]?.symbol || 'BTC-USDT')
    }
    showToast(`${normalized} 已从自选移除`, 'success')
    void manualRefresh(false)
  } catch (error) {
    console.error('移除自选失败', error)
    showToast('移除自选失败，请检查后端服务', 'error')
  } finally {
    watchlistBusy.value = false
  }
}

// --- add symbol modal ---
const addSymbolVisible = ref(false)

async function searchInstruments(query = symbolSearch.value) {
  const q = query.trim()
  if (!q) {
    instrumentResults.value = []
    instrumentSource.value = 'offline'
    return
  }
  instrumentLoading.value = true
  try {
    const payload = await getMarketInstruments(q, 80)
    instrumentResults.value = payload.items
    instrumentSource.value = payload.source || 'offline'
  } finally {
    instrumentLoading.value = false
  }
}

function queueInstrumentSearch() {
  if (searchTimer !== null) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    void searchInstruments()
  }, 180)
}

function openAddSymbol() {
  addSymbolVisible.value = true
  symbolSearch.value = ''
  instrumentResults.value = []
  instrumentSource.value = 'offline'
}

async function addInstrument(rawSymbol: string) {
  const symbol = parseSymbolInput(rawSymbol)
  if (!symbol) return
  const normalized = symbol
  addSymbolVisible.value = false
  watchlistBusy.value = true
  if (!overview.value.watchlist.some((item) => normalizeSymbol(item.symbol) === normalized)) {
    overview.value = {
      ...overview.value,
      watchlist: [...overview.value.watchlist, makePendingWatchRow(normalized)],
    }
  }
  selectedInstrument.value = normalized
  try {
    const symbols = await addWatchlistSymbol(normalized)
    mergeWatchlistSymbols(symbols)
    showToast(`${normalized} 已添加到自选`, 'success')
    void manualRefresh(false)
  } catch (error) {
    console.error('添加自选失败', error)
    overview.value = {
      ...overview.value,
      watchlist: overview.value.watchlist.filter((item) => normalizeSymbol(item.symbol) !== normalized),
    }
    showToast('添加自选失败，请检查后端服务', 'error')
  } finally {
    watchlistBusy.value = false
  }
}

async function addFirstInstrument() {
  const currentFirst = instrumentResults.value[0] as InstrumentOption | undefined
  if (currentFirst) {
    await addInstrument(currentFirst.symbol)
    return
  }
  await searchInstruments()
  const searchedFirst = instrumentResults.value[0] as InstrumentOption | undefined
  if (searchedFirst) {
    await addInstrument(searchedFirst.symbol)
  }
}

onMounted(async () => {
  await Promise.all([loadOverview(), loadCandles()])
  await loadMonitoring()
  timer = window.setInterval(loadOverview, 500)
  candleTimer = window.setInterval(loadCandles, 1000)
})

onUnmounted(() => {
  if (timer !== null) window.clearInterval(timer)
  if (candleTimer !== null) window.clearInterval(candleTimer)
  if (searchTimer !== null) window.clearTimeout(searchTimer)
  if (toastTimer !== null) window.clearTimeout(toastTimer)
})
</script>

<style scoped>
.market-marquee,
.activity-marquee {
  overflow: hidden;
  padding: 2px 2px 8px;
}

.market-track,
.activity-track {
  display: flex;
  width: max-content;
  gap: 12px;
  animation: stream-scroll 18s linear infinite;
}

.activity-track {
  animation-duration: 14s;
}

.market-track:hover,
.activity-track:hover {
  animation-play-state: paused;
}

.market-card {
  position: relative;
  display: grid;
  gap: 8px;
  min-height: 118px;
  padding: 14px;
  border: 1px solid rgba(204, 219, 229, 0.95);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  color: #132238;
  text-align: left;
  box-shadow: 0 12px 32px rgba(130, 153, 183, 0.1);
  width: 250px;
  flex: 0 0 auto;
  overflow: hidden;
  transition: border-color .18s ease, background .18s ease, transform .18s ease, box-shadow .18s ease;
}

.market-card::before {
  content: "";
  position: absolute;
  inset: 0;
  opacity: .78;
  pointer-events: none;
}

.market-card::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 0%, rgba(255,255,255,.62) 46%, transparent 68%);
  opacity: 0;
  transform: translateX(-120%);
  pointer-events: none;
}

.market-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 38px rgba(96, 122, 150, 0.15);
}

.market-card > * {
  position: relative;
  z-index: 1;
}

.market-card--up {
  border-color: rgba(24, 179, 107, 0.36);
  background:
    linear-gradient(135deg, rgba(24, 179, 107, 0.13), rgba(255, 255, 255, 0.98) 58%),
    rgba(255, 255, 255, 0.96);
}

.market-card--up::before {
  background:
    linear-gradient(90deg, rgba(24, 179, 107, 0.18), transparent 34%),
    radial-gradient(circle at 92% 18%, rgba(24, 179, 107, 0.18), transparent 32%);
}

.market-card--down {
  border-color: rgba(217, 75, 91, 0.34);
  background:
    linear-gradient(135deg, rgba(217, 75, 91, 0.12), rgba(255, 255, 255, 0.98) 58%),
    rgba(255, 255, 255, 0.96);
}

.market-card--down::before {
  background:
    linear-gradient(90deg, rgba(217, 75, 91, 0.16), transparent 34%),
    radial-gradient(circle at 92% 18%, rgba(217, 75, 91, 0.17), transparent 32%);
}

.market-card--up::after,
.market-card--down::after {
  animation: quote-flash 1.8s ease-in-out infinite;
}

.market-card--neutral {
  border-color: rgba(204, 219, 229, 0.95);
}

.market-card--active {
  outline: 2px solid rgba(42, 191, 218, 0.24);
  outline-offset: -2px;
}

.market-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 13px;
}

.market-card__price {
  font-size: 22px;
  font-weight: 800;
  line-height: 1.05;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0;
  text-shadow: 0 1px 0 rgba(255,255,255,.55);
  transition: color .15s ease, transform .15s ease;
}

.market-card__details {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  color: #7189a0;
  font-size: 12px;
}

.market-card__details span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  width: 300px;
  min-height: 58px;
  padding: 10px 12px;
  border: 1px solid rgba(204, 219, 229, 0.95);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.96);
  color: #132238;
  flex: 0 0 auto;
}

.activity-card div {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.activity-card span {
  overflow: hidden;
  color: #7189a0;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-card em {
  font-style: normal;
}

@keyframes stream-scroll {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}

@keyframes quote-flash {
  0%, 72% {
    opacity: 0;
    transform: translateX(-120%);
  }
  82% {
    opacity: .55;
  }
  100% {
    opacity: 0;
    transform: translateX(120%);
  }
}

.toast {
  position: fixed;
  top: 18px;
  left: 50%;
  z-index: 1200;
  transform: translateX(-50%);
  min-width: 220px;
  max-width: 520px;
  padding: 11px 16px;
  border: 1px solid #d9e5ef;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.98);
  color: #26415f;
  text-align: center;
  box-shadow: 0 16px 46px rgba(100, 125, 155, 0.2);
}

.toast--success {
  border-color: rgba(24, 179, 107, 0.24);
  color: #1f9a59;
}

.toast--error {
  border-color: rgba(217, 75, 91, 0.28);
  color: #d94b5b;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity .18s ease, transform .18s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

.instrument-search {
  display: grid;
  gap: 12px;
}

.instrument-search__box {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.instrument-search__box input {
  width: 100%;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid #d9e5ef;
  border-radius: 12px;
  background: #f8fbfd;
  color: #132238;
  outline: none;
}

.instrument-results {
  display: grid;
  gap: 8px;
  max-height: 320px;
  overflow: auto;
}

.instrument-result {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 52px;
  padding: 8px 12px;
  border: 1px solid #e5edf4;
  border-radius: 12px;
  background: #f8fbfd;
  color: #132238;
  text-align: left;
}

.instrument-result div {
  display: grid;
  gap: 2px;
}

.instrument-result span {
  color: #7189a0;
  font-size: 12px;
}

.instrument-result em {
  font-style: normal;
  color: #0e8aa6;
  font-size: 12px;
}

.instrument-empty {
  padding: 22px 8px;
  color: #7790a6;
  text-align: center;
}

.modal-card__actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 4px;
}
</style>
