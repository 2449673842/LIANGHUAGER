from fastapi import APIRouter

from app.config import settings
from app.schemas.common import ApiEnvelope

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=ApiEnvelope[dict])
def health() -> ApiEnvelope[dict]:
    return ApiEnvelope(
        data={
            "status": "ok",
            "service": "codex-live-backtest",
            "upstream_base_url": settings.upstream_base_url,
            "okx_public_base_url": settings.okx_public_base_url,
            "default_instrument_id": settings.default_instrument_id,
            "default_timeframe": settings.default_timeframe,
        }
    )
