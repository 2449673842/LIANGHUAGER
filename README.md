# Codex 版本实盘回测

独立重建中的 OKX 实盘、模拟盘、回测一体化工作台。

当前主线目录固定为 `E:\codex版本实盘回测`。项目采用 `Vue 3 + Vite + Pinia` 前端和 `FastAPI` 后端，目标是把旧项目里的可用后端逻辑、`trading-dashboard` 的 K 线/模拟/实盘能力，以及 OKX 官方能力整合成一个可持续维护的新项目。

## 当前状态

- 五个一级页面已经完成：总览终端、策略中心、模拟/实盘、回测/调参、系统设置。
- 总览页已接入 K 线、盘口、自选列表、行情脉冲、监控开关和快速刷新。
- 模拟/实盘页已接入账户列表、运行会话、执行队列、待确认弹窗。
- 回测页已接入回测指标、资金曲线、交易记录和周期运行入口。
- 策略中心已接入策略列表和策略导入入口。
- 数据源优先级为 `OKX Agent CLI -> OKX Public REST -> quant_platform 上游 -> 本地 fallback`。
- 前端生产构建已通过，后端主要模块语法检查已通过。

## 快速启动

### 后端

```powershell
cd E:\codex版本实盘回测\backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8100
```

后端默认地址：`http://127.0.0.1:8100`

### 前端

```powershell
cd E:\codex版本实盘回测\frontend
npm install
npm run dev -- --host 0.0.0.0 --port 9502
```

前端默认地址：`http://127.0.0.1:9502`

## 环境变量

```powershell
set CODEX_UPSTREAM_BASE_URL=http://127.0.0.1:5000
set CODEX_UPSTREAM_TIMEOUT=6
set CODEX_OKX_BASE_URL=https://www.okx.com
set CODEX_OKX_CLI_PATH=C:\Users\SZC\AppData\Roaming\npm\okx.cmd
set CODEX_DEFAULT_INSTRUMENT=BTC-USDT
set CODEX_DEFAULT_TIMEFRAME=15m
```

## 主要目录

- `frontend`：Vue 3 工作台前端。
- `backend`：FastAPI 后端 API。
- `docs`：项目文档、接口说明、进度和发布说明。
- `okx-live-backtest-workbench`：当前项目维护 skill。
- `codex升级代码位置`：本地升级快照，仅作对照，不建议提交到 GitHub。
- `DP`：本地补丁/备份内容，仅作对照，不建议提交到 GitHub。

## 文档入口

- [项目文档首页](docs/index.md)
- [API 说明](docs/API.md)
- [项目进度](docs/PROJECT_STATUS.md)
- [后续路线图](docs/ROADMAP.md)
- [GitHub 发布说明](docs/GITHUB_PUBLISH.md)
- [升级记录](docs/CHANGELOG.md)

## 验证命令

```powershell
cd E:\codex版本实盘回测\frontend
npm run build
```

```powershell
cd E:\codex版本实盘回测
& 'C:/Users/SZC/PycharmProjects/pythonProject/.venv/Scripts/python.exe' -m py_compile `
  'backend/app/main.py' `
  'backend/app/routers/workbench.py' `
  'backend/app/routers/trading.py' `
  'backend/app/routers/strategies.py' `
  'backend/app/routers/market.py' `
  'backend/app/services/upstream.py' `
  'backend/app/config.py'
```
