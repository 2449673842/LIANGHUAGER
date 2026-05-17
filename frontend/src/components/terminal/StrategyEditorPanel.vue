<template>
  <div class="split-grid">
    <PanelCard title="策略编辑器" description="复用 quant_platform 中已有的 Python 策略能力">
      <template #actions>
        <div class="inline-toolbar">
          <button class="button">检查代码</button>
          <button class="button">保存版本</button>
          <button class="button button--primary">运行回测</button>
        </div>
      </template>
      <div class="code-box">{{ source }}</div>
    </PanelCard>

    <div class="stack">
      <PanelCard title="运行参数" description="先保留为表单，后续接真实参数模板">
        <div class="field-grid">
          <div class="field">
            <label>策略名</label>
            <input value="trend_follow_btc_v1" />
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
            <label>止损 (%)</label>
            <input value="3.0" />
          </div>
          <div class="field">
            <label>止盈 (%)</label>
            <input value="6.0" />
          </div>
          <div class="field">
            <label>单次开仓比例 (%)</label>
            <input value="100" />
          </div>
          <div class="field">
            <label>追踪止损 (%)</label>
            <input value="2.0" />
          </div>
        </div>
      </PanelCard>

      <PanelCard title="策略列表" description="支持同标的多策略、多标的多策略">
        <div class="list list--scroll">
          <div v-for="item in board.items" :key="item.versionId" class="list-row">
            <div>
              <strong>{{ item.label }}</strong>
              <div class="muted">{{ item.instrumentId }} / {{ item.timeframe }} / {{ item.versionId }}</div>
            </div>
            <div style="text-align: right">
              <strong :class="statusTone(item.status)">{{ item.status }}</strong>
              <div class="muted">{{ item.updatedAt }}</div>
            </div>
          </div>
        </div>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import PanelCard from '../cards/PanelCard.vue'
import type { StrategyBoardPayload } from '../../services/api'

defineProps<{
  board: StrategyBoardPayload
}>()

const source = `my_indicator_name = "BTC Trend Follow"
my_indicator_description = "单一来源的策略参数样例"

# @strategy stopLossPct 0.03
# @strategy takeProfitPct 0.06
# @strategy entryPct 1.0
# @strategy trailingEnabled true
# @strategy trailingStopPct 0.02
# @strategy tradeDirection long

df = df.copy()
df["buy"] = False
df["sell"] = False

fast = df["close"].rolling(10).mean()
slow = df["close"].rolling(24).mean()

df.loc[(fast > slow) & (fast.shift(1) <= slow.shift(1)), "buy"] = True
df.loc[(fast < slow) & (fast.shift(1) >= slow.shift(1)), "sell"] = True`

function statusTone(status: string) {
  if (status.includes('运行') || status.includes('发布')) return 'tone-up'
  if (status.includes('告警') || status.includes('禁用')) return 'tone-down'
  return 'tone-neutral'
}
</script>
