from __future__ import annotations

from fastapi import APIRouter, Body

from app.schemas.common import ApiEnvelope
from app.services.state_store import AI_SETTINGS_STATE_PATH, load_json_state, save_json_state

router = APIRouter(prefix="/api", tags=["settings"])

DEFAULT_AI_SETTINGS = {
    "enabled": False,
    "provider": "OpenAI-compatible",
    "baseUrl": "",
    "model": "",
    "apiKey": "",
    "timeoutSeconds": 20,
}


def _load_ai_settings() -> dict:
    payload = load_json_state(AI_SETTINGS_STATE_PATH, DEFAULT_AI_SETTINGS)
    merged = {**DEFAULT_AI_SETTINGS, **payload}
    return merged


def _public_ai_settings(payload: dict) -> dict:
    return {
        "enabled": bool(payload.get("enabled")),
        "provider": str(payload.get("provider") or ""),
        "baseUrl": str(payload.get("baseUrl") or ""),
        "model": str(payload.get("model") or ""),
        "hasApiKey": bool(payload.get("apiKey")),
        "timeoutSeconds": int(payload.get("timeoutSeconds") or 20),
    }


@router.get("/settings/ai", response_model=ApiEnvelope[dict])
def get_ai_settings() -> ApiEnvelope[dict]:
    return ApiEnvelope(data=_public_ai_settings(_load_ai_settings()))


@router.post("/settings/ai", response_model=ApiEnvelope[dict])
def save_ai_settings(settings: dict = Body(...)) -> ApiEnvelope[dict]:
    current = _load_ai_settings()
    api_key = str(settings.get("apiKey") or "").strip()
    payload = {
        "enabled": bool(settings.get("enabled")),
        "provider": str(settings.get("provider") or current.get("provider") or "OpenAI-compatible").strip(),
        "baseUrl": str(settings.get("baseUrl") or "").strip(),
        "model": str(settings.get("model") or "").strip(),
        "apiKey": api_key or current.get("apiKey") or "",
        "timeoutSeconds": max(5, min(120, int(settings.get("timeoutSeconds") or 20))),
    }
    save_json_state(AI_SETTINGS_STATE_PATH, payload)
    return ApiEnvelope(data=_public_ai_settings(payload))
