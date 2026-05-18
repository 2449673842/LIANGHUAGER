from __future__ import annotations

import ast
from datetime import datetime
from itertools import count
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from app.schemas.common import ApiEnvelope
from app.services.mock_data import STRATEGIES
from app.services.upstream import fetch_upstream

router = APIRouter(prefix="/api", tags=["strategies"])

DEFAULT_CODE = '''my_indicator_name = "BTC Trend Follow"
my_indicator_description = "单一来源的策略参数样例"

# @strategy stopLossPct 0.03
# @strategy takeProfitPct 0.06
# @strategy entryPct 1.0
# @strategy trailingEnabled true
# @strategy trailingStopPct 0.02
# @strategy tradeDirection long

df = df.copy()
df["buy"] = False
df["sell"] = False

fast = df["close"].rolling(10).mean()
slow = df["close"].rolling(24).mean()

df.loc[(fast > slow) & (fast.shift(1) <= slow.shift(1)), "buy"] = True
df.loc[(fast < slow) & (fast.shift(1) >= slow.shift(1)), "sell"] = True
'''

strategy_items: list[dict[str, Any]] = [dict(item) for item in STRATEGIES["items"]]
strategy_sources: dict[str, str] = {item["strategyId"]: DEFAULT_CODE for item in strategy_items}
strategy_versions: dict[str, list[dict[str, Any]]] = {
    item["strategyId"]: [
        {
            "versionId": item["versionId"],
            "label": item["label"],
            "status": item.get("status", "已发布"),
            "updatedAt": item.get("updatedAt", "--"),
            "note": "初始版本",
            "code": strategy_sources[item["strategyId"]],
        }
    ]
    for item in strategy_items
}
_version_counter = count(2)

strategy_templates: list[dict[str, Any]] = [
    {
        "id": "trend-follow",
        "label": "趋势跟随模板",
        "instrumentId": "BTC-USDT",
        "timeframe": "15m",
        "code": DEFAULT_CODE,
    },
    {
        "id": "mean-reversion",
        "label": "均值回归模板",
        "instrumentId": "ETH-USDT",
        "timeframe": "1H",
        "code": '''my_indicator_name = "Mean Reversion"
my_indicator_description = "均值回归策略模板"

window = 20
threshold = 2.0

df = df.copy()
ma = df["close"].rolling(window).mean()
std = df["close"].rolling(window).std()

z = (df["close"] - ma) / std

df["buy"] = z < -threshold
df["sell"] = z > threshold
''',
    },
]


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _slug(value: str) -> str:
    allowed = []
    for char in value.strip().lower().replace(" ", "_"):
        if char.isalnum() or char in {"_", "-"}:
            allowed.append(char)
    slug = "".join(allowed).strip("_-")
    return slug or f"strategy_{len(strategy_items) + 1}"


def _find_strategy(strategy_id: str) -> dict[str, Any]:
    for item in strategy_items:
        if item.get("strategyId") == strategy_id:
            return item
    raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")


def _map_upstream_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategyId": row.get("strategy_id") or row.get("strategyId") or "unknown-strategy",
        "versionId": row.get("version_id") or row.get("versionId") or "unknown-version",
        "label": row.get("version_name") or row.get("strategy_name") or row.get("strategy_id") or "未命名策略",
        "instrumentId": row.get("instrument_id") or row.get("instrumentId") or "--",
        "timeframe": row.get("timeframe") or "--",
        "status": row.get("status") or row.get("governance_status") or "已导入",
        "updatedAt": str(row.get("updated_at") or row.get("created_at") or "--"),
    }


@router.get("/strategies/board", response_model=ApiEnvelope[dict])
def get_strategies_board(limit: int = Query(default=12, ge=1, le=50)) -> ApiEnvelope[dict]:
    result = fetch_upstream("/platform/strategies/versions", {"limit": limit})
    payload = dict(STRATEGIES)
    payload["source"] = result.source if result.connected else "local"
    payload["upstreamConnected"] = result.connected

    items = list(strategy_items)
    if result.connected:
        rows = result.data if isinstance(result.data, list) else result.data.get("items") or result.data.get("rows") or []
        mapped = [_map_upstream_row(row) for row in rows[:limit]]
        mapped_ids = {item["versionId"] for item in mapped}
        items = mapped + [item for item in items if item.get("versionId") not in mapped_ids]

    payload["items"] = items[:limit]
    return ApiEnvelope(data=payload)


