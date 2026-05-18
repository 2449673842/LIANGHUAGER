<template>
  <div class="strategy-workbench-grid">
    <PanelCard title="策略编辑器" description="代码可编辑、可检查、可保存版本，并发布到运行台">
      <template #actions>
        <div class="inline-toolbar">
          <button class="button" @click="undo" :disabled="!canUndo">撤销</button>
          <button class="button" @click="redo" :disabled="!canRedo">重做</button>
          <button class="button" @click="checkCurrentCode">检查代码</button>
          <button class="button" @click="openSaveVersionDialog" :disabled="!unsaved">保存版本</button>
          <button class="button" @click="toggleDiff">版本对比</button>
          <button class="button" @click="() => runStrategyBacktest()">运行回测</button>
          <button class="button button--primary" @click="publishCurrentStrategy">发布到运行台</button>
        </div>
      </template>

      <div class="editor-meta">
        <span class="mini-badge">{{ selectedItem?.label || '未选择策略' }}</span>
        <span class="mini-badge">{{ activeInstrument }} / {{ activeTimeframe }}</span>
        <span v-if="lastCheck" :class="lastCheck.ok ? 'tone-up' : 'tone-down'">
          {{ lastCheck.ok ? '检查通过' : '检查失败' }} · {{ lastCheck.checkedAt }}
        </span>
        <span v-if="backtestLoading" class="tone-neutral">回测运行中...</span>
        <span v-if="unsaved" class="tone-neutral">● 未保存</span>
      </div>

      <textarea v-model="source" class="code-editor" spellcheck="false" @input="onCodeInput" />

      <div v-if="lastCheck" class="check-result">
        <div v-if="lastCheck.errors.length" class="list list--scroll">
          <div v-for="error in lastCheck.errors" :key="error" class="list-row">
            <span class="tone-down">{{ error }}</span>
          </div>
        </div>
        <div v-if="lastCheck.warnings.length" class="list list--scroll">
          <div v-for="warning in lastCheck.warnings" :key="warning" class="list-row">
            <span class="tone-neutral">{{ warning }}</span>
          </div>
        </div>
      </div>

      <div v-if="showDiff" class="diff-panel">
        <h4>版本差异</h4>
        <pre class="diff-code"><code>{{ diffText }}</code></pre>
      </div>
    </PanelCard>

    <div class="stack">
      <PanelCard title="K线与回测预览" description="选择策略后加载对应标的 K 线，运行回测后即时刷新指标">
        <template #actions>
          <div class="inline-toolbar">
            <button
              v-for="tf in timeframeOptions"
              :key="tf"
              class="tab"
              :class="tf === activeTimeframe ? 'tab--active' : ''"
              @click="switchTimeframe(tf)"
            >
              {{ tf }}
            </button>
            <button class="button" @click="loadCandlesForSelection">刷新K线</button>
          </div>
        </template>

        <div class="preview-grid">
          <MarketKlineChart :items="candles" />
          <div class="preview-side">
            <div class="metric-grid metric-grid--compact">
              <div v-for="metric in backtestPreview.metrics" :key="metric.label" class="runtime-tile">
                <span>{{ metric.label }}</span>
                <strong :class="toneClass(metric.tone)">{{ metric.value }}</strong>
              </div>
            </div>
            <div class="equity-mini">
              <EquityCurveChart :points="backtestPreview.equityCurve" />
            </div>
          </div>
        </div>
      </PanelCard>

      <PanelCard title="回测交易预览" description="运行回测后查看买卖点与原因">
        <div class="table table--scroll">
          <div class="table__head table-preview-trades">
            <span>时间</span><span>方向</span><span>价格</span><span>原因</span>
          </div>
          <div v-for="row in backtestPreview.trades" :key="`${row.time}-${row.side}-${row.price}`" class="table__row table-preview-trades">
            <span>{{ row.time }}</span>
            <span :class="row.side === '买入' ? 'tone-up' : 'tone-down'">{{ row.side }}</span>
            <span>{{ row.price }}</span>
            <span>{{ row.reason }}</span>
          </div>
        </div>
      </PanelCard>
    </div>

    <div class="stack strategy-side-panel">
      <PanelCard title="运行参数" :description="dynamicParams.length ? '根据策略注释自动生成' : '参数会参与策略中心内置回测预览'">
        <div class="field-grid">
          <template v-if="dynamicParams.length">
            <div v-for="param in dynamicParams" :key="param.name" class="field">
              <label>{{ param.label }}<span v-if="param.required" style="color:#e74c3c;"> *</span></label>
              <input v-if="param.type === 'number'" v-model="param.value" type="number" :min="param.min" :max="param.max" :step="param.step || 0.01" />
              <select v-else-if="param.type === 'enum'" v-model="param.value">
                <option v-for="opt in param.options" :key="opt" :value="opt">{{ opt }}</option>
              </select>
              <input v-else v-model="param.value" />
            </div>
          </template>
          <template v-else>
            <div class="field">
              <label>策略名</label>
              <input v-model="params.strategyName" />
            </div>
            <div class="field">
              <label>交易方向</label>
              <select v-model="params.direction">
                <option>做多</option>
                <option>做空</option>
                <option>双向</option>
              </select>
            </div>
            <div class="field">
              <label>初始资金</label>
              <input v-model="params.capital" />
            </div>
            <div class="field">
              <label>杠杆</label>
              <input v-model="params.leverage" />
            </div>
            <div class="field">
              <label>手续费 (%)</label>
              <input v-model="params.fee" />
            </div>
            <div class="field">
              <label>滑点 (%)</label>
              <input v-model="params.slippage" />
            </div>
          </template>
        </div>
      </PanelCard>

      <PanelCard title="策略列表" description="点击策略后加载源码、版本历史、K线和回测预览">
        <div class="list list--scroll strategy-list-scroll">
          <button
            v-for="item in board.items"
            :key="item.versionId"
            type="button"
            class="list-row strategy-row"
            :class="item.strategyId === selectedStrategyId ? 'strategy-row--active' : ''"
            @click="selectStrategy(item.strategyId)"
          >
            <div>
              <strong>{{ item.label }}</strong>
              <div class="muted">{{ item.instrumentId }} / {{ item.timeframe }} / {{ item.versionId }}</div>
            </div>
            <div style="text-align: right">
              <strong :class="statusTone(item.status)">{{ item.status }}</strong>
              <div class="muted">{{ item.updatedAt }}</div>
            </div>
          </button>
        </div>
      </PanelCard>

      <PanelCard title="版本历史" description="保存版本后会显示在这里">
        <div class="list list--scroll strategy-version-scroll">
          <div v-for="version in versions" :key="version.versionId" class="list-row">
            <div>
              <strong>{{ version.versionId }}</strong>
              <div class="muted">{{ version.note || '无备注' }}</div>
            </div>
            <div style="text-align: right">
              <strong :class="statusTone(version.status)">{{ version.status }}</strong>
              <div class="muted">{{ version.updatedAt }}</div>
            </div>
          </div>
        </div>
      </PanelCard>
    </div>

    <ModalDialog
      :visible="showSaveDialog" title="保存策略版本" width="420px"
      @cancel="showSaveDialog = false">
      <div class="modal-field">
        <label>版本备注</label>
        <input v-model="versionNote" placeholder="例如 调整止损/止盈参数" />
      </div>
      <div class="modal-actions">
        <button class="button" @click="showSaveDialog = false">取消</button>
        <button class="button button--primary" @click="saveCurrentVersion">保存</button>
      </div>
    </ModalDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, reactive, ref, watch } from 'vue'
