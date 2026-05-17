# Codex 实盘回测 — 升级记录

## 概述

本文档记录 `E:\codex版本实盘回测` 项目自第一阶段骨架完成后，经历的三次功能升级内容。

---

## v4 — 文档发布准备 & 构建修复

### 新增文档

| 文件 | 说明 |
|------|------|
| `docs/index.md` | GitHub 文档首页 |
| `docs/API.md` | 当前后端 API 说明 |
| `docs/PROJECT_STATUS.md` | 当前进度、限制和下一步 |
| `docs/ROADMAP.md` | 后续开发阶段 |
| `docs/GITHUB_PUBLISH.md` | GitHub 仓库和 Pages 发布说明 |
| `docs/_config.yml` | GitHub Pages/Jekyll 基础配置 |

### 变更

- `README.md` 更新为当前真实项目状态，不再停留在第一阶段骨架描述。
- `docs/architecture.md` 更新为当前前后端结构、数据源优先级和边界说明。
- `.gitignore` 增加 `.idea/`、日志、前端 dist、后端缓存忽略规则。
- `frontend/src/services/api.ts` 补齐 `ApiEnvelope<T>` 类型，修复前端生产构建失败。

### 验证

- `npm run build` 已通过。
- 后端主要模块 `py_compile` 已通过。

---

## v1 — 自选列表 & 监控开关

### 新增后端端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/watchlist` | 获取当前自选列表 |
| `POST` | `/api/watchlist` | 添加自选（自动标准化为 BTC-USDT，去重） |
| `DELETE` | `/api/watchlist` | 移除自选 |
| `GET` | `/api/monitoring/state` | 获取监控状态 |
| `POST` | `/api/monitoring/state` | 切换监控开关 |

### 变更文件

- `backend/app/routers/workbench.py` — 新增 `watchlist_symbols`、`monitoring_running` 状态 + 5 个端点
- `frontend/src/services/api.ts` — 新增 5 个监控/自选 API 函数
- `frontend/src/pages/OverviewPage.vue` — 添加自选 + 监控切换按钮
- `frontend/src/components/terminal/TerminalOverview.vue` — toggleMonitoring 事件

---

## v2 — 执行数据管理 & 回测运行 & 策略导入

### 新增后端端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET/POST` | `/api/execution/accounts` | 账户列表管理 |
| `GET/POST` | `/api/execution/queues` | 执行队列管理 |
| `POST` | `/api/backtests/run` | 按周期运行回测 |
| `POST` | `/api/strategies/import` | 导入策略模板 |

### 变更文件

- `backend/app/routers/trading.py` — 内存列表 + 4 个端点
- `backend/app/routers/strategies.py` — 策略导入端点，上游合并逻辑
- `backend/app/routers/workbench.py` — 回测运行端点
- `frontend/src/pages/ExecutionPage.vue` — 按钮调 API
- `frontend/src/pages/BacktestPage.vue` — 运行回调查 API
- `frontend/src/pages/StrategyCenterPage.vue` — 导入策略调 API

---

## v3 — 卡片式模态框 & 详细交互

### 新增功能

- **卡片式模态框** 替换所有 `window.prompt()`，带动画过渡
- **搜索选择**：添加自选时输入过滤 + 下拉选择（50 个币种）
- **字段提示**：每个输入框下方有灰色 hint 文字
- **待确认列表**：执行页查看待确认队列任务
- **周期选择下拉**：回测运行选择 1M/3M/6M/1Y
- **按钮 hover**：全局 `cursor: pointer` + 微过渡

### 新建/变更文件

| 文件 | 改动 |
|------|------|
| `frontend/src/components/cards/ModalDialog.vue` | 新建：通用模态框（slot/select/suggestions/hint/动画） |
| `frontend/src/pages/OverviewPage.vue` | 搜索选择交易对 |
| `frontend/src/pages/ExecutionPage.vue` | 新增账户 + 待确认列表 + 执行队列 三个模态 |
| `frontend/src/pages/BacktestPage.vue` | 运行回测 → select 周期下拉 |
| `frontend/src/pages/StrategyCenterPage.vue` | 导入策略 → 单字段模态 |
| `frontend/src/styles/base.css` | 按钮 hover 效果 |

### ModalDialog 组件接口

```typescript
interface ModalField {
  key: string
  label: string
  placeholder?: string
  type?: 'text' | 'select'
  suggestions?: string[]         // 搜索建议（type=text 时生效）
  options?: {value,label}[]      // 下拉选项（type=select 时生效）
  hint?: string                  // 字段提示
}
// Props: visible, title, subtitle?, fields?, confirmText?, hideCancel?, hideConfirm?, width?
// Slots: default (替换 fields 区域)
// Events: @confirm(values), @cancel
```

---

## 完整 API 端点一览

| 分组 | 方法 | 路径 | 引入 |
|------|------|------|------|
| 健康 | `GET` | `/api/health` | 骨架 |
| 行情 | `GET` | `/api/market/candles` | 骨架 |
| 行情 | `GET` | `/api/market/snapshot` | 骨架 |
| 总览 | `GET` | `/api/workbench/overview` | 骨架 |
| 自选 | `GET/POST/DELETE` | `/api/watchlist` | v1 |
| 监控 | `GET/POST` | `/api/monitoring/state` | v1 |
| 执行 | `GET` | `/api/execution/state` | 骨架 |
| 执行 | `GET/POST` | `/api/execution/accounts` | v2 |
| 执行 | `GET/POST` | `/api/execution/queues` | v2 |
| 回测 | `GET` | `/api/backtests/workbench` | 骨架 |
| 回测 | `POST` | `/api/backtests/run` | v2 |
| 策略 | `GET` | `/api/strategies/board` | 骨架 |
| 策略 | `POST` | `/api/strategies/import` | v2 |
