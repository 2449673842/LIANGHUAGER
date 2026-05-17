---
name: okx-live-backtest-workbench
description: Build and maintain the Codex OKX live-trading, paper-trading, and backtest workbench in E:\codex版本实盘回测. Use when working on this project's Vue 3 frontend, FastAPI backend, OKX Agent CLI integration, layout constraints, migration boundaries, or project planning/status updates.
---

# OKX Live Backtest Workbench

## Overview

Use this skill when modifying the `E:\codex版本实盘回测` project. Keep product intent, data-source priority, page-shape rules, and migration boundaries consistent across turns.

## Core Rules

- Treat `E:\codex版本实盘回测` as the mainline project.
- Use `Vue 3 + Vite + Pinia` for the frontend and `FastAPI` for the backend.
- Keep the five top-level pages fixed:
  - `总览终端`
  - `策略中心`
  - `模拟/实盘`
  - `回测/调参`
  - `系统设置`
- Keep every main page visually compact. Avoid ultra-tall pages. Prefer panel-level scrolling over page-level sprawl.
- Keep data refresh frequent enough to feel live:
  - overview market data: very fast polling
  - execution state: fast polling
  - backtest data: slower polling
- Prefer official OKX Agent access over all other market/trading sources.

## Data Source Priority

Apply this priority order unless a user explicitly overrides it:

1. `OKX Agent CLI`
2. `OKX public REST`
3. `quant_platform` upstream
4. local fallback/mock data

Implementation notes:

- Use `okx.cmd` by absolute path from the backend when calling the official CLI on Windows.
- Normalize instrument IDs to `BTC-USDT` style before backend requests.
- Surface the active data source in the UI so the user can tell whether a panel is live or in fallback mode.

## Migration Boundaries

Reuse these sources, but do not let them redefine the new project structure:

- Backend/business source:
  - `E:\pycelve\autojy\实时盯盘回测\quant_platform`
- Terminal content source:
  - `E:\Projects\trading-dashboard`

Rules:

- Reuse business logic and data contracts where practical.
- Rebuild the UI shell for the new workbench instead of copying old screens wholesale.
- Keep layout decisions aligned with the new workbench, not the legacy page shapes.

## Product Requirements

- Support crypto first.
- Support OKX spot and perpetual swap first.
- Support multi-account structure.
- Support multi-symbol and multi-strategy execution.
- Support paper and live modes.
- Default live execution to manual confirmation, but preserve an automatic execution path.
- Preserve room for TradingView-style signal/notification flows.
- Support SMTP email and Enterprise WeCom webhook notification paths.

## Layout Rules

- Keep panel heights bounded.
- Use chart-centered work areas with side panels for watchlists, queues, diagnostics, and controls.
- Keep K-line, orderbook, control panel, queues, and stats visible without excessive vertical scrolling.
- Use compact stat tiles and panel-internal scroll containers for long tables/lists.
- Keep page headers short and consistent.

## Current Status

- Independent project scaffold exists in `E:\codex版本实盘回测`.
- Frontend workbench shell is live on `http://127.0.0.1:9502`.
- Backend API is live on `http://127.0.0.1:8100`.
- Official OKX CLI is installed and working locally.
- Real-time overview market snapshot is already coming from `okx-cli`.
- Real-time orderbook is already coming from `okx-cli`.
- Candle data path prefers `okx-cli`, then REST, then upstream, then fallback.
- Overview and execution pages poll automatically.
- Page length has been tightened by limiting panel heights and using internal scrolling.

## Next Work

Implement these slices next:

1. Replace more execution-page placeholders with real account/session/confirmation data.
2. Bind more backtest detail fields from `quant_platform` into the new backtest workbench.
3. Add explicit user-triggered refresh controls that coexist with automatic polling.
4. Start wiring OKX live-account and confirmation operations behind backend-safe endpoints.
5. Reduce remaining static copy in strategy and execution panels.

## Response and Status Discipline

- Report progress in short, concrete increments.
- State what changed, what was verified, and what remains.
- Mention when a page is using `okx-cli`, public REST, upstream, or fallback.
- Call out validation results after meaningful changes:
  - backend syntax check
  - frontend build
  - endpoint probe
  - preview availability
