from fastapi import APIRouter, Body

from app.schemas.common import ApiEnvelope
from app.services.mock_data import BACKTEST, OVERVIEW
from app.services.upstream import fetch_okx_market_snapshot, fetch_strategy_runs, fetch_view

router = APIRouter(prefix="/api", tags=["workbench"])

# In-memory state for the current watchlist symbols and monitoring status.  The
# watchlist stores additional instruments the user has added on the overview
# page.  Monitoring state reflects whether the high‑frequency polling loop on
# the frontend should be considered active.  Persisting these values in
# memory keeps the API stateless with respect to external systems and avoids
# writing to disk.  If a future version requires persistence across restarts,
# these values can be loaded from and saved to a database or config file.
watchlist_symbols: list[str] = []  # default empty watchlist uses service default list
monitoring_running: bool = False


@router.get("/workbench/overview", response_model=ApiEnvelope[dict])
def get_overview() -> ApiEnvelope[dict]:
    # When a custom watchlist has been set via the `/watchlist` endpoints, pass
    # it through to the market snapshot service so the watchlist data reflects
    # user preferences.  Otherwise allow the service to use its default symbols.
    runtime_result = fetch_view("execution-runtime-console", limit=8)
    # Make a copy of the global watchlist to avoid mutation during the fetch
    current_watchlist = list(watchlist_symbols)
    market_result = fetch_okx_market_snapshot(watchlist=current_watchlist if current_watchlist else None)
    payload = dict(OVERVIEW)
    payload["source"] = runtime_result.source if runtime_result.connected else market_result["source"]
    payload["upstreamConnected"] = runtime_result.connected or market_result["connected"]
    if runtime_result.connected and isinstance(runtime_result.data, dict):
        active_tasks = runtime_result.data.get("active_tasks") or []
        session_summary = runtime_result.data.get("session_summary") or {}
        if active_tasks:
            payload["activity"] = [
                {
                    "time": str(item.get("updated_at") or item.get("started_at") or "--")[-8:],
                    "message": item.get("task_name") or item.get("title") or "运行任务",
                    "tone": "neutral",
                }
                for item in active_tasks[:4]
            ]
        if session_summary:
            payload["marketPulse"] = list(payload["marketPulse"])
            payload["marketPulse"][2] = {
                "label": "活跃策略",
                "value": str(session_summary.get("active_sessions") or session_summary.get("running") or "0"),
                "tone": "neutral",
            }
    if market_result["marketPulse"]:
        payload["marketPulse"] = market_result["marketPulse"]
    if market_result["watchlist"]:
        payload["watchlist"] = market_result["watchlist"]
    if market_result["orderbook"]:
        payload["orderbook"] = market_result["orderbook"]

    # Reflect the current monitoring state in the control panel so the frontend
    # can display "监控运行中" or "监控已停止" accordingly.  Only update when
    # payload already has a controlState object (from the fallback data).  If
    # controlState is missing, create a minimal version.
    ctrl = payload.get("controlState") or {}
    ctrl["running"] = monitoring_running
    payload["controlState"] = ctrl
    return ApiEnvelope(data=payload)


@router.get("/watchlist", response_model=ApiEnvelope[list[str]])
def get_watchlist() -> ApiEnvelope[list[str]]:
    """Return the current watchlist symbols.

    The watchlist is a simple list of instrument identifiers (e.g. "BTC-USDT").
    When empty, the market snapshot service falls back to its default symbols.
    """
    return ApiEnvelope(data=list(watchlist_symbols))


@router.post("/watchlist", response_model=ApiEnvelope[list[str]])
def add_watchlist(symbol: str = Body(..., embed=True)) -> ApiEnvelope[list[str]]:
    """Add a symbol to the watchlist.

    The symbol must be provided in the request body as JSON: `{ "symbol": "ETH-USDT" }`.
    Symbols are normalized to uppercase with hyphens.  Duplicates are ignored.
    Returns the updated watchlist.
    """
    normalized = symbol.replace("/", "-").upper()
    if normalized not in watchlist_symbols:
        watchlist_symbols.append(normalized)
    return ApiEnvelope(data=list(watchlist_symbols))


@router.delete("/watchlist", response_model=ApiEnvelope[list[str]])
def remove_watchlist(symbol: str) -> ApiEnvelope[list[str]]:
    """Remove a symbol from the watchlist via query parameter.

    To remove a symbol, call `/watchlist?symbol=BTC-USDT`.  If the symbol does
    not exist in the watchlist, the call is a no‑op.  Returns the updated
    watchlist.
    """
    normalized = symbol.replace("/", "-").upper()
    try:
        watchlist_symbols.remove(normalized)
    except ValueError:
        pass
    return ApiEnvelope(data=list(watchlist_symbols))


