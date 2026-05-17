<template>
  <section class="page">
    <div class="page__header">
      <div class="page__title">
        <h1>模拟 / 实盘</h1>
        <p>多账户、多标的、多策略并行，默认人工确认，可切自动执行。</p>
      </div>
      <div class="page__actions">
        <span class="mini-badge">{{ payload.source || 'fallback' }}</span>
        <button class="button" @click="openAddAccount">新增账户</button>
        <button class="button" @click="openPendingList">查看待确认</button>
        <button class="button button--primary" @click="openAddQueue">进入执行队列</button>
      </div>
    </div>

    <ExecutionConsole :payload="payload" />

    <ModalDialog
      :visible="accountVisible" title="新增账户" :fields="accountFields" confirm-text="添加"
      @confirm="onAddAccount" @cancel="accountVisible = false" />

    <ModalDialog
      :visible="queueVisible" title="添加到执行队列"
      subtitle="手动创建一个执行任务。任务默认进入待确认队列，审核后发送给策略引擎。"
      :fields="queueFields" confirm-text="加入队列"
      @confirm="onAddQueue" @cancel="queueVisible = false" />

    <ModalDialog
      :visible="pendingVisible" title="待确认列表"
      subtitle="当前等待审核的执行任务，确认后进入运行队列。"
      :hide-cancel="true" :hide-confirm="true" width="520px"
      @cancel="pendingVisible = false">
      <div v-if="pendingItems.length === 0" style="padding:20px 0;text-align:center;color:#7790a6;">
        暂无待确认的任务
      </div>
      <div v-else class="table" style="display:grid;gap:8px;">
        <div class="table__head" style="display:grid;grid-template-columns:72px 1fr 0.9fr 60px 1fr 68px;gap:8px;color:#6f879f;font-size:12px;text-transform:uppercase;padding:0 4px;">
          <span>时间</span><span>策略</span><span>标的</span><span>动作</span><span>原因</span><span>状态</span>
        </div>
        <div v-for="item in pendingItems" :key="`${item.time}-${item.strategy}`"
          style="display:grid;grid-template-columns:72px 1fr 0.9fr 60px 1fr 68px;gap:8px;min-height:46px;background:#f8fbfd;border:1px solid #e5edf4;border-radius:10px;padding:0 10px;align-items:center;font-size:13px;">
          <span>{{ item.time }}</span>
          <span>{{ item.strategy }}</span>
          <span>{{ item.symbol }}</span>
          <span>{{ item.action }}</span>
          <span class="muted">{{ item.reason }}</span>
          <span style="color:#607a96;">待确认</span>
        </div>
      </div>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import ExecutionConsole from '../components/terminal/ExecutionConsole.vue'
import ModalDialog, { type ModalField } from '../components/cards/ModalDialog.vue'
import { getExecution, addAccount, addExecutionQueue, type ExecutionPayload } from '../services/api'

const payload = ref<ExecutionPayload>({
  mode: 'paper', accounts: [], sessions: [], queues: [],
  runtime: { activeTasks: 0, activeSessions: 0, pendingConfirmations: 0, notificationsSent: 0 },
})
let timer: number | null = null

async function loadExecution() { payload.value = await getExecution() }

const pendingItems = computed(() => payload.value.queues.filter(q => q.state.includes('确认')))

const accountVisible = ref(false)
const accountFields: ModalField[] = [
  { key: 'name', label: '账户名称', placeholder: 'OKX 主账户', hint: '自定义标识，用于区分多账户策略分配。' },
  { key: 'equity', label: '权益 (USDT)', placeholder: '100000', type: 'text', hint: '仅用于展示和仓位比例计算。' },
]
function openAddAccount() { accountVisible.value = true }
async function onAddAccount(v: Record<string, string>) {
  if (!(v.name || '').trim()) return
  try { await addAccount({ name: v.name, equity: v.equity }); await loadExecution() } catch (e) { console.error(e) }
  accountVisible.value = false
}

const queueVisible = ref(false)
const queueFields: ModalField[] = [
  { key: 'strategy', label: '策略名称', placeholder: '趋势跟随-A', hint: '已在策略中心导入的策略。' },
  { key: 'symbol', label: '交易对', placeholder: 'BTC-USDT', hint: '格式：BTC-USDT。' },
  { key: 'action', label: '操作动作', placeholder: '开多', hint: '开多/开空/平多/平空/加仓/减仓。' },
  { key: 'reason', label: '触发原因', placeholder: '1H 突破确认', hint: '记录触发逻辑，便于复盘。' },
]
function openAddQueue() { queueVisible.value = true }
async function onAddQueue(v: Record<string, string>) {
  if (!(v.strategy || '').trim()) return
  try { await addExecutionQueue({ strategy: v.strategy, symbol: v.symbol, action: v.action, reason: v.reason || '手动添加' }); await loadExecution() } catch (e) { console.error(e) }
  queueVisible.value = false
}

const pendingVisible = ref(false)
function openPendingList() { pendingVisible.value = true }

onMounted(async () => { await loadExecution(); timer = window.setInterval(loadExecution, 2000) })
onUnmounted(() => { if (timer !== null) window.clearInterval(timer) })
</script>
