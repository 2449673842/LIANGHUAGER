<template>
  <div class="overview-workspace">
    <div class="trade-row">
      <PanelCard title="自选与信号" description="点击切换主图" class="watch-panel">
        <div class="watch-summary">
          <span>{{ overview.watchlist.length }} 个自选</span>
          <em>{{ watchlistBusy ? '保存中' : '已保存' }}</em>
        </div>
        <div class="list watch-list">
          <div
            v-for="item in overview.watchlist"
            :key="item.symbol"
            class="watch-row"
            :class="[
              watchToneClass(item.change),
              { 'watch-row--active': normalizeSymbol(item.symbol) === selectedInstrument },
            ]"
          >
            <button class="watch-row__main" @click="$emit('selectInstrument', item.symbol)">
              <strong>{{ item.symbol }}</strong>
              <div class="muted">{{ item.signal }}</div>
            </button>
            <button class="watch-row__price" @click="$emit('selectInstrument', item.symbol)">
              <strong :class="changeToneClass(item.change)">{{ item.price }}</strong>
              <div :class="changeToneClass(item.change)">{{ item.change }}</div>
            </button>
            <button class="watch-row__remove" title="移除自选" @click="$emit('removeSymbol', item.symbol)">×</button>
          </div>
          <div v-if="overview.watchlist.length === 0" class="empty-state">
            暂无自选，点击右上角添加标的
          </div>
        </div>
      </PanelCard>
      <PanelCard title="K 线与交易台" description="承接 trading-dashboard 的主终端内容" class="kline-panel">
        <template #actions>
          <div class="chart-toolbar">
            <span class="mini-badge">{{ instrumentLabel }}</span>
            <button
              v-for="timeframe in timeframes"
              :key="timeframe"
              class="tab"
              :class="{ 'tab--active': timeframe === selectedTimeframe }"
              @click="$emit('changeTimeframe', timeframe)"
            >
              {{ timeframe }}
            </button>
            <span class="mini-badge">{{ candleSource }}</span>
            <span class="mini-badge">{{ overview.upstreamConnected ? '上游已连接' : '本地回落' }}</span>
            <span class="mini-badge">{{ refreshing ? '刷新中' : `刷新 ${lastRefreshText}` }}</span>
            <button class="button button--primary" @click="$emit('toggleMonitoring')">
              {{ overview.controlState.running ? '停止监控' : '开始监控' }}
            </button>
          </div>
        </template>
        <MarketKlineChart :items="candles" />
        <div class="ai-signal-grid">
          <div>
            <span>AI趋势</span>
            <strong :class="aiToneClass">{{ aiTrendLabel }}</strong>
          </div>
          <div>
            <span>买点分析</span>
            <strong :class="buyPointTone">{{ buyPointText }}</strong>
          </div>
          <div>
            <span>卖点分析</span>
            <strong :class="sellPointTone">{{ sellPointText }}</strong>
          </div>
          <div>
            <span>置信度</span>
            <strong>{{ aiConfidenceText }}</strong>
          </div>
          <div>
            <span>风险提示</span>
            <strong :class="riskTone">{{ riskText }}</strong>
          </div>
        </div>
      </PanelCard>
      <PanelCard title="盘口深度" description="跟随当前标的" class="orderbook-panel">
        <div class="orderbook">
          <div class="orderbook__header"><span>卖</span><span>数量</span></div>
          <div v-for="(ask, index) in overview.orderbook.asks" :key="`ask-${index}`" class="orderbook__row orderbook__row--ask">
            <span class="tone-down">{{ ask[0] }}</span>
            <span>{{ ask[1] }}</span>
          </div>
          <div class="orderbook__spread">{{ overview.orderbook.spreadText }}</div>
          <div v-for="(bid, index) in overview.orderbook.bids" :key="`bid-${index}`" class="orderbook__row orderbook__row--bid">
            <span class="tone-up">{{ bid[0] }}</span>
            <span>{{ bid[1] }}</span>
          </div>
          <div class="orderbook__header"><span>买</span><span>数量</span></div>
        </div>
      </PanelCard>
    </div>

    <PanelCard title="策略持仓" description="运行中的模拟与实盘会话">
      <div class="position-strip">
        <div v-for="row in overview.positions" :key="`${row.strategy}-${row.symbol}`" class="position-pill">
          <span>{{ row.strategy }}</span>
          <strong>{{ row.symbol }}</strong>
          <em>{{ row.side }}</em>
          <b :class="row.pnl.startsWith('-') ? 'tone-down' : 'tone-up'">{{ row.pnl }}</b>
          <small>{{ row.size }}</small>
        </div>
      </div>
    </PanelCard>

    <div class="overview-lower-grid">
      <PanelCard title="控制面板" description="监控与执行状态">
        <div class="control-panel">
          <div class="control-panel__status">
            <div>
              <strong :class="overview.controlState.running ? 'tone-up' : 'tone-neutral'">
                {{ overview.controlState.running ? '监控运行中' : '监控已停止' }}
              </strong>
              <div class="muted">上次同步 {{ overview.controlState.lastSync }}</div>
            </div>
            <span class="mini-badge">{{ overview.controlState.executionMode }}</span>
          </div>
          <div class="control-panel__metrics">
            <div class="list-row">
              <span>冷却计时</span>
              <strong>{{ formatCooldown(overview.controlState.cooldownSeconds) }}</strong>
            </div>
            <div class="list-row">
              <span>当前标的</span>
              <strong>{{ selectedInstrument }}</strong>
            </div>
            <div class="list-row">
              <span>行情来源</span>
              <strong>{{ candleSource }}</strong>
            </div>
            <div class="list-row">
              <span>自选数量</span>
              <strong>{{ overview.watchlist.length }}</strong>
            </div>
            <div class="list-row">
              <span>盘口档位</span>
              <strong>{{ orderbookDepthText }}</strong>
            </div>
          </div>
          <div class="inline-toolbar">
            <button class="button button--primary" @click="$emit('toggleMonitoring')">
              {{ overview.controlState.running ? '停止监控' : '启动监控' }}
            </button>
            <button class="button" @click="$emit('refreshCandles')">同步最新K线</button>
          </div>
        </div>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import PanelCard from '../cards/PanelCard.vue'
