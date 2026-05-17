<template>
  <section class="page">
    <div class="page__header">
      <div class="page__title">
        <h1>系统设置</h1>
        <p>先把交易接入、提醒通道和运行策略的系统级配置聚合到这里。</p>
      </div>
      <div class="page__actions">
        <button class="button">导出配置</button>
        <button class="button button--primary">保存设置</button>
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
      </div>

      <div class="stack">
        <PanelCard title="系统说明" description="这不是最终业务逻辑，只是第一阶段工作台骨架">
          <div class="list">
            <div class="list-row"><span>前端</span><span>Vue 3 + Router + Pinia</span></div>
            <div class="list-row"><span>后端</span><span>FastAPI 独立骨架</span></div>
            <div class="list-row"><span>主数据源</span><span>OKX</span></div>
            <div class="list-row"><span>迁移来源</span><span>quant_platform + trading-dashboard</span></div>
          </div>
        </PanelCard>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import PanelCard from '../components/cards/PanelCard.vue'
</script>
