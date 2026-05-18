from datetime import datetime

from fastapi import APIRouter, Body, Query

from app.config import settings
from app.schemas.common import ApiEnvelope
from app.services.mock_data import BACKTEST, OVERVIEW
from app.services.state_store import WORKBENCH_STATE_PATH, load_json_state, save_json_state
from app.services.upstream import fetch_okx_market_snapshot, fetch_strategy_runs, fetch_view

router = APIRouter(prefix="/api", tags=["workbench"])

DEFAULT_WATCHLIST = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "DOGE-USDT"]
_workbench_state = load_json_state(
    WORKBENCH_STATE_PATH,
    {
        "watchlist_symbols": [],
        "hidden_watchlist_symbols": [],
        "monitoring_running": True,
    },
)
watchlist_symbols: list[str] = [
    str(symbol).replace("/", "-").upper()
    for symbol in _workbench_state.get("watchlist_symbols", [])
    if str(symbol).strip()
]
hidden_watchlist_symbols: set[str] = {
    str(symbol).replace("/", "-").upper()
    for symbol in _workbench_state.get("hidden_watchlist_symbols", [])
    if str(symbol).strip()
}
monitoring_running: bool = bool(_workbench_state.get("monitoring_running", True))


def persist_workbench_state() -> None:
    save_json_state(
        WORKBENCH_STATE_PATH,
        {
            "watchlist_symbols": watchlist_symbols,
            "hidden_watchlist_symbols": sorted(hidden_watchlist_symbols),
            "monitoring_running": monitoring_running,
        },
    )


def get_effective_watchlist() -> list[str]:
    symbols: list[str] = []
    for symbol in [*DEFAULT_WATCHLIST, *watchlist_symbols]:
        normalized = symbol.replace("/", "-").upper()
        if normalized not in hidden_watchlist_symbols and normalized not in symbols:
            symbols.append(normalized)
    return symbols