import MarketKlineChart from './MarketKlineChart.vue'
import { computed } from 'vue'
import type { CandlePoint, OverviewPayload } from '../../services/api'

const props = defineProps<{
  overview: OverviewPayload
  candles: CandlePoint[]
  instrumentLabel: string
  timeframeLabel: string
  selectedInstrument: string
  selectedTimeframe: string
  candleSource: string
  lastRefreshText: string
  refreshing: boolean
  watchlistBusy: boolean
}>()

defineEmits<{
  refreshCandles: []
  toggleMonitoring: []
  selectInstrument: [symbol: string]
  removeSymbol: [symbol: string]
  changeTimeframe: [timeframe: string]
}>()

const timeframes = ['1m', '5m', '15m', '1H', '4H']

const latestCandle = computed(() => props.candles[props.candles.length - 1])

const candleChangePct = computed(() => {
  const candle = latestCandle.value
  if (!candle || !candle.open) return 0
  return ((candle.close - candle.open) / candle.open) * 100
})

const candleRangePct = computed(() => {
  const candle = latestCandle.value
  if (!candle || !candle.low) return 0
  return ((candle.high - candle.low) / candle.low) * 100
})

const maFast = computed(() => movingAverageClose(8))
const maSlow = computed(() => movingAverageClose(24))

const orderbookBias = computed(() => {
  const bidSize = props.overview.orderbook.bids.reduce((sum, row) => sum + Number(row[1] || 0), 0)
  const askSize = props.overview.orderbook.asks.reduce((sum, row) => sum + Number(row[1] || 0), 0)
  const total = bidSize + askSize
  return total ? (bidSize - askSize) / total : 0
})