import PanelCard from '../cards/PanelCard.vue'
import ModalDialog from '../cards/ModalDialog.vue'
import MarketKlineChart from './MarketKlineChart.vue'
import EquityCurveChart from './EquityCurveChart.vue'
import {
  checkStrategyCode,
  getMarketCandles,
  getStrategyCode,
  getStrategyVersions,
  publishStrategy,
  runBacktest,
  saveStrategyCode,
  saveStrategyVersion,
  type BacktestPayload,
  type CandlePoint,
  type StrategyBoardPayload,
  type StrategyVersionItem,
} from '../../services/api'

const props = defineProps<{
  board: StrategyBoardPayload
}>()

const emit = defineEmits<{
  refresh: []
}>()

const showToast = inject<(msg: string, tone?: 'neutral' | 'success' | 'error') => void>('showToast', () => {})

const selectedStrategyId = ref('')
const source = ref('')
const versions = ref<StrategyVersionItem[]>([])
const candles = ref<CandlePoint[]>([])
const lastCheck = ref<{ ok: boolean; errors: string[]; warnings: string[]; checkedAt: string } | null>(null)
const showSaveDialog = ref(false)
const versionNote = ref('')
const backtestLoading = ref(false)
const unsaved = ref(false)
const showDiff = ref(false)
const diffText = ref('')
const dynamicParams = ref<any[]>([])

