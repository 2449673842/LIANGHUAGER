<template>
  <section class="page">
    <Transition name="toast">
      <div v-if="toast.visible" class="toast" :class="`toast--${toast.tone}`">
        {{ toast.message }}
      </div>
    </Transition>
    <div class="page__header">
      <div class="page__title">
        <h1>回测 / 调参</h1>
        <p>把回测结果、图上买卖点、调参窗口和结果对比放进同一个工作区。</p>
      </div>
      <div class="page__actions">
        <span class="mini-badge">{{ payload.source || candles.source || 'fallback' }}</span>
        <button class="button" @click="openTemplateDialog">参数模板</button>
        <button class="button" @click="openArchiveDialog">结果归档</button>
        <button class="button button--primary" @click="runBacktestNow">运行回测</button>
      </div>
    </div>

    <BacktestWorkbench :payload="payload" :candles="candles.items" :params="backtestParams" @update:params="backtestParams = $event" />

    <!-- 参数模板 -->
    <ModalDialog :visible="showTemplateDialog" title="参数模板" @cancel="showTemplateDialog = false">
      <div v-if="templateList.length" class="modal-field">
        <label>已保存的模板</label>
        <div class="list list--scroll" style="max-height:160px;">
          <div v-for="tpl in templateList" :key="tpl.name" class="list-row" style="cursor:pointer;" @click="loadTemplate(tpl)">
            <span>{{ tpl.name }}</span>
            <span class="muted">{{ tpl.params?.period || '--' }}</span>
          </div>
        </div>
      </div>
      <div class="modal-field">
        <label>新模板名称</label>
        <input v-model="newTemplateName" placeholder="输入模板名称保存当前参数" />
      </div>
      <div class="modal-actions">
        <button class="button" @click="showTemplateDialog = false">取消</button>
        <button class="button button--primary" @click="confirmSaveTemplate" :disabled="!newTemplateName.trim()">保存</button>
      </div>
    </ModalDialog>

    <!-- 结果归档 -->
    <ModalDialog :visible="showArchiveDialog" title="结果归档" @cancel="showArchiveDialog = false">
      <div v-if="archiveList.length" class="modal-field">
        <label>已归档结果</label>
        <div class="list list--scroll" style="max-height:160px;">
          <div v-for="item in archiveList" :key="item.time" class="list-row">
            <span>{{ item.name }}</span>
            <span class="muted">{{ item.time }}</span>
          </div>
        </div>
      </div>
      <div class="modal-field">
        <label>归档当前结果</label>
        <input v-model="newArchiveName" placeholder="输入归档名称" />
      </div>
      <div class="modal-actions">
        <button class="button" @click="showArchiveDialog = false">取消</button>
        <button class="button button--primary" @click="confirmSaveArchive" :disabled="!newArchiveName.trim()">保存</button>
      </div>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import BacktestWorkbench from '../components/terminal/BacktestWorkbench.vue'
import ModalDialog from '../components/cards/ModalDialog.vue'
import { useToast } from '../composables/useToast'
import {
  getBacktestWorkbench,
  getMarketCandles,
  runBacktest,
  getBacktestTemplates,
  saveBacktestTemplate,
  getBacktestArchives,
  saveBacktestArchive,
  type BacktestPayload,
  type CandlePayload,
} from '../services/api'

const payload = ref<BacktestPayload>({ periods: [], metrics: [], trades: [], equityCurve: [] })
const candles = ref<CandlePayload>({ instrumentId: 'BTC-USDT', timeframe: '15m', items: [] })
const backtestParams = ref<Record<string, any>>({
  period: '1M', direction: '做多', capital: 10000,
  leverage: 1, fee: 0.02, slippage: 0.02,
})
let timer: number | null = null
const { toast, showToast } = useToast()

// --- dialogs ---
const showTemplateDialog = ref(false)
const showArchiveDialog = ref(false)
const templateList = ref<Array<{ name: string; params: any }>>([])
const archiveList = ref<Array<{ name: string; params: any; result: any; time: string }>>([])
const newTemplateName = ref('')
const newArchiveName = ref('')

async function loadBacktest() {
  const [b, c] = await Promise.all([getBacktestWorkbench(), getMarketCandles()])
  payload.value = b; candles.value = c
}

// --- run backtest directly ---
async function runBacktestNow() {
  const period = backtestParams.value.period || payload.value.periods?.[0] || '1M'
  try {
    const result = await runBacktest({ period })
    payload.value = result
    showToast('回测运行完成', 'success')
  } catch (e) {
    showToast('回测运行失败', 'error')
    console.error('运行回测失败', e)
    await loadBacktest()
  }
}

// --- template dialog ---
async function openTemplateDialog() {
  try {
    templateList.value = await getBacktestTemplates()
  } catch { templateList.value = [] }
  newTemplateName.value = ''
  showTemplateDialog.value = true
}

async function confirmSaveTemplate() {
  const name = newTemplateName.value.trim()
  if (!name) return
  try {
    await saveBacktestTemplate({ name, params: { period: backtestParams.value.period || payload.value.periods?.[0] || '1M' } })
    templateList.value = await getBacktestTemplates()
    newTemplateName.value = ''
    showToast('模板已保存', 'success')
  } catch (e) { showToast('保存模板失败', 'error'); console.error('保存模板失败', e) }
  showTemplateDialog.value = false
}

function loadTemplate(tpl: { name: string; params: any }) {
  if (tpl?.params?.period) backtestParams.value.period = tpl.params.period
  showTemplateDialog.value = false
}

// --- archive dialog ---
async function openArchiveDialog() {
  try {
    archiveList.value = await getBacktestArchives()
  } catch { archiveList.value = [] }
  newArchiveName.value = ''
  showArchiveDialog.value = true
}

async function confirmSaveArchive() {
  const name = newArchiveName.value.trim()
  if (!name) return
  try {
    await saveBacktestArchive({
      name,
      params: { period: backtestParams.value.period || payload.value.periods?.[0] || '1M' },
      result: payload.value,
    })
    archiveList.value = await getBacktestArchives()
    newArchiveName.value = ''
    showToast('结果已归档', 'success')
  } catch (e) { showToast('归档失败', 'error'); console.error('归档失败', e) }
  showArchiveDialog.value = false
}

onMounted(async () => { await loadBacktest(); timer = window.setInterval(loadBacktest, 10000) })
onUnmounted(() => { if (timer !== null) window.clearInterval(timer) })
</script>

<style scoped>
.modal-field { display: grid; gap: 6px; }
.modal-field label { font-size: 13px; font-weight: 600; color: #4c6782; }
.modal-field select,
.modal-field input { min-height: 42px; padding: 0 14px; border: 1px solid #d9e5ef; border-radius: 12px; background: #f8fbfd; color: #132238; font-size: 14px; outline: none; }
.modal-field select:focus,
.modal-field input:focus { border-color: #2eb8f6; background: #fff; box-shadow: 0 0 0 3px rgba(46, 184, 246, 0.08); }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 4px; }
.modal-actions .button { min-height: 40px; padding: 0 18px; border: 1px solid #d9e5ef; background: #fff; border-radius: 12px; color: #26415f; font-size: 14px; cursor: pointer; }
.modal-actions .button:hover { background: #f4f8fb; }
.modal-actions .button--primary { background: linear-gradient(135deg, #16c8d0 0%, #2fb7f6 100%); color: #fff; border: none; box-shadow: 0 8px 20px rgba(43, 179, 226, 0.18); }
.modal-actions .button--primary:hover { box-shadow: 0 12px 28px rgba(43, 179, 226, 0.28); }

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