const aiScore = computed(() => {
  let score = 0
  if (maFast.value > maSlow.value) score += 1
  if (maFast.value < maSlow.value) score -= 1
  if (candleChangePct.value > 0) score += 0.6
  if (candleChangePct.value < 0) score -= 0.6
  score += Math.max(-0.8, Math.min(0.8, orderbookBias.value * 1.6))
  return score
})

const aiTrendLabel = computed(() => {
  if (aiScore.value >= 1.2) return '偏多趋势'
  if (aiScore.value <= -1.2) return '偏空趋势'
  return '震荡观察'
})

const aiToneClass = computed(() => {
  if (aiScore.value >= 1.2) return 'tone-up'
  if (aiScore.value <= -1.2) return 'tone-down'
  return 'tone-neutral'
})

const buyPointText = computed(() => {
  if (aiScore.value >= 1.2) return '回踩MA8'
  if (aiScore.value > 0.25) return '小仓试探'
  return '等待放量'
})

const buyPointTone = computed(() => (aiScore.value > 0.25 ? 'tone-up' : 'tone-neutral'))

const sellPointText = computed(() => {
  if (aiScore.value <= -1.2) return '反弹减仓'
  if (candleRangePct.value > 0.8) return '冲高保护'
  return '跌破MA24'
})

const sellPointTone = computed(() => (aiScore.value < -0.25 || candleRangePct.value > 0.8 ? 'tone-down' : 'tone-neutral'))

const aiConfidenceText = computed(() => {
  const confidence = Math.min(92, Math.max(48, 58 + Math.abs(aiScore.value) * 16 + Math.min(candleRangePct.value, 1.2) * 6))
  return `${confidence.toFixed(0)}%`
})

const riskText = computed(() => {
  if (candleRangePct.value > 1.2) return '波动偏高'
  if (Math.abs(orderbookBias.value) > 0.35) return '盘口倾斜'
  return '常规'
})

const riskTone = computed(() => (riskText.value === '常规' ? 'tone-neutral' : 'tone-down'))

function movingAverageClose(period: number) {
  const items = props.candles.slice(-period)
  if (items.length < period) return 0
  return items.reduce((sum, item) => sum + item.close, 0) / items.length
}

const orderbookDepthText = computed(() => {
  const asks = props.overview.orderbook.asks.length
  const bids = props.overview.orderbook.bids.length
  return `${bids}/${asks}`
})

function normalizeSymbol(symbol: string) {
  return symbol.replace('/', '-').toUpperCase()
}

function toneClass(tone?: 'up' | 'down' | 'neutral') {
  if (tone === 'up') return 'tone-up'
  if (tone === 'down') return 'tone-down'
  return 'tone-neutral'
}

function changeToneClass(change: string) {
  if (change.startsWith('-')) return 'tone-down'
  if (change.startsWith('+')) return 'tone-up'
  return 'tone-neutral'
}

function watchToneClass(change: string) {
  if (change.startsWith('-')) return 'watch-row--down'
  if (change.startsWith('+')) return 'watch-row--up'
  return 'watch-row--neutral'
}

function formatCooldown(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const remain = seconds % 60
  return `${minutes}分${remain}秒`
}
</script>

<style scoped>
.overview-workspace {
  display: grid;
  gap: 16px;
}

.trade-row {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 260px;
  gap: 16px;
  align-items: stretch;
}

.kline-panel,
.orderbook-panel,
.watch-panel {
  min-height: 510px;
}

.orderbook-panel :deep(.panel__body),
.watch-panel :deep(.panel__body) {
  flex: 1;
  overflow: hidden;
}

.overview-lower-grid {
  display: grid;
  grid-template-columns: minmax(280px, 320px);
  gap: 16px;
  align-items: start;
}

.table-pos {
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) 68px 88px;
}

.control-panel {
  display: grid;
  gap: 12px;
}

.control-panel__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.control-panel__metrics {
  display: grid;
  gap: 8px;
}

.control-panel__metrics .list-row {
  min-height: 38px;
  padding: 8px 10px;
  border-radius: 10px;
}

