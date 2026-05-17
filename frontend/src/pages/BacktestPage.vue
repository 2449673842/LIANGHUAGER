<template>
  <section class="page">
    <div class="page__header">
      <div class="page__title">
        <h1>回测 / 调参</h1>
        <p>把回测结果、图上买卖点、调参窗口和结果对比放进同一个工作区。</p>
      </div>
      <div class="page__actions">
        <span class="mini-badge">{{ payload.source || candles.source || 'fallback' }}</span>
        <button class="button">参数模板</button>
        <button class="button">结果归档</button>
        <button class="button button--primary" @click="openRunBacktest">运行回测</button>
      </div>
    </div>

    <BacktestWorkbench :payload="payload" :candles="candles.items" />

    <ModalDialog
      :visible="runVisible" title="运行回测"
      subtitle="选择一个周期运行回测，系统将根据历史数据模拟策略表现。"
      :fields="runFields" confirm-text="运行"
      @confirm="onRunBacktest" @cancel="runVisible = false" />
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import BacktestWorkbench from '../components/terminal/BacktestWorkbench.vue'
import ModalDialog, { type ModalField } from '../components/cards/ModalDialog.vue'
import { getBacktestWorkbench, getMarketCandles, runBacktest, type BacktestPayload, type CandlePayload } from '../services/api'

const payload = ref<BacktestPayload>({ periods: [], metrics: [], trades: [], equityCurve: [] })
const candles = ref<CandlePayload>({ instrumentId: 'BTC-USDT', timeframe: '15m', items: [] })
let timer: number | null = null

async function loadBacktest() {
  const [b, c] = await Promise.all([getBacktestWorkbench(), getMarketCandles()])
  payload.value = b; candles.value = c
}

const runVisible = ref(false)
const runFields: ModalField[] = [
  {
    key: 'period', label: '回测周期', type: 'select',
    options: [
      { value: '1M', label: '1 个月' },
      { value: '3M', label: '3 个月' },
      { value: '6M', label: '6 个月' },
      { value: '1Y', label: '1 年' },
    ],
    hint: '周期越长，越能反映策略在不同市场环境下的表现。',
  },
]

function openRunBacktest() {
  runVisible.value = true
}

async function onRunBacktest(v: Record<string, string>) {
  try {
    const result = await runBacktest({ period: v.period || '1M' })
    payload.value = result
  } catch (e) {
    console.error('运行回测失败', e)
    await loadBacktest()
  }
  runVisible.value = false
}

onMounted(async () => { await loadBacktest(); timer = window.setInterval(loadBacktest, 10000) })
onUnmounted(() => { if (timer !== null) window.clearInterval(timer) })
</script>