// undo/redo
const undoStack = ref<string[]>([])
const redoStack = ref<string[]>([])
const isUndoRedo = ref(false)
const canUndo = computed(() => undoStack.value.length > 0)
const canRedo = computed(() => redoStack.value.length > 0)

const backtestPreview = ref<BacktestPayload>({
  periods: ['1M', '3M', '6M', '1Y'],
  metrics: [],
  trades: [],
  equityCurve: [],
})

const params = reactive({
  strategyName: '',
  direction: '做多',
  capital: '10000',
  leverage: '1',
  fee: '0.05',
  slippage: '0.03',
})

const timeframeOptions = ['15m', '1H', '4H', '1D']
const activeTimeframe = ref('15m')
const selectedItem = computed(() => props.board.items.find((item) => item.strategyId === selectedStrategyId.value))
const activeInstrument = computed(() => selectedItem.value?.instrumentId || 'BTC-USDT')

watch(source, (newVal, oldVal) => {
  if (!isUndoRedo.value && typeof oldVal === 'string') {
    undoStack.value.push(oldVal)
    if (undoStack.value.length > 50) undoStack.value.shift()
    redoStack.value = []
  }
  parseParams()
})

watch(
  () => props.board.items,
  async (items) => {
    if (!selectedStrategyId.value && items.length) {
      await selectStrategy(items[0].strategyId)
    }
  },
  { immediate: true },
)

function onCodeInput() {
  unsaved.value = true
}

function undo() {
  if (undoStack.value.length === 0) return
  isUndoRedo.value = true
  const prev = undoStack.value.pop()!
  redoStack.value.push(source.value)
  source.value = prev
  isUndoRedo.value = false
  unsaved.value = true
}

function redo() {
  if (redoStack.value.length === 0) return
  isUndoRedo.value = true
  const next = redoStack.value.pop()!
  undoStack.value.push(source.value)
  source.value = next
  isUndoRedo.value = false
  unsaved.value = true
}

