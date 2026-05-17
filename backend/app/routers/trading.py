from fastapi import APIRouter, Body

from app.schemas.common import ApiEnvelope
from app.services.mock_data import EXECUTION
from app.services.upstream import fetch_execution_runtime, fetch_paper_strategies

router = APIRouter(prefix="/api", tags=["trading"])

# In-memory execution data.  These lists hold accounts, sessions and queue
# items created by the user via the API.  They are initialised with the
# fallback data from EXECUTION so that the UI has something to display
# before any real data arrives.  A future integration could persist these
# lists or replace them with real OKX account/session state.
execution_accounts: list[dict] = list(EXECUTION["accounts"])
execution_sessions: list[dict] = list(EXECUTION["sessions"])
execution_queues: list[dict] = list(EXECUTION["queues"])


@router.get("/execution/state", response_model=ApiEnvelope[dict])
def get_execution_state() -> ApiEnvelope[dict]:
    # Start with the fallback payload and overlay any user-added accounts and queues.
    result = fetch_paper_strategies(limit=8)
    runtime_result = fetch_execution_runtime(limit=8)
    payload = dict(EXECUTION)
    # Always use the in-memory accounts and queues lists.  Sessions are
    # preserved from fallback for now; they could be loaded from upstream.
    payload["accounts"] = list(execution_accounts)
    payload["queues"] = list(execution_queues)
    # Source and connectivity reflect upstream availability for session and runtime data
    payload["source"] = result.source
    payload["upstreamConnected"] = result.connected
    # When upstream provides session data, map it into the sessions list
    if result.connected and isinstance(result.data, dict):
        items = result.data.get("items") or result.data.get("rows") or result.data.get("records") or []
        if items:
            mapped: list[dict] = []
            for item in items[:6]:
                mapped.append(
                    {
                        "name": item.get("paper_strategy_id") or item.get("session_id") or "paper-session",
                        "strategy": item.get("strategy_id") or item.get("version_id") or "unknown-strategy",
                        "symbol": item.get("instrument_id") or item.get("symbol") or "BTC-USDT",
                        "mode": item.get("mode") or "模拟",
                        "state": item.get("status") or item.get("state") or "运行中",
                    }
                )
            payload["sessions"] = mapped
    else:
        # Use the in-memory sessions when upstream is not connected
        payload["sessions"] = list(execution_sessions)
    # Overlay runtime metrics with upstream data when available
    if runtime_result.connected and isinstance(runtime_result.data, dict):
        tasks = runtime_result.data.get("active_tasks") or []
        session_summary = runtime_result.data.get("session_summary") or {}
        payload["runtime"] = {
            "activeTasks": len(tasks) or session_summary.get("active_tasks") or payload["runtime"]["activeTasks"],
            "activeSessions": session_summary.get("active_sessions") or session_summary.get("running") or payload["runtime"]["activeSessions"],
            "pendingConfirmations": session_summary.get("pending_confirmations") or payload["runtime"]["pendingConfirmations"],
            "notificationsSent": session_summary.get("notifications_sent") or payload["runtime"]["notificationsSent"],
        }
        if tasks:
            payload["queues"] = [
                {
                    "time": str(item.get("updated_at") or item.get("started_at") or "--")[-8:],
                    "strategy": item.get("task_name") or item.get("title") or "运行任务",
                    "symbol": item.get("instrument_id") or item.get("symbol") or "--",
                    "action": item.get("action") or "处理",
                    "reason": item.get("reason") or item.get("status") or "执行队列",
                    "state": item.get("status") or "运行中",
                }
                for item in tasks[:6]
            ]
    return ApiEnvelope(data=payload)


@router.get("/execution/accounts", response_model=ApiEnvelope[list[dict]])
def get_accounts() -> ApiEnvelope[list[dict]]:
    """Return the current account list."""
    return ApiEnvelope(data=list(execution_accounts))


@router.post("/execution/accounts", response_model=ApiEnvelope[list[dict]])
def add_account(account: dict = Body(...)) -> ApiEnvelope[list[dict]]:
    """Add a new account.

    Expects a JSON body with keys `name`, `venue`, `equity`, `status`.  Missing
    keys will be filled with sensible defaults.  Returns the updated accounts
    list.
    """
    name = account.get("name") or f"Account-{len(execution_accounts)+1}"
    venue = account.get("venue") or "OKX"
    equity = account.get("equity") or "0"
    status = account.get("status") or "待确认"
    execution_accounts.append({"name": name, "venue": venue, "equity": equity, "status": status})
    return ApiEnvelope(data=list(execution_accounts))


@router.get("/execution/queues", response_model=ApiEnvelope[list[dict]])
def get_queues() -> ApiEnvelope[list[dict]]:
    """Return the current execution queue."""
    return ApiEnvelope(data=list(execution_queues))


@router.post("/execution/queues", response_model=ApiEnvelope[list[dict]])
def add_queue(item: dict = Body(...)) -> ApiEnvelope[list[dict]]:
    """Add a new queue task.

    Expects JSON with keys `strategy`, `symbol`, `action`, `reason`.  Missing
    fields are defaulted.  The state is initialised to "待确认" and the
    current time string is used.
    """
    from datetime import datetime

    strategy = item.get("strategy") or "unknown"
    symbol = item.get("symbol") or "--"
    action = item.get("action") or "--"
    reason = item.get("reason") or "--"
    now = datetime.now().strftime("%H:%M:%S")
    execution_queues.insert(0, {
        "time": now,
        "strategy": strategy,
        "symbol": symbol,
        "action": action,
        "reason": reason,
        "state": "待确认",
    })
    return ApiEnvelope(data=list(execution_queues))
