<template>
  <section class="page">
    <div class="page__header">
      <div class="page__title">
        <h1>策略中心</h1>
        <p>第一阶段先把已有 Python 策略编辑、参数和版本入口迁进新工作台。</p>
      </div>
      <div class="page__actions">
        <button class="button" @click="openImport">导入策略</button>
        <button class="button">新建模板</button>
        <button class="button button--primary">发布到运行台</button>
      </div>
    </div>

    <StrategyEditorPanel :board="board" />

    <ModalDialog
      :visible="importVisible"
      title="导入策略"
      subtitle="将一个新的策略模板导入到策略中心。导入后即可在回测和实盘中引用该策略，建议命名规范：${策略风格}-${序号}。"
      :fields="importFields"
      confirm-text="导入"
      @confirm="onImport"
      @cancel="importVisible = false"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import StrategyEditorPanel from '../components/terminal/StrategyEditorPanel.vue'
import ModalDialog, { type ModalField } from '../components/cards/ModalDialog.vue'
import { getStrategyBoard, importStrategy, type StrategyBoardPayload } from '../services/api'

const board = ref<StrategyBoardPayload>({
  items: [],
})

async function load() {
  board.value = await getStrategyBoard()
}

// --- import modal ---
const importVisible = ref(false)
const importFields: ModalField[] = [
  {
    key: 'label',
    label: '策略名称',
    placeholder: '趋势跟随-B',
    hint: '导入的策略将以当前名称创建初始版本 (v1.0.0)，默认交易对为 BTC-USDT、周期 15m。导入后可在策略列表中编辑参数。',
  },
]

function openImport() {
  importVisible.value = true
}

async function onImport(values: Record<string, string>) {
  const label = (values.label || '').trim()
  if (!label) return
  try {
    await importStrategy({ label })
    board.value = await getStrategyBoard()
  } catch (error) {
    console.error('导入策略失败', error)
  }
  importVisible.value = false
}

onMounted(async () => {
  await load()
})
</script>
