<template>
  <section class="page">
    <Transition name="toast">
      <div v-if="toast.visible" class="toast" :class="`toast--${toast.tone}`">
        {{ toast.message }}
      </div>
    </Transition>
    <div class="page__header">
      <div class="page__title">
        <h1>策略中心</h1>
        <p>策略源码编辑、版本保存、模板创建，并可发布到执行队列。</p>
      </div>
      <div class="page__actions">
        <span class="mini-badge">{{ board.source || 'local' }}</span>
        <button class="button" @click="openImportDialog">导入策略</button>
        <button class="button" @click="openTemplateDialog">模板管理</button>
        <button class="button button--primary" @click="refreshBoard">刷新策略</button>
      </div>
    </div>

    <div class="search-toolbar" style="margin-bottom:12px;">
      <input class="search-input" v-model="searchKeyword" placeholder="搜索策略名称/标的/周期" style="width:100%;padding:8px 14px;border:1px solid #d9e5ef;border-radius:10px;font-size:14px;outline:none;" />
    </div>
    <StrategyEditorPanel :board="filteredBoard" @refresh="refreshBoard" />

    <!-- 导入策略弹窗 -->
    <ModalDialog
      :visible="showImportDialog" title="导入策略" width="560px"
      @cancel="showImportDialog = false">
      <div class="modal-field">
        <label>策略名称</label>
        <input v-model="importForm.label" placeholder="例如 BTC 趋势跟随" />
      </div>
      <div class="modal-field">
        <label>标的</label>
        <input v-model="importForm.instrumentId" placeholder="例如 BTC-USDT" />
      </div>
      <div class="modal-field">
        <label>周期</label>
        <input v-model="importForm.timeframe" placeholder="例如 15m" />
      </div>
      <div class="modal-field">
        <label>策略代码</label>
        <textarea v-model="importForm.code" class="field-textarea" placeholder="粘贴 Python 策略代码，可留空使用默认模板" />
      </div>
      <div class="modal-actions">
        <button class="button" @click="showImportDialog = false">取消</button>
        <button class="button button--primary" @click="confirmImport">确认导入</button>
      </div>
    </ModalDialog>

    <!-- 模板管理弹窗 -->
    <ModalDialog
      :visible="showTemplateDialog" title="模板管理" width="560px"
      @cancel="showTemplateDialog = false">
      <div v-if="templates.length === 0" style="color:#9bb1c4;padding:10px 0;">暂无模板，请先保存模板。</div>
      <div v-for="tpl in templates" :key="tpl.id" style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #edf3f8;">
        <div>
          <strong>{{ tpl.label }}</strong>
          <div style="font-size:12px;color:#9bb1c4;">{{ tpl.instrumentId }} / {{ tpl.timeframe }}</div>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="button" style="padding:5px 10px;font-size:12px;" @click="applyTemplate(tpl)">加载</button>
          <button class="button" style="padding:5px 10px;font-size:12px;" @click="renameTemplateDialog(tpl)">重命名</button>
          <button class="button" style="padding:5px 10px;font-size:12px;color:#e74c3c;border-color:#f5c6cb;" @click="deleteTemplateConfirm(tpl)">删除</button>
        </div>
      </div>
      <div style="margin-top:14px;padding-top:14px;border-top:1px solid #edf3f8;">
        <h4 style="font-size:14px;margin-bottom:10px;color:#688299;">保存当前为模板</h4>
        <div class="modal-field">
          <input v-model="newTemplateName" placeholder="输入模板名称" />
        </div>
        <div class="modal-actions">
          <button class="button button--primary" @click="saveTemplateCurrent" :disabled="!newTemplateName.trim()">保存模板</button>
        </div>
      </div>
    </ModalDialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import StrategyEditorPanel from '../components/terminal/StrategyEditorPanel.vue'
import ModalDialog from '../components/cards/ModalDialog.vue'
import { useToast } from '../composables/useToast'
import {
  createStrategyFromTemplate,
  getStrategyBoard,
  getStrategyTemplates,
  importStrategy,
  saveStrategyTemplate,
  renameStrategyTemplate,
  deleteStrategyTemplate,
  type StrategyBoardPayload,
  type StrategyTemplateItem,
} from '../services/api'

