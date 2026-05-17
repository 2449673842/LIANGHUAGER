<template>
  <section class="page">
    <div class="page__header">
      <div class="page__title">
        <h1>总览终端</h1>
        <p>把 K 线、盘口、信号、持仓、运行动态收进一个工作台首页。</p>
      </div>
      <div class="page__actions">
        <span class="mini-badge">{{ overview.source || 'fallback' }}</span>
        <button class="button" @click="openAddSymbol">添加自选</button>
        <button class="button" @click="manualRefresh">同步数据</button>
        <button class="button button--primary" @click="toggleMonitoring">
          {{ monitoring ? '停止监控' : '启动监控' }}
        </button>
      </div>
    </div>

    <div class="stat-grid">
      <StatTile v-for="item in overview.marketPulse" :key="item.label" :label="item.label" :value="item.value" :tone="item.tone" />
    </div>

    <TerminalOverview
      :overview="overview"
      :candles="candles.items"
      :instrument-label="candles.instrumentId.replace('-', '/')"
      :timeframe-label="candles.timeframe"
      @refresh-candles="handleRefreshCandles"
      @toggle-monitoring="toggleMonitoring"
    />

    <ModalDialog
      :visible="addSymbolVisible"
      title="添加自选标的"
      subtitle="搜索并选择一个交易对，将添加到右侧自选列表和行情监控中"
      :fields="addSymbolFields"
      confirm-text="添加"
      @confirm="onAddSymbol"
      @cancel="addSymbolVisible = false"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import StatTile from '../components/cards/StatTile.vue'
import TerminalOverview from '../components/terminal/TerminalOverview.vue'
import ModalDialog, { type ModalField } from '../components/cards/ModalDialog.vue'
import {
  getMarketCandles,
  getOverview,
  getMonitoringState,
  setMonitoringState,
  addWatchlistSymbol,
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
let timer: number | null = null
let candleTimer: number | null = null

const monitoring = ref(false)

async function loadOverview() {
  const overviewData = await getOverview()
  overview.value = overviewData
}

async function loadCandles() {
  const candleData = await getMarketCandles()
  candles.value = candleData
}

async function manualRefresh() {
  await Promise.all([loadOverview(), loadCandles()])
}

async function handleRefreshCandles() {
  await loadCandles()
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
}

// --- add symbol modal ---
const addSymbolVisible = ref(false)
const SYMBOLS = [
  'BTC-USDT','ETH-USDT','SOL-USDT','XRP-USDT','DOGE-USDT','ADA-USDT','AVAX-USDT',
  'LINK-USDT','DOT-USDT','MATIC-USDT','UNI-USDT','SHIB-USDT','LTC-USDT','ATOM-USDT',
  'ETC-USDT','XLM-USDT','FIL-USDT','TRX-USDT','NEAR-USDT','APT-USDT','ARB-USDT',
  'OP-USDT','SUI-USDT','PEPE-USDT','INJ-USDT','TIA-USDT','SEI-USDT','ORDI-USDT',
  'SATS-USDT','RUNE-USDT','AAVE-USDT','ALGO-USDT','FLOW-USDT','SAND-USDT','MANA-USDT',
  'AXS-USDT','CRV-USDT','EOS-USDT','ICP-USDT','KAS-USDT','FET-USDT','AGIX-USDT',
  'BONK-USDT','WIF-USDT','JUP-USDT','PYTH-USDT','STRK-USDT','DYM-USDT','ALT-USDT',
]

const addSymbolFields: ModalField[] = [
  {
    key: 'symbol',
    label: '交易对代码',
    placeholder: '输入搜索...',
    suggestions: SYMBOLS,
    hint: '输入关键词筛选，从下拉列表中选择。支持 BTC、ETH、SOL 等主流币种及新上市交易对。',
  },
]

function openAddSymbol() {
  addSymbolVisible.value = true
}

async function onAddSymbol(values: Record<string, string>) {
  const symbol = (values.symbol || '').trim()
  if (!symbol) return
  try {
    await addWatchlistSymbol(symbol)
    await loadOverview()
  } catch (error) {
    console.error('添加自选失败', error)
  }
  addSymbolVisible.value = false
}

onMounted(async () => {
  await Promise.all([loadOverview(), loadCandles()])
  await loadMonitoring()
  timer = window.setInterval(loadOverview, 1000)
  candleTimer = window.setInterval(loadCandles, 5000)
})

onUnmounted(() => {
  if (timer !== null) window.clearInterval(timer)
  if (candleTimer !== null) window.clearInterval(candleTimer)
})
</script>
