<template>
  <section class="page">
    <Transition name="toast">
      <div v-if="toast.visible" class="toast" :class="`toast--${toast.tone}`">
        {{ toast.message }}
      </div>
    </Transition>
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

    <!-- 新增账户 -->
    <ModalDialog
      :visible="accountVisible" title="新增账户" :fields="accountFields" confirm-text="添加"
      @confirm="onAddAccount" @cancel="accountVisible = false" />

    <!-- 添加到执行队列 -->
    <ModalDialog
      :visible="queueVisible" title="添加到执行队列"
      subtitle="手动创建一个执行任务。任务默认进入待确认队列，审核后发送给策略引擎。"
      :fields="queueFields" confirm-text="加入队列"
      @confirm="onAddQueue" @cancel="queueVisible = false" />

    <!-- 待确认列表 -->
    <ModalDialog
      :visible="pendingVisible" title="待确认列表"
      subtitle="当前等待审核的执行任务，确认后进入运行队列。"
      :hide-cancel="true" :hide-confirm="true" width="520px"
      @cancel="pendingVisible = false">
      <div v-if="pendingItems.length === 0" class="muted" style="padding: 20px 0; text-align: center; color: #7790a6;">
        暂无待确认的任务
      </div>
      <div v-else class="table table--scroll">
        <div class="table__head table-queue">
          <span>时间</span><span>策略</span><span>标的</span><span>动作</span><span>原因</span><span>状态</span>
        </div>
        <div v-for="item in pendingItems" :key="`${item.time}-${item.strategy}`" class="table__row table-queue">
          <span>{{ item.time }}</span>
          <span>{{ item.strategy }}</span>
          <span>{{ item.symbol }}</span>
          <span>{{ item.action }}</span>
          <span class="muted">{{ item.reason }}</span>
          <span class="tone-neutral">待确认</span>
        </div>
      </div>
      <div style="display:flex;justify-content:flex-end;padding-top:8px;">
        <button class="button" @click="pendingVisible = false">关闭</button>
      </div>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import ExecutionConsole from '../components/terminal/ExecutionConsole.vue'
import ModalDialog, { type ModalField } from '../components/cards/ModalDialog.vue'
import { useToast } from '../composables/useToast'
import { getExecution, addAccount, addExecutionQueue, type ExecutionPayload } from '../services/api'

const { toast, showToast } = useToast()
const payload = ref<ExecutionPayload>({
  mode: 'paper', accounts: [], sessions: [], queues: [],
  runtime: { activeTasks: 0, activeSessions: 0, pendingConfirmations: 0, notificationsSent: 0 },
})
let timer: number | null = null

async function loadExecution() { payload.value = await getExecution() }

const pendingItems = computed(() => payload.value.queues.filter(q => q.state.includes('确认')))

// --- 新增账户 ---
const accountVisible = ref(false)
const accountFields: ModalField[] = [
  { key: 'name', label: '账户名称', placeholder: 'OKX 主账户', hint: '自定义标识，用于区分多账户策略分配。' },
  { key: 'equity', label: '权益 (USDT)', placeholder: '100000', type: 'text', hint: '仅用于展示和仓位比例计算。' },
]
function openAddAccount() { accountVisible.value = true }
async function onAddAccount(v: Record<string, string>) {
  if (!(v.name || '').trim()) return
  try { await addAccount({ name: v.name, equity: v.equity }); await loadExecution(); showToast('账户已添加', 'success') } catch (e) { showToast('添加账户失败', 'error'); console.error(e) }
  accountVisible.value = false
}

// --- 执行队列 ---
const queueVisible = ref(false)
const queueFields: ModalField[] = [
  { key: 'strategy', label: '策略名称', placeholder: '趋势跟随-A', hint: '已在策略中心导入的策略。' },
  { key: 'symbol', label: '交易对', placeholder: 'BTC-USDT', hint: '格式：BTC-USDT。' },
  { key: 'action', label: '操作动作', placeholder: '开多', hint: '开多 / 开空 / 平多 / 平空 / 加仓 / 减仓。' },
  { key: 'reason', label: '触发原因', placeholder: '1H 突破确认', hint: '记录触发逻辑，便于复盘。' },
]
function openAddQueue() { queueVisible.value = true }
async function onAddQueue(v: Record<string, string>) {
  if (!(v.strategy || '').trim()) return
  try { await addExecutionQueue({ strategy: v.strategy, symbol: v.symbol, action: v.action, reason: v.reason || '手动添加' }); await loadExecution(); showToast('任务已加入队列', 'success') } catch (e) { showToast('添加任务失败', 'error'); console.error(e) }
  queueVisible.value = false
}

// --- 待确认列表 ---
const pendingVisible = ref(false)
function openPendingList() { pendingVisible.value = true }

onMounted(async () => { await loadExecution(); timer = window.setInterval(loadExecution, 2000) })
onUnmounted(() => { if (timer !== null) window.clearInterval(timer) })
</script>

<style scoped>
.table-queue { grid-template-columns: 72px 1fr 0.9fr 72px 1fr 68px; }

.toast {
  position: fixed; top: 18px; left: 50%; z-index: 1200;
  transform: translateX(-50%); min-width: 220px; max-width: 520px;
  padding: 11px 16px; border: 1px solid #d9e5ef; border-radius: 12px;
  background: rgba(255, 255, 255, 0.98); color: #26415f;
  text-align: center; box-shadow: 0 16px 46px rgba(100, 125, 155, 0.2);
}
.toast--success { border-color: rgba(24, 179, 107, 0.24); color: #1f9a59; }
.toast--error { border-color: rgba(217, 75, 91, 0.28); color: #d94b5b; }
.toast-enter-active, .toast-leave-active { transition: opacity .18s ease, transform .18s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, -8px); }
</style>