@router.post("/strategies/import", response_model=ApiEnvelope[list[dict]])
def import_strategy(payload: dict = Body(default_factory=dict)) -> ApiEnvelope[list[dict]]:
    label = payload.get("label") or f"新策略-{len(strategy_items) + 1}"
    instrument_id = payload.get("instrumentId") or payload.get("instrument_id") or "BTC-USDT"
    timeframe = payload.get("timeframe") or "15m"
    code = payload.get("code") or DEFAULT_CODE
    strategy_id = _slug(payload.get("strategyId") or label)
    if any(item.get("strategyId") == strategy_id for item in strategy_items):
        strategy_id = f"{strategy_id}_{len(strategy_items) + 1}"
    version_id = f"{strategy_id}:v1.0.0"
    now_text = _now_text()
    item = {
        "strategyId": strategy_id,
        "versionId": version_id,
        "label": label,
        "instrumentId": instrument_id.replace("/", "-").upper(),
        "timeframe": timeframe,
        "status": "已导入",
        "updatedAt": now_text,
    }
    strategy_items.insert(0, item)
    strategy_sources[strategy_id] = code
    strategy_versions[strategy_id] = [
        {"versionId": version_id, "label": label, "status": "已导入", "updatedAt": now_text, "note": "导入策略", "code": code}
    ]
    return ApiEnvelope(data=list(strategy_items))


@router.get("/strategies/templates", response_model=ApiEnvelope[list[dict]])
def get_strategy_templates() -> ApiEnvelope[list[dict]]:
    return ApiEnvelope(data=list(strategy_templates))


@router.post("/strategies/templates", response_model=ApiEnvelope[list[dict]])
def create_strategy_from_template(payload: dict = Body(default_factory=dict)) -> ApiEnvelope[list[dict]]:
    template_id = payload.get("templateId") or "trend-follow"
    template = next((item for item in strategy_templates if item.get("id") == template_id), strategy_templates[0])
    label = payload.get("label") or template["label"]
    return import_strategy(
        {
            "label": label,
            "instrumentId": payload.get("instrumentId") or template.get("instrumentId"),
            "timeframe": payload.get("timeframe") or template.get("timeframe"),
            "code": template.get("code") or DEFAULT_CODE,
        }
    )


@router.put("/strategies/templates/{template_id}", response_model=ApiEnvelope[list[dict]])
def rename_strategy_template(template_id: str, payload: dict = Body(...)) -> ApiEnvelope[list[dict]]:
    """Rename a strategy template.

    Accepts `new_label` in the JSON body.  Returns the updated template list.
    """
    template = next((item for item in strategy_templates if item.get("id") == template_id), None)
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    new_label = payload.get("new_label") or payload.get("label") or payload.get("newLabel")
    if new_label and isinstance(new_label, str) and new_label.strip():
        template["label"] = new_label.strip()
    return ApiEnvelope(data=list(strategy_templates))


@router.post("/strategies/templates/save", response_model=ApiEnvelope[list[dict]])
def save_custom_template(payload: dict = Body(...)) -> ApiEnvelope[list[dict]]:
    """Save current parameters as a new template.

    Accepts `name` (required), and optional `code`, `instrumentId`, `timeframe`.
    Returns the updated template list.
    """
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    template_id = _slug(name)
    code = payload.get("code") or DEFAULT_CODE
    instrument_id = (payload.get("instrumentId") or "BTC-USDT").replace("/", "-").upper()
    timeframe = payload.get("timeframe") or "15m"
    # Remove existing template with same id before adding
    strategy_templates[:] = [item for item in strategy_templates if item.get("id") != template_id]
    strategy_templates.append({
        "id": template_id,
        "label": name,
        "instrumentId": instrument_id,
        "timeframe": timeframe,
        "code": code,
    })
    return ApiEnvelope(data=list(strategy_templates))


@router.delete("/strategies/templates/{template_id}", response_model=ApiEnvelope[list[dict]])
def delete_strategy_template(template_id: str) -> ApiEnvelope[list[dict]]:
    """Delete a strategy template.

    Returns the updated template list (the deleted template is removed).
    """
    template = next((item for item in strategy_templates if item.get("id") == template_id), None)
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    strategy_templates[:] = [item for item in strategy_templates if item.get("id") != template_id]
    return ApiEnvelope(data=list(strategy_templates))


