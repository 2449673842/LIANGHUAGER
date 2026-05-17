<template>
  <div class="split-grid">
    <div class="stack">
      <PanelCard title="运行摘要" description="接近 execution-runtime 的总览卡片">
        <div class="runtime-grid">
          <div class="runtime-tile">
            <span>活跃任务</span>
            <strong>{{ payload.runtime.activeTasks }}</strong>
          </div>
          <div class="runtime-tile">
            <span>活跃会话</span>
            <strong>{{ payload.runtime.activeSessions }}</strong>
          </div>
          <div class="runtime-tile">
            <span>待确认</span>
            <strong>{{ payload.runtime.pendingConfirmations }}</strong>
          </div>
          <div class="runtime-tile">
            <span>已通知</span>
            <strong>{{ payload.runtime.notificationsSent }}</strong>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="交易模式" description="默认人工确认，可切到自动执行">
        <template #actions>
          <div class="inline-toolbar">
            <button class="button" @click="store.toggleTradeMode()">切换到{{ store.tradeMode === 'paper' ? '实盘' : '模拟' }}</button>
            <button class="button button--primary">{{ store.modeLabel }}运行队列</button>
          </div>
        </template>
        <div class="field-grid">
          <div class="field">
            <label>当前模式</label>
            <input :value="store.modeLabel" />
          </div>
          <div class="field">
            <label>执行开关</label>
            <select>
              <option>人工确认</option>
              <option>自动执行</option>
            </select>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="运行会话" description="多账户、多标的、多策略并行">
        <div class="table table--scroll">
          <div class="table__head table-session">
            <span>会话</span><span>策略</span><span>标的</span><span>模式</span><span>状态</span>
          </div>
          <div v-for="item in payload.sessions" :key="item.name" class="table__row table-session">
            <span>{{ item.name }}</span>
            <span>{{ item.strategy }}</span>
            <span>{{ item.symbol }}</span>
            <span>{{ item.mode }}</span>
            <strong :class="sessionTone(item.state)">{{ item.state }}</strong>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="待确认 / 执行队列" description="人工确认与自动执行共用一个队列面板">
        <div class="table table--scroll">
          <div class="table__head table-queue">
            <span>时间</span><span>策略</span><span>标的</span><span>动作</span><span>状态</span>
          </div>
          <div v-for="item in payload.queues" :key="`${item.time}-${item.strategy}-${item.symbol}`" class="table__row table-queue">
            <span>{{ item.time }}</span>
            <span>{{ item.strategy }}</span>
            <span>{{ item.symbol }}</span>
            <span>{{ item.action }}</span>
            <strong :class="queueTone(item.state)">{{ item.state }}</strong>
          </div>
        </div>
      </PanelCard>
    </div>

    <div class="stack">
      <PanelCard title="账户接入" description="第一阶段先围绕 OKX 现货与永续">
        <div class="list list--scroll">
          <div v-for="account in payload.accounts" :key="account.name" class="list-row">
            <div>
              <strong>{{ account.name }}</strong>
              <div class="muted">{{ account.venue }}</div>
            </div>
            <div style="text-align: right">
              <strong>{{ account.equity }}</strong>
              <div :class="account.status === '在线' ? 'tone-up' : 'tone-neutral'">{{ account.status }}</div>
            </div>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="告警通道" description="先留邮件和企业微信，后续补信号派发">
        <div class="list list--scroll">
          <div class="list-row"><span>SMTP 邮件</span><span class="tone-up">已启用</span></div>
          <div class="list-row"><span>企业微信 Webhook</span><span class="tone-neutral">待配置</span></div>
          <div class="list-row"><span>TradingView 桥接</span><span class="tone-neutral">迁移中</span></div>
        </div>
      </PanelCard>

      <PanelCard title="执行说明" description="默认策略仍然走人工确认，后续再把真实下单链补齐">
        <div class="list">
          <div class="list-row"><span>当前上游</span><span>{{ payload.upstreamConnected ? (payload.source || '上游已连接') : '本地回落' }}</span></div>
          <div class="list-row"><span>默认执行</span><span>人工确认</span></div>
          <div class="list-row"><span>自动执行</span><span>预留开关</span></div>
        </div>
      </PanelCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import PanelCard from '../cards/PanelCard.vue'
import { useWorkbenchStore } from '../../stores/workbench'
import type { ExecutionPayload } from '../../services/api'

defineProps<{
  payload: ExecutionPayload
}>()

const store = useWorkbenchStore()

function sessionTone(state: string) {
  if (state.includes('运行')) return 'tone-up'
  if (state.includes('告警')) return 'tone-down'
  return 'tone-neutral'
}

function queueTone(state: string) {
  if (state.includes('确认')) return 'tone-neutral'
  if (state.includes('发送') || state.includes('运行')) return 'tone-up'
  return 'tone-down'
}
</script>

<style scoped>
.table-session {
  grid-template-columns: 1.2fr 1fr 0.9fr 72px 92px;
}

.table-queue {
  grid-template-columns: 88px 1fr 0.9fr 72px 88px;
}

.runtime-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.runtime-tile {
  display: grid;
  gap: 6px;
  min-height: 88px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid #e4edf4;
  background: #f8fbfd;
}

.runtime-tile span {
  color: #688299;
  font-size: 13px;
}

.runtime-tile strong {
  font-size: 24px;
  color: #11233d;
}
</style>
