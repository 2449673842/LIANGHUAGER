<template>
  <aside class="sidebar">
    <div class="sidebar__brand">
      <div class="sidebar__logo">CQ</div>
      <div>
        <strong>Codex 实盘回测</strong>
        <p>OKX 多策略工作台</p>
      </div>
    </div>

    <nav class="sidebar__nav">
      <RouterLink
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="sidebar__link"
        active-class="sidebar__link--active"
      >
        <span class="sidebar__icon">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar__footer">
      <div class="sidebar__status">
        <span class="status-dot"></span>
        <span>主链规划中</span>
      </div>
      <p>第一阶段先重建工作台、交易台和回测台。</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
const items = [
  { to: '/overview', label: '总览终端', icon: '◫' },
  { to: '/strategies', label: '策略中心', icon: '⌘' },
  { to: '/execution', label: '模拟/实盘', icon: '◎' },
  { to: '/backtest', label: '回测/调参', icon: '◭' },
  { to: '/settings', label: '系统设置', icon: '⚙' },
]
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px 20px;
  border-right: 1px solid rgba(217, 229, 239, 0.95);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(16px);
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.sidebar__logo {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, #14c6d3 0%, #2eb8f6 100%);
  color: white;
  font-weight: 800;
}

.sidebar__brand strong {
  display: block;
  color: #10213a;
  font-size: 18px;
}

.sidebar__brand p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6f879f;
}

.sidebar__nav {
  display: grid;
  gap: 8px;
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 48px;
  padding: 0 14px;
  color: #344f6d;
  border-radius: 14px;
  border: 1px solid transparent;
}

.sidebar__link:hover {
  background: #f6fbfd;
  border-color: #e0ebf4;
}

.sidebar__link--active {
  background: linear-gradient(135deg, rgba(21, 201, 208, 0.12), rgba(47, 184, 247, 0.16));
  border-color: rgba(42, 191, 218, 0.34);
  color: #0f87a3;
  font-weight: 700;
}

.sidebar__icon {
  width: 22px;
  text-align: center;
}

.sidebar__footer {
  margin-top: auto;
  padding: 18px 16px;
  border-radius: 16px;
  background: #f8fbfd;
  border: 1px solid #e5edf4;
}

.sidebar__status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #1e9d72;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #30c48d;
}

.sidebar__footer p {
  margin: 10px 0 0;
  color: #6b859d;
  font-size: 13px;
}
</style>
