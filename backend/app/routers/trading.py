from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body

from app.schemas.common import ApiEnvelope
from app.services.execution import execute_queue_task
from app.services.mock_data import EXECUTION
from app.services.state_store import EXECUTION_STATE_PATH, load_json_state, save_json_state
from app.services.upstream import fetch_execution_runtime, fetch_paper_strategies

router = APIRouter(prefix="/api", tags=["trading"])

# In-memory execution state. This keeps the current workbench interactive while
# avoiding a persistence migration in this slice. The next persistence slice can
# move these structures to SQLite/JSON storage without changing the API shapes.
_saved_state = load_json_state(EXECUTION_STATE_PATH, {})
execution_accounts: list[dict[str, Any]] = list(_saved_state.get("accounts") or EXECUTION["accounts"])
execution_sessions: list[dict[str, Any]] = list(_saved_state.get("sessions") or EXECUTION["sessions"])
execution_mode: str = _saved_state.get("executionMode") or EXECUTION.get("controlState", {}).get("executionMode", "人工确认")  # type: ignore[arg-type]
_queue_id_counter = 1


def _seed_queue() -> list[dict[str, Any]]:
    global _queue_id_counter
    rows: list[dict[str, Any]] = []
    for item in EXECUTION.get("queues", []):
        row = dict(item)
        row["id"] = _queue_id_counter
        row.setdefault("executionResult", None)
        _queue_id_counter += 1
        rows.append(row)
    return rows


execution_queues: list[dict[str, Any]] = list(_saved_state.get("queues") or _seed_queue())
execution_events: list[dict[str, Any]] = list(_saved_state.get("events") or [])
if execution_queues:
    _queue_id_counter = max(int(item.get("id") or 0) for item in execution_queues) + 1


def _persist_execution_state() -> None:
    save_json_state(
        EXECUTION_STATE_PATH,
        {
            "accounts": execution_accounts,
            "sessions": execution_sessions,
            "queues": execution_queues,
            "events": execution_events,
            "executionMode": execution_mode,
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
        },
    )


def _now_text() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _add_event(message: str, tone: str = "neutral") -> None:
    execution_events.insert(0, {"time": _now_text(), "message": message, "tone": tone})
    del execution_events[20:]
    _persist_execution_state()


def _next_queue_id() -> int:
    global _queue_id_counter
    item_id = _queue_id_counter
    _queue_id_counter += 1
    return item_id


def _find_queue(item_id: int) -> dict[str, Any] | None:
    return next((item for item in execution_queues if item.get("id") == item_id), None)


def _execute_and_update(item: dict[str, Any], trigger: str) -> dict[str, Any]:
    result = execute_queue_task(item, mode=execution_mode)
    item["executionResult"] = result
    item["state"] = "已发送" if result.get("ok") else "执行失败"
    item["lastExecutedAt"] = result.get("submittedAt")
    tone = "up" if result.get("ok") else "down"
    dry = " dry-run" if result.get("dryRun") else ""
    _add_event(f"{item.get('strategy')} {item.get('symbol')} {trigger}{dry}: {result.get('message')}", tone)
    _persist_execution_state()
    return result


@router.get("/execution/state", response_model=ApiEnvelope[dict])
def get_execution_state() -> ApiEnvelope[dict]:
    result = fetch_paper_strategies(limit=8)
    runtime_result = fetch_execution_runtime(limit=8)
    payload = dict(EXECUTION)
    payload["accounts"] = list(execution_accounts)
    payload["queues"] = list(execution_queues)
    payload["executionMode"] = execution_mode
    payload["events"] = list(execution_events)
    payload["source"] = result.source
    payload["upstreamConnected"] = result.connected

    if result.connected and isinstance(result.data, dict):
        items = result.data.get("items") or result.data.get("rows") or result.data.get("records") or []
        if items:
            payload["sessions"] = [
                {
                    "name": item.get("paper_strategy_id") or item.get("session_id") or "paper-session",
                    "strategy": item.get("strategy_id") or item.get("version_id") or "unknown-strategy",
                    "symbol": item.get("instrument_id") or item.get("symbol") or "BTC-USDT",
                    "mode": item.get("mode") or "模拟",
                    "state": item.get("status") or item.get("state") or "运行中",
                }
                for item in items[:6]
            ]
        else:
            payload["sessions"] = list(execution_sessions)
    else:
        payload["sessions"] = list(execution_sessions)

    if runtime_result.connected and isinstance(runtime_result.data, dict):
        tasks = runtime_result.data.get("active_tasks") or []
        session_summary = runtime_result.data.get("session_summary") or {}
        payload["runtime"] = {
            "activeTasks": len(tasks) or session_summary.get("active_tasks") or payload["runtime"]["activeTasks"],
            "activeSessions": session_summary.get("active_sessions") or session_summary.get("running") or payload["runtime"]["activeSessions"],
            "pendingConfirmations": session_summary.get("pending_confirmations") or len([q for q in execution_queues if q.get("state") == "待确认"]),
            "notificationsSent": session_summary.get("notifications_sent") or payload["runtime"]["notificationsSent"],
        }
    else:
        payload["runtime"] = dict(payload["runtime"])
        payload["runtime"]["pendingConfirmations"] = len([q for q in execution_queues if q.get("state") == "待确认"])
        payload["runtime"]["activeTasks"] = len([q for q in execution_queues if q.get("state") in ("运行中", "已发送")])
    return ApiEnvelope(data=payload)


