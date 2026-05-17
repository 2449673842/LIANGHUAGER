<template>
  <div class="overview-grid">
    <div class="stack">
      <PanelCard title="市场脉冲" description="K 线、盘口、信号前的快速读数">
        <div class="list list--scroll">
          <div v-for="item in overview.marketPulse" :key="item.label" class="list-row">
            <span>{{ item.label }}</span>
            <strong :class="toneClass(item.tone)">{{ item.value }}</strong>
          </div>
        </div>
      </PanelCard>
      <PanelCard title="策略持仓" description="来自运行中的模拟与实盘会话">
        <div class="table table--scroll">
          <div class="table__head table-pos">
            <span>策略</span><span>标的</span><span>方向</span><span>盈亏</span>
          </div>
          <div v-for="row in overview.positions" :key="`${row.strategy}-${row.symbol}`" class="table__row table-pos">
            <span>{{ row.strategy }}</span>
            <span>{{ row.symbol }}</span>
            <span>{{ row.side }}</span>
            <strong :class="row.pnl.startsWith('-') ? 'tone-down' : 'tone-up'">{{ row.pnl }}</strong>
          </div>
        </div>
      </PanelCard>
      <PanelCard title="控制面板" description="沿着 trading-dashboard 的监控面板继续做">
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

    <div class="stack">
      <PanelCard title="K 线与交易台" description="承接 trading-dashboard 的主终端内容">
        <template #actions>
          <div class="chart-toolbar">
            <span class="mini-badge">{{ instrumentLabel }}</span>
            <button class="tab tab--active">{{ timeframeLabel }}</button>
            <button class="tab">1H</button>
            <button class="tab">4H</button>
            <span class="mini-badge">{{ overview.upstreamConnected ? '上游已连接' : '本地回落' }}</span>
            <button class="button button--primary" @click="$emit('toggleMonitoring')">
              {{ overview.controlState.running ? '停止监控' : '开始监控' }}
            </button>
          </div>
        </template>
        <MarketKlineChart :items="candles" />
      </PanelCard>
      <PanelCard title="盘口深度" description="先把 trading-dashboard 的订单簿结构迁过来">
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

    <div class="stack">
      <PanelCard title="自选与信号" description="参考你截图里的右侧信息区">
        <div class="list list--scroll">
          <div v-for="item in overview.watchlist" :key="item.symbol" class="list-row">
            <div>
              <strong>{{ item.symbol }}</strong>
              <div class="muted">{{ item.signal }}</div>
            </div>
            <div style="text-align: right">
              <strong>{{ item.price }}</strong>
              <div :class="item.change.startsWith('-') ? 'tone-down' : 'tone-up'">{{ item.change }}</div>
            </div>
          </div>
        </div>
      </PanelCard>
      <PanelCard title="运行动态" description="告警、执行、确认和系统事件">
        <div class="list list--scroll">
          <div v-for="item in overview.activity" :key="`${item.time}-${item.message}`" class="list-row">
            <div>
              <strong>{{ item.time }}</strong>
              <div class="muted">{{ item.message }}</div>
            </div>
            <span :class="toneClass(item.tone)">●</span>
          </div>
        </div>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import PanelCard from '../cards/PanelCard.vue'
import MarketKlineChart from './MarketKlineChart.vue'
import type { CandlePoint, OverviewPayload } from '../../services/api'

const props = defineProps<{
  overview: OverviewPayload
  candles: CandlePoint[]
  instrumentLabel: string
  timeframeLabel: string
}>()

function toneClass(tone?: 'up' | 'down' | 'neutral') {
  if (tone === 'up') return 'tone-up'
  if (tone === 'down') return 'tone-down'
  return 'tone-neutral'
}

function formatCooldown(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const remain = seconds % 60
  return `${minutes}分${remain}秒`
}
</script>

<style scoped>
.table-pos {
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) 68px 88px;
}

.control-panel {
  display: grid;
  gap: 14px;
}

.control-panel__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.orderbook {
  display: grid;
  gap: 8px;
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
  min-height: 42px;
  padding: 0 12px;
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
  min-height: 38px;
  padding: 0 12px;
  border-radius: 12px;
  background: #eef5fa;
  color: #46637f;
  font-weight: 700;
}
</style>
