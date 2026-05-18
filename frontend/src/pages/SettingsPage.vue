<template>
  <section class="page">
    <Transition name="toast">
      <div v-if="toast.visible" class="toast" :class="`toast--${toast.tone}`">
        {{ toast.message }}
      </div>
    </Transition>
    <div class="page__header">
      <div class="page__title">
        <h1>系统设置</h1>
        <p>先把交易接入、提醒通道和运行策略的系统级配置聚合到这里。</p>
      </div>
      <div class="page__actions">
        <span v-if="savedText" class="mini-badge">{{ savedText }}</span>
        <button class="button">导出配置</button>
        <button class="button button--primary" @click="saveAiConfig">保存设置</button>
      </div>
    </div>

    <div class="split-grid">
      <div class="stack">
        <PanelCard title="交易通道" description="第一阶段固定围绕 OKX">
          <div class="field-grid">
            <div class="field">
              <label>交易所</label>
              <input value="OKX" />
            </div>
            <div class="field">
              <label>市场范围</label>
              <input value="现货 + 永续" />
            </div>
            <div class="field">
              <label>默认模式</label>
              <select>
                <option>人工确认</option>
                <option>自动执行</option>
              </select>
            </div>
            <div class="field">
              <label>多账户结构</label>
              <input value="已启用" />
            </div>
          </div>
        </PanelCard>
        <PanelCard title="提醒配置" description="邮件和企业微信先保留为一等配置项">
          <div class="field-grid">
            <div class="field">
              <label>SMTP 服务器</label>
              <input placeholder="smtp.example.com" />
            </div>
            <div class="field">
              <label>发送邮箱</label>
              <input placeholder="alerts@example.com" />
            </div>
            <div class="field">
              <label>企业微信 Webhook</label>
              <input placeholder="https://qyapi.weixin.qq.com/..." />
            </div>
            <div class="field">
              <label>TradingView 桥接</label>
              <input placeholder="后续迁移 quant_platform 桥接服务" />
            </div>
          </div>
        </PanelCard>
        <PanelCard title="AI 分析接口" description="用于首页 AI 趋势、买卖点和后续策略解释">
          <div class="field-grid">
            <div class="field">
              <label>启用 AI 分析</label>
              <select v-model="aiConfig.enabled">
                <option :value="true">启用</option>
                <option :value="false">关闭</option>
              </select>
            </div>
            <div class="field">
              <label>接口类型</label>
              <select v-model="aiConfig.provider">
                <option>OpenAI-compatible</option>
                <option>DeepSeek</option>
                <option>Moonshot</option>
                <option>本地模型</option>
              </select>
            </div>
            <div class="field">
              <label>Base URL</label>
              <input v-model="aiConfig.baseUrl" placeholder="https://api.openai.com/v1" />
            </div>
            <div class="field">
              <label>模型名称</label>
              <input v-model="aiConfig.model" placeholder="gpt-4.1 / deepseek-chat / 本地模型名" />
            </div>
            <div class="field">
              <label>API Key</label>
              <input v-model="aiConfig.apiKey" type="password" :placeholder="aiConfig.hasApiKey ? '已保存，留空则不修改' : 'sk-...'" />
            </div>
            <div class="field">
              <label>超时时间</label>
              <input v-model.number="aiConfig.timeoutSeconds" type="number" min="5" max="120" />
            </div>
          </div>
          <div class="ai-config-status">
            <span :class="aiConfig.enabled ? 'tone-up' : 'tone-neutral'">{{ aiConfig.enabled ? 'AI分析已启用' : 'AI分析未启用' }}</span>
            <span>{{ aiConfig.hasApiKey || aiConfig.apiKey ? 'API Key 已配置' : '尚未配置 API Key' }}</span>
          </div>
        </PanelCard>
      </div>

      <div class="stack">
        <PanelCard title="系统说明" description="这不是最终业务逻辑，只是第一阶段工作台骨架">
          <div class="list">
            <div class="list-row"><span>前端</span><span>Vue 3 + Router + Pinia</span></div>
            <div class="list-row"><span>后端</span><span>FastAPI 独立骨架</span></div>
            <div class="list-row"><span>主数据源</span><span>OKX</span></div>
            <div class="list-row"><span>AI 分析</span><span>{{ aiConfig.enabled ? aiConfig.provider : '本地规则引擎' }}</span></div>
            <div class="list-row"><span>迁移来源</span><span>quant_platform + trading-dashboard</span></div>
          </div>
        </PanelCard>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useToast } from '../composables/useToast'
const { toast, showToast } = useToast()
import { onMounted, reactive, ref } from 'vue'
import PanelCard from '../components/cards/PanelCard.vue'
import { getAiSettings, saveAiSettings } from '../services/api'

const savedText = ref('')
let savedTimer: number | null = null

const aiConfig = reactive({
  enabled: false,
  provider: 'OpenAI-compatible',
  baseUrl: '',
  model: '',
  apiKey: '',
  hasApiKey: false,
  timeoutSeconds: 20,
})

function showSaved(text: string) {
  savedText.value = text
  if (savedTimer !== null) window.clearTimeout(savedTimer)
  savedTimer = window.setTimeout(() => {
    savedText.value = ''
  }, 2400)
}

async function loadAiConfig() {
  const payload = await getAiSettings()
  aiConfig.enabled = payload.enabled
  aiConfig.provider = payload.provider || 'OpenAI-compatible'
  aiConfig.baseUrl = payload.baseUrl || ''
  aiConfig.model = payload.model || ''
  aiConfig.apiKey = ''
  aiConfig.hasApiKey = payload.hasApiKey
  aiConfig.timeoutSeconds = payload.timeoutSeconds || 20
}

async function saveAiConfig() {
  const payload = await saveAiSettings({
    enabled: aiConfig.enabled,
    provider: aiConfig.provider,
    baseUrl: aiConfig.baseUrl,
    model: aiConfig.model,
    apiKey: aiConfig.apiKey,
    timeoutSeconds: aiConfig.timeoutSeconds,
  })
  aiConfig.apiKey = ''
  aiConfig.hasApiKey = payload.hasApiKey
  showSaved('设置已保存')
}

onMounted(() => {
  void loadAiConfig()
})
</script>

<style scoped>
.ai-config-status {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: #607a96;
  font-size: 13px;
}
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