@router.get("/workbench/overview", response_model=ApiEnvelope[dict])
def get_overview(
    instrument_id: str = Query(default=settings.default_instrument_id),
) -> ApiEnvelope[dict]:
    # When a custom watchlist has been set via the `/watchlist` endpoints, pass
    # it through to the market snapshot service so the watchlist data reflects
    # user preferences.  Otherwise allow the service to use its default symbols.
    runtime_result = fetch_view("execution-runtime-console", limit=8, timeout=0.25)
    # Make a copy of the global watchlist to avoid mutation during the fetch
    current_watchlist = get_effective_watchlist()
    market_result = fetch_okx_market_snapshot(
        inst_id=instrument_id,
        watchlist=current_watchlist,
    )
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
    ctrl["lastSync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload["controlState"] = ctrl
    return ApiEnvelope(data=payload)


@router.get("/watchlist", response_model=ApiEnvelope[list[str]])
def get_watchlist() -> ApiEnvelope[list[str]]:
    """Return the current watchlist symbols.

    The watchlist is a simple list of instrument identifiers (e.g. "BTC-USDT").
    When empty, the market snapshot service falls back to its default symbols.
    """
    return ApiEnvelope(data=get_effective_watchlist())


@router.post("/watchlist", response_model=ApiEnvelope[list[str]])
def add_watchlist(symbol: str = Body(..., embed=True)) -> ApiEnvelope[list[str]]:
    """Add a symbol to the watchlist.

    The symbol must be provided in the request body as JSON: `{ "symbol": "ETH-USDT" }`.
    Symbols are normalized to uppercase with hyphens.  Duplicates are ignored.
    Returns the updated watchlist.
    """
    normalized = symbol.replace("/", "-").upper()
    hidden_watchlist_symbols.discard(normalized)
    if normalized not in DEFAULT_WATCHLIST and normalized not in watchlist_symbols:
        watchlist_symbols.append(normalized)
    persist_workbench_state()
    return ApiEnvelope(data=get_effective_watchlist())


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
    if normalized in DEFAULT_WATCHLIST:
        hidden_watchlist_symbols.add(normalized)
    persist_workbench_state()
    return ApiEnvelope(data=get_effective_watchlist())


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
        persist_workbench_state()
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

    Expects a JSON payload with at least a `period` field (e.g. "1M", "3M", "6M", "1Y").
    Additional fields `capital` scale the metrics proportionally (default 10000).
    The implementation produces a synthetic result by scaling fallback metrics
    and equity curve based on period and capital.  A real integration would call
    into quant_platform or another backtesting engine.
    """
    from copy import deepcopy

    period = (params.get("period") or "1M").upper()
    factor_map = {"1M": 1.0, "3M": 1.2, "6M": 1.5, "1Y": 1.8}
    period_factor = factor_map.get(period, 1.0)
    capital_str = params.get("capital") or "10000"
    try:
        capital_value = float(capital_str)
        capital_factor = capital_value / 10000.0 if capital_value > 0 else 1.0
    except Exception:
        capital_factor = 1.0
    factor = period_factor * capital_factor
    # Make a deep copy so we don't mutate the global BACKTEST constant
    payload = deepcopy(BACKTEST)
    # Scale metrics: first metric is net profit, second is max drawdown
    try:
        net_str = payload["metrics"][0]["value"].strip('%').replace('+', '').replace('-', '')
        net_value = float(net_str) * factor
        sign = '+' if net_value >= 0 else '-'
        payload["metrics"][0]["value"] = f"{sign}{abs(net_value):.2f}%"
        draw_str = payload["metrics"][1]["value"].strip('%').replace('+', '').replace('-', '')
        draw_value = float(draw_str) * factor
        payload["metrics"][1]["value"] = f"-{abs(draw_value):.2f}%"
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


# ---------------------------------------------------------------------------
# Backtest templates and archives
#
# Lightweight in-memory stores for saving backtest parameter templates and
# archiving backtest results.  These lists are process‑scoped and will be
# lost on restart.  A future version should persist them.
# ---------------------------------------------------------------------------

backtest_templates: list[dict] = []
backtest_archives: list[dict] = []


@router.get("/backtests/templates", response_model=ApiEnvelope[list[dict]])
def get_backtest_templates() -> ApiEnvelope[list[dict]]:
    """Return all saved backtest parameter templates."""
    return ApiEnvelope(data=list(backtest_templates))


@router.post("/backtests/templates", response_model=ApiEnvelope[list[dict]])
def save_backtest_template(template: dict = Body(...)) -> ApiEnvelope[list[dict]]:
    """Save a new backtest parameter template.

    The request body should be a JSON object with at least a `name` and a
    `params` object.  Returns the updated template list.
    """
    name = template.get("name")
    params_dict = template.get("params")
    if name and isinstance(params_dict, dict):
        backtest_templates.append({"name": name, "params": params_dict})
    return ApiEnvelope(data=list(backtest_templates))


@router.get("/backtests/archives", response_model=ApiEnvelope[list[dict]])
def get_backtest_archives() -> ApiEnvelope[list[dict]]:
    """Return all archived backtest results."""
    return ApiEnvelope(data=list(backtest_archives))


@router.post("/backtests/archives", response_model=ApiEnvelope[list[dict]])
def save_backtest_archive(record: dict = Body(...)) -> ApiEnvelope[list[dict]]:
    """Save a backtest result to the archive.

    The request body should include a `name`, a `params` dict, and a
    `result` dict.  A timestamp is automatically added on save.
    """
    from datetime import datetime

    name = record.get("name")
    params_dict = record.get("params")
    result_dict = record.get("result")
    if name and isinstance(params_dict, dict) and isinstance(result_dict, dict):
        backtest_archives.append(
            {
                "name": name,
                "params": params_dict,
                "result": result_dict,
                "time": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
        )
    return ApiEnvelope(data=list(backtest_archives))
