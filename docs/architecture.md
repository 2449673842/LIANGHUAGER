# 架构说明

## 项目目标

`Codex 版本实盘回测` 是一个独立工作台项目，用于承载 OKX 行情、模拟盘、实盘执行、策略管理和回测调参。

项目不直接复制旧界面，而是复用旧项目中已经跑通的业务逻辑和数据契约，在新前端里重新组织布局与交互。

## 技术栈

- 前端：`Vue 3`、`Vite`、`Pinia`、`Vue Router`、`ECharts`
- 后端：`FastAPI`、`Pydantic`
- 外部能力：OKX Agent CLI、OKX Public REST、旧 `quant_platform` 上游接口

## 数据源优先级

1. `OKX Agent CLI`
2. `OKX Public REST`
3. `quant_platform` 上游接口
4. 本地 fallback/mock 数据

前端会展示当前数据来源，例如 `okx-cli`、`okx-public`、`upstream` 或 `fallback`。这样可以快速判断页面是否处在真实数据路径上。

## 后端结构

- `backend/app/main.py`：FastAPI 入口和路由注册。
- `backend/app/config.py`：上游地址、OKX 地址、CLI 路径、默认交易对配置。
- `backend/app/routers/market.py`：K 线和行情快照。
- `backend/app/routers/workbench.py`：总览、监控、自选和回测工作台。
- `backend/app/routers/trading.py`：模拟/实盘状态、账户和执行队列。
- `backend/app/routers/strategies.py`：策略看板和策略导入。
- `backend/app/services/upstream.py`：OKX CLI、OKX REST、旧平台上游和缓存层。
- `backend/app/services/mock_data.py`：本地兜底数据。

## 前端结构

- `frontend/src/pages`：五个一级页面。
- `frontend/src/components/terminal`：K 线、总览终端、执行终端、回测终端、策略编辑面板。
- `frontend/src/components/cards`：统计卡片、面板卡片、通用模态框。
- `frontend/src/services/api.ts`：前端 API 类型和请求函数。
- `frontend/src/styles/base.css`：全局布局和视觉样式。

## 页面布局规则

- 保持五个一级页面稳定：总览终端、策略中心、模拟/实盘、回测/调参、系统设置。
- 页面整体不要过长，长列表放进面板内部滚动。
- K 线、盘口、执行队列、运行状态和控制入口尽量在首屏可见。
- 实盘动作默认走人工确认队列，后续保留自动执行开关。

## 当前边界

- 自选、监控、账户、队列和策略导入目前使用内存态，服务重启后会恢复默认数据。
- OKX 真实下单、账户资产和确认执行还没有直接开放到前端，需要继续封装安全后端端点。
- 回测运行入口已可用，但目前仍是本地模拟结果，后续要接入旧项目真实回测引擎。
