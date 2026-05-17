# Codex 版本实盘回测文档

这是 `E:\codex版本实盘回测` 的项目文档首页，适合直接放到 GitHub 仓库的 `docs` 目录，也可以作为 GitHub Pages 的文档源。

## 项目定位

本项目是一个 OKX 优先的实盘、模拟盘、回测和策略管理工作台。

核心目标：

- 保留旧 `quant_platform` 中已经跑通的后端逻辑。
- 复刻并重构 `trading-dashboard` 中可用的 K 线、模拟盘和实盘功能。
- 使用新的 Vue 3 工作台布局，避免旧前端错位和页面过长问题。
- 让真实行情、盘口、自选、执行队列和策略回测逐步替换占位数据。

## 当前能力

- OKX K 线数据路径：CLI 优先，REST 兜底，再 fallback。
- OKX 行情快照和盘口：CLI/REST 优先。
- 总览终端：行情脉冲、自选列表、盘口、持仓摘要、监控开关。
- 模拟/实盘：账户列表、运行会话、执行队列、待确认任务。
- 回测/调参：指标卡片、资金曲线、交易记录、周期运行。
- 策略中心：策略列表、策略导入。
- 通用模态框：支持字段、下拉、搜索建议、提示文字和自定义 slot。

## 文档目录

- [架构说明](architecture.md)
- [API 说明](API.md)
- [项目进度](PROJECT_STATUS.md)
- [路线图](ROADMAP.md)
- [GitHub 发布说明](GITHUB_PUBLISH.md)
- [升级记录](CHANGELOG.md)

## 本地运行

后端：

```powershell
cd E:\codex版本实盘回测\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8100
```

前端：

```powershell
cd E:\codex版本实盘回测\frontend
npm run dev -- --host 0.0.0.0 --port 9502
```

访问：`http://127.0.0.1:9502`
