from fastapi import APIRouter, Query

from app.schemas.common import ApiEnvelope
from app.services.mock_data import STRATEGIES
from app.services.upstream import fetch_upstream

router = APIRouter(prefix="/api", tags=["strategies"])

# In-memory strategy list seeded from fallback STRATEGIES.  Users can import
# new strategies via the API which will be added to this list.  A real
# implementation would persist strategies in a database or query them
# dynamically from quant_platform.
strategy_items: list[dict] = list(STRATEGIES["items"])


@router.get("/strategies/board", response_model=ApiEnvelope[dict])
def get_strategies_board(limit: int = Query(default=12, ge=1, le=50)) -> ApiEnvelope[dict]:
    result = fetch_upstream("/platform/strategies/versions", {"limit": limit})
    payload = dict(STRATEGIES)
    payload["source"] = result.source
    payload["upstreamConnected"] = result.connected
    # Always start with the in-memory strategy list.  When upstream is
    # connected, map its data into items and append or override local list.
    items = list(strategy_items)
    if result.connected:
        rows = result.data if isinstance(result.data, list) else result.data.get("items") or result.data.get("rows") or []
        mapped = []
        for row in rows[:limit]:
            mapped.append(
                {
                    "strategyId": row.get("strategy_id") or row.get("strategyId") or "unknown-strategy",
                    "versionId": row.get("version_id") or row.get("versionId") or "unknown-version",
                    "label": row.get("version_name") or row.get("strategy_name") or row.get("strategy_id") or "未命名策略",
                    "instrumentId": row.get("instrument_id") or row.get("instrumentId") or "--",
                    "timeframe": row.get("timeframe") or "--",
                    "status": row.get("status") or row.get("governance_status") or "已导入",
                    "updatedAt": str(row.get("updated_at") or row.get("created_at") or "--"),
                }
            )
        # Extend or override local items with upstream items (simple union)
        items = mapped + [item for item in items if item["versionId"] not in {m["versionId"] for m in mapped}]
    payload["items"] = items[:limit]
    return ApiEnvelope(data=payload)


@router.post("/strategies/import", response_model=ApiEnvelope[list[dict]])
def import_strategy(
    label: str = Query(None),
    instrumentId: str = Query(None),
    timeframe: str = Query(None),
) -> ApiEnvelope[list[dict]]:
    """Import a new strategy.

    Expects query parameters (for simplicity) or JSON body with at least a `label` field
    and optionally `instrumentId` and `timeframe`.  Generates a new strategyId
    and versionId, sets status to "已导入" and updatedAt to now, and appends the
    new entry to the in-memory list.  Returns the updated strategy list.
    """
    from datetime import datetime
    # 直接使用命名查询参数
    if not label:
        label = f"新策略-{len(strategy_items)+1}"
    strategy_id = label.replace(' ', '_').lower()
    version_id = f"{strategy_id}:v1.0.0"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_item = {
        "strategyId": strategy_id,
        "versionId": version_id,
        "label": label,
        "instrumentId": instrumentId or "--",
        "timeframe": timeframe or "15m",
        "status": "已导入",
        "updatedAt": now_str,
    }
    strategy_items.insert(0, new_item)
    return ApiEnvelope(data=list(strategy_items))
