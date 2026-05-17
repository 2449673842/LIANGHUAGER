<template>
  <div class="split-grid">
    <div class="stack">
      <PanelCard title="图表与买卖点" description="后续接 quant_platform 回测结果和 trading-dashboard K 线">
        <template #actions>
          <div class="tabs">
            <button class="tab tab--active">回测结果</button>
            <button class="tab">智能调参</button>
            <button class="tab">策略对比</button>
            <span class="mini-badge">{{ payload.upstreamConnected ? (payload.source || '上游已连接') : '本地回落' }}</span>
          </div>
        </template>
        <MarketKlineChart :items="candles" />
      </PanelCard>

      <PanelCard title="权益曲线" description="先接结果走势，后续补点击交易定位图表">
        <EquityCurveChart :points="payload.equityCurve" />
      </PanelCard>

      <PanelCard title="交易列表" description="点击后应联动图表定位">
        <div class="table table--scroll">
          <div class="table__head table-trades">
            <span>时间</span><span>方向</span><span>价格</span><span>原因</span>
          </div>
          <div v-for="row in payload.trades" :key="`${row.time}-${row.side}`" class="table__row table-trades">
            <span>{{ row.time }}</span>
            <span :class="row.side === '买入' ? 'tone-up' : 'tone-down'">{{ row.side }}</span>
            <span>{{ row.price }}</span>
            <span>{{ row.reason }}</span>
          </div>
        </div>
      </PanelCard>
    </div>

    <div class="stack">
      <PanelCard title="回测参数" description="先接工作台右侧参数面板">
        <div class="field-grid">
          <div class="field">
            <label>回测周期</label>
            <select>
              <option v-for="period in payload.periods" :key="period">{{ period }}</option>
            </select>
          </div>
          <div class="field">
            <label>交易方向</label>
            <select>
              <option>做多</option>
              <option>做空</option>
              <option>双向</option>
            </select>
          </div>
          <div class="field">
            <label>初始资金</label>
            <input value="10000" />
          </div>
          <div class="field">
            <label>杠杆</label>
            <input value="1" />
          </div>
          <div class="field">
            <label>手续费 (%)</label>
            <input value="0.0200" />
          </div>
          <div class="field">
            <label>滑点 (%)</label>
            <input value="0.0200" />
          </div>
        </div>
      </PanelCard>

      <PanelCard title="关键指标" description="先保留回测 KPI 卡片">
        <div class="list list--scroll">
          <div v-for="metric in payload.metrics" :key="metric.label" class="list-row">
            <span>{{ metric.label }}</span>
            <strong :class="toneClass(metric.tone)">{{ metric.value }}</strong>
          </div>
        </div>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import PanelCard from '../cards/PanelCard.vue'
import MarketKlineChart from './MarketKlineChart.vue'
import EquityCurveChart from './EquityCurveChart.vue'
import type { BacktestPayload, CandlePoint } from '../../services/api'

defineProps<{
  payload: BacktestPayload
  candles: CandlePoint[]
}>()

function toneClass(tone?: 'up' | 'down' | 'neutral') {
  if (tone === 'up') return 'tone-up'
  if (tone === 'down') return 'tone-down'
  return 'tone-neutral'
}
</script>

<style scoped>
.table-trades {
  grid-template-columns: 1.3fr 60px 88px 1fr;
}
</style>