.watch-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 32px;
  padding: 0 4px;
  color: #6f879f;
  font-size: 12px;
}

.watch-summary em {
  color: #0e8aa6;
  font-style: normal;
  font-weight: 700;
}

.orderbook {
  display: grid;
  gap: 6px;
  height: 100%;
  align-content: start;
}

.orderbook__header,
.orderbook__row,
.orderbook__spread {
  display: grid;
  grid-template-columns: 1fr 88px;
  align-items: center;
  gap: 12px;
}

.orderbook__header {
  color: #6f879f;
  font-size: 12px;
  text-transform: uppercase;
  padding: 0 2px;
}

.orderbook__row {
  min-height: 34px;
  padding: 0 10px;
  border: 1px solid #e6edf3;
  border-radius: 12px;
  background: #f8fbfd;
}

.orderbook__row--ask {
  background: rgba(240, 91, 113, 0.05);
}

.orderbook__row--bid {
  background: rgba(24, 179, 107, 0.06);
}

.orderbook__spread {
  min-height: 34px;
  padding: 0 10px;
  border-radius: 12px;
  background: #eef5fa;
  color: #46637f;
  font-weight: 700;
  font-size: 13px;
}

.watch-row {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(86px, auto) 28px;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #e5edf4;
  border-radius: 12px;
  background: #f8fbfd;
  overflow: hidden;
  transition: border-color .18s ease, background .18s ease;
}

.watch-row::before {
  content: "";
  position: absolute;
  inset: 0;
  opacity: .8;
  pointer-events: none;
}

.watch-row > * {
  position: relative;
  z-index: 1;
}

.watch-row--up {
  border-color: rgba(24, 179, 107, 0.25);
  background: linear-gradient(90deg, rgba(24, 179, 107, 0.12), #f8fbfd 46%);
}

.watch-row--up::before {
  background: linear-gradient(90deg, rgba(24, 179, 107, 0.1), transparent 52%);
}

.watch-row--down {
  border-color: rgba(217, 75, 91, 0.25);
  background: linear-gradient(90deg, rgba(217, 75, 91, 0.11), #f8fbfd 46%);
}

.watch-row--down::before {
  background: linear-gradient(90deg, rgba(217, 75, 91, 0.09), transparent 52%);
}

.watch-list {
  max-height: 438px;
  overflow: auto;
  padding-right: 4px;
}

.empty-state {
  display: grid;
  place-items: center;
  min-height: 112px;
  border: 1px dashed #d5e3ee;
  border-radius: 12px;
  color: #7790a6;
  font-size: 13px;
}

.watch-row--active {
  border-color: rgba(42, 191, 218, 0.48);
  background: linear-gradient(135deg, rgba(28, 201, 208, 0.09), rgba(47, 184, 247, 0.12));
}

.watch-row__main,
.watch-row__price,
.watch-row__remove {
  border: 0;
  background: transparent;
  color: inherit;
  padding: 0;
}

.watch-row__main {
  min-width: 0;
  text-align: left;
}

.watch-row__price {
  text-align: right;
}

.watch-row__price strong {
  font-variant-numeric: tabular-nums;
}

.watch-row__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  color: #8ca2b7;
  font-size: 18px;
}

.watch-row__remove:hover {
  background: #fff0f2;
  color: #d94b5b;
}

.position-strip {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(240px, 1fr);
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.position-pill {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 4px 12px;
  min-height: 74px;
  padding: 12px 14px;
  border: 1px solid #e5edf4;
  border-radius: 12px;
  background: #f8fbfd;
}

.position-pill span,
.position-pill small {
  color: #7189a0;
  font-size: 12px;
}

.position-pill em {
  color: #607a96;
  font-style: normal;
  font-size: 12px;
}

.position-pill b {
  font-size: 15px;
}

.ai-signal-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.ai-signal-grid div {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid #e5edf4;
  border-radius: 10px;
  background: #f8fbfd;
}

.ai-signal-grid span {
  color: #7189a0;
  font-size: 11px;
}

.ai-signal-grid strong {
  overflow: hidden;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

</style>