function parseParams() {
  const res: any[] = []
  const lines = (source.value || '').split(/\r?\n/)
  for (const line of lines) {
    const m = line.match(/#\s*@strategy\s+(\w+)\s+(.+)/)
    if (!m) continue
    const name = m[1]
    const tokens = m[2].trim().split(/\s+/)
    const defaultToken = tokens.shift() || ''
    let type = 'string'
    let parsed: any = defaultToken
    let options: string[] | undefined
    if (defaultToken === 'true' || defaultToken === 'false') {
      type = 'boolean'
      parsed = defaultToken === 'true'
    } else if (defaultToken.startsWith('[') && defaultToken.endsWith(']')) {
      type = 'enum'
      options = defaultToken.slice(1, -1).split(',').map(s => s.trim())
      parsed = options[0]
    } else if (!isNaN(Number(defaultToken))) {
      type = 'number'
      parsed = Number(defaultToken)
    }
    const extra: Record<string, any> = {}
    for (const t of tokens) {
      const kv = t.split('=')
      if (kv.length === 2) {
        const numVal = Number(kv[1])
        extra[kv[0]] = isNaN(numVal) ? kv[1] : numVal
      } else if (t.toLowerCase() === 'required') extra.required = true
      else if (t.toLowerCase() === 'optional') extra.required = false
    }
    res.push({
      name, label: name, type, value: parsed,
      options,
      required: extra.required !== undefined ? extra.required : false,
      min: type === 'number' ? extra.min : undefined,
      max: type === 'number' ? extra.max : undefined,
      step: type === 'number' ? extra.step : undefined,
    })
  }
  dynamicParams.value = res
}

function toggleDiff() {
  if (!showDiff.value && versions.value.length >= 2) {
    const latest = versions.value[0]
    const prev = versions.value[1]
    diffText.value = `最新: ${latest?.versionId || '—'}\n前版: ${prev?.versionId || '—'}\n\n(选择不同版本对比)`
  }
  showDiff.value = !showDiff.value
}

async function selectStrategy(strategyId: string) {
  selectedStrategyId.value = strategyId
  lastCheck.value = null
  unsaved.value = false
  showDiff.value = false
  undoStack.value = []
  redoStack.value = []
  const item = props.board.items.find((entry) => entry.strategyId === strategyId)
  params.strategyName = item?.label || strategyId
  activeTimeframe.value = normalizeTimeframe(item?.timeframe || '15m')
  const [codePayload, versionPayload] = await Promise.all([getStrategyCode(strategyId), getStrategyVersions(strategyId)])
  source.value = codePayload.code
  versions.value = versionPayload
  parseParams()
  await Promise.all([loadCandlesForSelection(), runStrategyBacktest(false)])
}

async function loadCandlesForSelection() {
  const candlePayload = await getMarketCandles(activeInstrument.value, activeTimeframe.value, 160)
  candles.value = candlePayload.items
}

async function switchTimeframe(timeframe: string) {
  activeTimeframe.value = timeframe
  await loadCandlesForSelection()
  await runStrategyBacktest()
}

async function runStrategyBacktest(saveCodeBeforeRun = true) {
  if (!selectedStrategyId.value) return
  backtestLoading.value = true
  try {
    if (saveCodeBeforeRun) {
      await saveStrategyCode(selectedStrategyId.value, source.value)
    }
    // Map K-line timeframe to backtest period for visual variety
    const periodMap: Record<string, string> = { '15m': '1M', '1H': '3M', '4H': '6M', '1D': '1Y' }
    const btPeriod = periodMap[activeTimeframe.value] || '1M'
    backtestPreview.value = await runBacktest({
      period: btPeriod,
      strategyId: selectedStrategyId.value,
      instrumentId: activeInstrument.value,
      timeframe: activeTimeframe.value,
      direction: params.direction,
      capital: params.capital,
      leverage: params.leverage,
      fee: params.fee,
      slippage: params.slippage,
      code: source.value,
    })
    showToast('回测完成', 'success')
  } catch (e) {
    console.error('回测失败', e)
    showToast('回测失败', 'error')
  } finally {
    backtestLoading.value = false
  }
}

async function checkCurrentCode() {
  lastCheck.value = await checkStrategyCode(source.value)
}

function openSaveVersionDialog() {
  versionNote.value = ''
  showSaveDialog.value = true
}

async function saveCurrentVersion() {
  if (!selectedStrategyId.value) return
  await saveStrategyCode(selectedStrategyId.value, source.value)
  await saveStrategyVersion(selectedStrategyId.value, source.value, versionNote.value || '保存策略版本')
  versions.value = await getStrategyVersions(selectedStrategyId.value)
  showSaveDialog.value = false
  emit('refresh')
}

async function publishCurrentStrategy() {
  if (!selectedStrategyId.value) return
  await saveStrategyCode(selectedStrategyId.value, source.value)
  await publishStrategy(selectedStrategyId.value, versions.value[0]?.versionId)
  emit('refresh')
}

function normalizeTimeframe(timeframe: string) {
  if (timeframe === '1h') return '1H'
  if (timeframe === '4h') return '4H'
  if (timeframe === '1d') return '1D'
  return timeframe || '15m'
}

function statusTone(status: string) {
  if (status.includes('运行') || status.includes('发布') || status.includes('保存')) return 'tone-up'
  if (status.includes('告警') || status.includes('禁用') || status.includes('失败')) return 'tone-down'
  return 'tone-neutral'
}

function toneClass(tone?: 'up' | 'down' | 'neutral') {
  if (tone === 'up') return 'tone-up'
  if (tone === 'down') return 'tone-down'
  return 'tone-neutral'
}
</script>

<style scoped>
.strategy-workbench-grid {
  display: grid;
  grid-template-columns: minmax(360px, 0.92fr) minmax(520px, 1.35fr) minmax(300px, 0.8fr);
  gap: 16px;
  align-items: start;
}

.code-editor {
  min-height: 430px;
  max-height: 560px;
  width: 100%;
  padding: 18px;
  border-radius: 14px;
  border: 1px solid #d8e6f0;
  background: #0f1723;
  color: #dfe8f0;
  overflow: auto;
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
}

.editor-meta,
.check-result {
  display: grid;
  gap: 10px;
}

.preview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 14px;
  align-items: start;
}