@router.get("/monitoring/state", response_model=ApiEnvelope[dict])
def get_monitoring_state() -> ApiEnvelope[dict]:
    """Return the current monitoring state as a dict with a boolean `running` key."""
    return ApiEnvelope(data={"running": monitoring_running})


@router.post("/monitoring/state", response_model=ApiEnvelope[dict])
def set_monitoring_state(state: dict = Body(...)) -> ApiEnvelope[dict]:
    """Set the monitoring state.

    Accepts JSON body `{ "running": true }` or `{ "running": false }` and
    updates the global flag accordingly.  Returns the updated state.
    """
    global monitoring_running
    running = state.get("running")
    if isinstance(running, bool):
        monitoring_running = running
    return ApiEnvelope(data={"running": monitoring_running})


@router.get("/backtests/workbench", response_model=ApiEnvelope[dict])
def get_backtest_workbench() -> ApiEnvelope[dict]:
    result = fetch_strategy_runs(limit=8)
    payload = dict(BACKTEST)
    payload["source"] = result.source
    payload["upstreamConnected"] = result.connected
    if result.connected and isinstance(result.data, dict):
        rows = result.data.get("rows") or result.data.get("items") or []
        if rows:
            mapped = []
            for row in rows[:4]:
                metrics = row.get("metrics") or {}
                pnl = metrics.get("net_profit_pct") or metrics.get("return_pct") or metrics.get("pnl_pct")
                drawdown = metrics.get("max_drawdown_pct") or metrics.get("max_drawdown")
                sharpe = metrics.get("sharpe")
                win_rate = metrics.get("win_rate")
                payload["metrics"] = [
                    {"label": "净收益", "value": f"{float(pnl):+.2f}%" if pnl is not None else payload["metrics"][0]["value"], "tone": "up" if float(pnl or 0) >= 0 else "down"},
                    {"label": "最大回撤", "value": f"{float(drawdown):+.2f}%" if drawdown is not None else payload["metrics"][1]["value"], "tone": "down"},
                    {"label": "Sharpe", "value": f"{float(sharpe):.2f}" if sharpe is not None else payload["metrics"][2]["value"], "tone": "up"},
                    {"label": "胜率", "value": f"{float(win_rate):.2f}%" if win_rate is not None else payload["metrics"][3]["value"], "tone": "neutral"},
                ]
                mapped.append(
                    {
                        "time": str(row.get("created_at") or row.get("run_id") or "--"),
                        "side": row.get("status") or "回测",
                        "price": row.get("version_id") or row.get("strategy_id") or "--",
                        "reason": row.get("run_name") or row.get("label") or "策略运行",
                    }
                )
            if mapped:
                payload["trades"] = mapped
    return ApiEnvelope(data=payload)


@router.post("/backtests/run", response_model=ApiEnvelope[dict])
def run_backtest(params: dict = Body(...)) -> ApiEnvelope[dict]:
    """Run a backtest with custom parameters.

    Expects a JSON payload with at least a `period` field (e.g. "1M", "3M", "6M", "1Y").  Other
    fields like `direction`, `capital`, `leverage`, etc., are accepted but ignored for now.
    The implementation here produces a synthetic backtest result by scaling the fallback
    metrics and equity curve based on the period.  A real integration would call into
    quant_platform or another backtesting engine.
    """
    from copy import deepcopy

    period = params.get("period") or "1M"
    factor_map = {"1M": 1.0, "3M": 1.2, "6M": 1.5, "1Y": 1.8}
    factor = factor_map.get(period, 1.0)
    # Make a deep copy so we don't mutate the global BACKTEST constant
    payload = deepcopy(BACKTEST)
    # Scale metrics: assume the first metric is net profit and second is max drawdown
    try:
        net_str = payload["metrics"][0]["value"].strip('%').replace('+', '').replace('-', '')
        net_value = float(net_str) * factor
        sign = '+' if net_value >= 0 else '-'
        payload["metrics"][0]["value"] = f"{sign}{abs(net_value):.2f}%"
        draw_str = payload["metrics"][1]["value"].strip('%').replace('+', '').replace('-', '')
        draw_value = float(draw_str) * factor
        payload["metrics"][1]["value"] = f"-{draw_value:.2f}%"
    except Exception:
        pass
    # Scale equity curve values
    try:
        base = payload["equityCurve"][0]["value"] if payload["equityCurve"] else 10000
        scaled = []
        for point in payload["equityCurve"]:
            delta = point["value"] - base
            new_value = base + delta * factor
            scaled.append({"time": point["time"], "value": round(new_value, 2)})
        payload["equityCurve"] = scaled
    except Exception:
        pass
    payload["source"] = "local"
    payload["upstreamConnected"] = False
    return ApiEnvelope(data=payload)