const board = ref<StrategyBoardPayload>({
  items: [],
})

const templates = ref<StrategyTemplateItem[]>([])
const showImportDialog = ref(false)
const showTemplateDialog = ref(false)
const searchKeyword = ref('')
const newTemplateName = ref('')

const { toast, showToast } = useToast()
import { provide } from 'vue'
provide('showToast', showToast)

const filteredBoard = computed<StrategyBoardPayload>(() => {
  const k = searchKeyword.value.trim().toLowerCase()
  if (!k) return board.value
  const filtered = board.value.items.filter(item =>
    `${item.label} ${item.instrumentId} ${item.timeframe}`.toLowerCase().includes(k)
  )
  return { ...board.value, items: filtered }
})

const importForm = reactive({
  label: '',
  instrumentId: 'BTC-USDT',
  timeframe: '15m',
  code: '',
})

async function refreshBoard() {
  board.value = await getStrategyBoard()
}

function openImportDialog() {
  importForm.label = ''
  importForm.instrumentId = 'BTC-USDT'
  importForm.timeframe = '15m'
  importForm.code = ''
  showImportDialog.value = true
}

async function openTemplateDialog() {
  templates.value = await getStrategyTemplates()
  newTemplateName.value = ''
  showTemplateDialog.value = true
}

async function confirmImport() {
  if (!importForm.label.trim()) return
  await importStrategy({
    label: importForm.label.trim(),
    instrumentId: importForm.instrumentId.trim(),
    timeframe: importForm.timeframe.trim(),
    code: importForm.code,
  })
  showImportDialog.value = false
  await refreshBoard()
  showToast('策略已导入', 'success')
}

async function applyTemplate(tpl: StrategyTemplateItem) {
  await createStrategyFromTemplate({
    templateId: tpl.id,
    label: tpl.label,
    instrumentId: tpl.instrumentId,
    timeframe: tpl.timeframe,
  })
  showTemplateDialog.value = false
  await refreshBoard()
}

async function renameTemplateDialog(tpl: StrategyTemplateItem) {
  const name = prompt('新名称', tpl.label)
  if (!name || !name.trim()) return
  try {
    await renameStrategyTemplate(tpl.id, name.trim())
    templates.value = await getStrategyTemplates()
    showToast('模板已重命名', 'success')
  } catch (e) { showToast('重命名失败', 'error'); console.error('重命名失败', e) }
}

async function deleteTemplateConfirm(tpl: StrategyTemplateItem) {
  if (!confirm(`确认删除模板「${tpl.label}」？`)) return
  try {
    await deleteStrategyTemplate(tpl.id)
    templates.value = await getStrategyTemplates()
    showToast('模板已删除', 'success')
  } catch (e) { showToast('删除失败', 'error'); console.error('删除失败', e) }
}

async function saveTemplateCurrent() {
  const name = newTemplateName.value.trim()
  if (!name) return
  try {
    await saveStrategyTemplate({ name })
    newTemplateName.value = ''
    templates.value = await getStrategyTemplates()
    showToast('模板已保存', 'success')
  } catch (e) { showToast('保存模板失败', 'error'); console.error('保存失败', e) }
}

onMounted(async () => {
  await Promise.all([refreshBoard(), getStrategyTemplates().then((items) => (templates.value = items))])
})
</script>

<style scoped>
.modal-field { display: grid; gap: 6px; }
.modal-field label { font-size: 13px; font-weight: 600; color: #4c6782; }
.modal-field input,
.modal-field select { min-height: 42px; padding: 0 14px; border: 1px solid #d9e5ef; border-radius: 12px; background: #f8fbfd; color: #132238; font-size: 14px; outline: none; }
.modal-field input:focus,
.modal-field select:focus { border-color: #2eb8f6; background: #fff; box-shadow: 0 0 0 3px rgba(46, 184, 246, 0.08); }
.field-textarea { min-height: 100px; padding: 12px 14px; border: 1px solid #d9e5ef; border-radius: 12px; background: #f8fbfd; color: #132238; font-size: 13px; font-family: Consolas, monospace; outline: none; resize: vertical; }
.field-textarea:focus { border-color: #2eb8f6; background: #fff; box-shadow: 0 0 0 3px rgba(46, 184, 246, 0.08); }
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