.preview-side {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.metric-grid--compact {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.runtime-tile {
  display: grid;
  gap: 6px;
  min-height: 72px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid #e4edf4;
  background: #f8fbfd;
}

.runtime-tile span {
  color: #688299;
  font-size: 13px;
}

.runtime-tile strong {
  font-size: 20px;
  color: #11233d;
}

.equity-mini :deep(.chart-surface--equity) {
  height: 180px;
}

.strategy-row {
  width: 100%;
  border: 1px solid #e5edf4;
  text-align: left;
  cursor: pointer;
}

.strategy-row--active {
  border-color: rgba(42, 191, 218, 0.58);
  background: linear-gradient(135deg, rgba(28, 201, 208, 0.12), rgba(47, 184, 247, 0.12));
}

.strategy-list-scroll {
  max-height: 260px;
}

.strategy-version-scroll {
  max-height: 170px;
}

.table-preview-trades {
  grid-template-columns: 1.3fr 58px 88px 1fr;
}

@media (max-width: 1380px) {
  .strategy-workbench-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .preview-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

.modal-field { display: grid; gap: 6px; }
.modal-field label { font-size: 13px; font-weight: 600; color: #4c6782; }
.modal-field input { min-height: 42px; padding: 0 14px; border: 1px solid #d9e5ef; border-radius: 12px; background: #f8fbfd; color: #132238; font-size: 14px; outline: none; }
.modal-field input:focus { border-color: #2eb8f6; background: #fff; box-shadow: 0 0 0 3px rgba(46, 184, 246, 0.08); }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 4px; }
.modal-actions .button { min-height: 40px; padding: 0 18px; border: 1px solid #d9e5ef; background: #fff; border-radius: 12px; color: #26415f; font-size: 14px; cursor: pointer; }
.modal-actions .button:hover { background: #f4f8fb; }
.modal-actions .button--primary { background: linear-gradient(135deg, #16c8d0 0%, #2fb7f6 100%); color: #fff; border: none; box-shadow: 0 8px 20px rgba(43, 179, 226, 0.18); }
.modal-actions .button--primary:hover { box-shadow: 0 12px 28px rgba(43, 179, 226, 0.28); }
.diff-panel { margin-top: 12px; padding: 14px; border: 1px solid #d8e6f0; border-radius: 12px; background: #f8fbfd; }
.diff-panel h4 { margin: 0 0 8px; color: #688299; font-size: 13px; }
.diff-code { max-height: 200px; overflow: auto; padding: 10px; border-radius: 8px; background: #0f1723; color: #dfe8f0; font-size: 12px; font-family: Consolas, monospace; margin: 0; }
</style>