@router.get("/execution/accounts", response_model=ApiEnvelope[list[dict]])
def get_accounts() -> ApiEnvelope[list[dict]]:
    return ApiEnvelope(data=list(execution_accounts))


@router.post("/execution/accounts", response_model=ApiEnvelope[list[dict]])
def add_account(account: dict = Body(...)) -> ApiEnvelope[list[dict]]:
    name = account.get("name") or f"Account-{len(execution_accounts)+1}"
    venue = account.get("venue") or "OKX"
    equity = account.get("equity") or "0"
    status = account.get("status") or "待确认"
    execution_accounts.append({"name": name, "venue": venue, "equity": equity, "status": status})
    _add_event(f"新增账户 {name}")
    _persist_execution_state()
    return ApiEnvelope(data=list(execution_accounts))


@router.get("/execution/queues", response_model=ApiEnvelope[list[dict]])
def get_queues() -> ApiEnvelope[list[dict]]:
    return ApiEnvelope(data=list(execution_queues))


@router.post("/execution/queues", response_model=ApiEnvelope[list[dict]])
def add_queue(item: dict = Body(...)) -> ApiEnvelope[list[dict]]:
    queue_item: dict[str, Any] = {
        "id": _next_queue_id(),
        "time": _now_text(),
        "strategy": item.get("strategy") or "unknown",
        "symbol": item.get("symbol") or "--",
        "action": item.get("action") or "--",
        "reason": item.get("reason") or "--",
        "size": item.get("size") or item.get("sz"),
        "tradeMode": item.get("tradeMode"),
        "state": "待确认",
        "executionResult": None,
    }
    execution_queues.insert(0, queue_item)
    _add_event(f"新增执行任务 {queue_item['strategy']} {queue_item['symbol']}")

    if execution_mode == "自动执行":
        queue_item["state"] = "运行中"
        _execute_and_update(queue_item, "自动执行")

    _persist_execution_state()
    return ApiEnvelope(data=list(execution_queues))


@router.post("/execution/queues/{item_id}/confirm", response_model=ApiEnvelope[dict])
def confirm_queue(item_id: int) -> ApiEnvelope[dict]:
    item = _find_queue(item_id)
    if not item:
        return ApiEnvelope(data={"ok": False, "message": "queue item not found", "queues": list(execution_queues)})
    item["state"] = "运行中"
    result = _execute_and_update(item, "人工确认")
    _persist_execution_state()
    return ApiEnvelope(data={"ok": result.get("ok", False), "result": result, "queues": list(execution_queues)})


@router.post("/execution/queues/{item_id}/reject", response_model=ApiEnvelope[dict])
def reject_queue(item_id: int) -> ApiEnvelope[dict]:
    item = _find_queue(item_id)
    if item:
        item["state"] = "已拒绝"
        _add_event(f"拒绝任务 {item.get('strategy')} {item.get('symbol')}", "down")
        _persist_execution_state()
    return ApiEnvelope(data={"ok": item is not None, "queues": list(execution_queues)})


@router.get("/execution/mode", response_model=ApiEnvelope[dict])
def get_execution_mode() -> ApiEnvelope[dict]:
    return ApiEnvelope(data={"mode": execution_mode})


@router.post("/execution/mode", response_model=ApiEnvelope[dict])
def set_execution_mode(payload: dict = Body(...)) -> ApiEnvelope[dict]:
    global execution_mode
    mode = payload.get("mode")
    if mode not in ("人工确认", "自动执行"):
        return ApiEnvelope(data={"mode": execution_mode, "ok": False, "message": "mode must be 人工确认 or 自动执行"})
    execution_mode = mode
    _add_event(f"执行模式切换为 {mode}")
    _persist_execution_state()
    return ApiEnvelope(data={"mode": execution_mode, "ok": True})


@router.post("/execution/queues/{item_id}/retry", response_model=ApiEnvelope[dict])
def retry_queue(item_id: int) -> ApiEnvelope[dict]:
    item = _find_queue(item_id)
    if not item:
        return ApiEnvelope(data={"ok": False, "message": "queue item not found", "queues": list(execution_queues)})
    item["state"] = "运行中"
    result = _execute_and_update(item, "重新执行")
    _persist_execution_state()
    return ApiEnvelope(data={"ok": result.get("ok", False), "result": result, "queues": list(execution_queues)})