@router.get("/strategies/{strategy_id}/code", response_model=ApiEnvelope[dict])
def get_strategy_code(strategy_id: str) -> ApiEnvelope[dict]:
    item = _find_strategy(strategy_id)
    code = strategy_sources.get(strategy_id) or DEFAULT_CODE
    return ApiEnvelope(data={"strategyId": strategy_id, "label": item.get("label"), "code": code})


@router.put("/strategies/{strategy_id}/code", response_model=ApiEnvelope[dict])
def save_strategy_code(strategy_id: str, payload: dict = Body(...)) -> ApiEnvelope[dict]:
    item = _find_strategy(strategy_id)
    code = payload.get("code") or ""
    strategy_sources[strategy_id] = code
    item["updatedAt"] = _now_text()
    return ApiEnvelope(data={"strategyId": strategy_id, "label": item.get("label"), "code": code, "updatedAt": item["updatedAt"]})


@router.post("/strategies/check", response_model=ApiEnvelope[dict])
def check_strategy_code(payload: dict = Body(...)) -> ApiEnvelope[dict]:
    code = payload.get("code") or ""
    errors: list[str] = []
    warnings: list[str] = []
    # 1) Python AST parse for syntax errors
    try:
        tree = ast.parse(code, filename="strategy.py")
    except SyntaxError as exc:
        errors.append(f"语法错误 第 {exc.lineno} 行: {exc.msg}")
        return ApiEnvelope(data={"ok": False, "errors": errors, "warnings": warnings, "checkedAt": _now_text()})
    # 2) AST walk to detect banned imports and function calls
    banned_modules = {"os", "sys", "subprocess"}
    banned_funcs = {"eval", "exec"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if base in banned_modules:
                    errors.append(f"禁止使用模块: {alias.name}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in banned_funcs:
                errors.append(f"禁止调用函数: {func.id}")
    # 3) Heuristic checks on variable references
    if "df" not in code:
        warnings.append("未检测到 df 数据帧引用，可能不是完整策略。")
    if "buy" not in code and "sell" not in code:
        warnings.append("未检测到 buy/sell 信号字段。")
    return ApiEnvelope(data={"ok": not errors, "errors": errors, "warnings": warnings, "checkedAt": _now_text()})


@router.get("/strategies/{strategy_id}/versions", response_model=ApiEnvelope[list[dict]])
def get_strategy_versions(strategy_id: str) -> ApiEnvelope[list[dict]]:
    _find_strategy(strategy_id)
    versions = [{key: value for key, value in version.items() if key != "code"} for version in strategy_versions.get(strategy_id, [])]
    return ApiEnvelope(data=versions)


@router.post("/strategies/{strategy_id}/versions", response_model=ApiEnvelope[dict])
def save_strategy_version(strategy_id: str, payload: dict = Body(...)) -> ApiEnvelope[dict]:
    item = _find_strategy(strategy_id)
    code = payload.get("code") or strategy_sources.get(strategy_id) or DEFAULT_CODE
    note = payload.get("note") or "保存版本"
    next_no = next(_version_counter)
    version_id = f"{strategy_id}:v1.{next_no}.0"
    now_text = _now_text()
    version = {
        "versionId": version_id,
        "label": item.get("label"),
        "status": "已保存",
        "updatedAt": now_text,
        "note": note,
        "code": code,
    }
    strategy_versions.setdefault(strategy_id, []).insert(0, version)
    strategy_sources[strategy_id] = code
    item["versionId"] = version_id
    item["status"] = "已保存"
    item["updatedAt"] = now_text
    return ApiEnvelope(data={key: value for key, value in version.items() if key != "code"})


@router.post("/strategies/publish", response_model=ApiEnvelope[dict])
def publish_strategy(payload: dict = Body(...)) -> ApiEnvelope[dict]:
    strategy_id = payload.get("strategyId")
    if not strategy_id:
        raise HTTPException(status_code=400, detail="strategyId is required")
    item = _find_strategy(strategy_id)
    version_id = payload.get("versionId") or item.get("versionId")
    from app.routers import trading

    queue_payload = {
        "strategy": item.get("label") or strategy_id,
        "symbol": item.get("instrumentId") or "BTC-USDT",
        "action": "发布运行",
        "reason": f"策略版本 {version_id} 发布到运行台",
    }
    queue_result = trading.add_queue(queue_payload).data
    item["status"] = "已发布"
    item["updatedAt"] = _now_text()
    return ApiEnvelope(data={"strategy": item, "queue": queue_result[0] if queue_result else None})
