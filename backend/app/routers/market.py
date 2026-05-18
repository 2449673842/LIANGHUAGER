from fastapi import APIRouter, Query

from app.config import settings
from app.schemas.common import ApiEnvelope
from app.services.upstream import fetch_bar_series, fetch_okx_instruments, fetch_okx_market_snapshot

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/market/candles", response_model=ApiEnvelope[dict])
def get_market_candles(
    instrument_id: str = Query(default=settings.default_instrument_id),
    timeframe: str = Query(default=settings.default_timeframe),
    limit: int = Query(default=160, ge=50, le=500),
) -> ApiEnvelope[dict]:
    return ApiEnvelope(data=fetch_bar_series(instrument_id=instrument_id, timeframe=timeframe, limit=limit))


@router.get("/market/snapshot", response_model=ApiEnvelope[dict])
def get_market_snapshot(
    instrument_id: str = Query(default=settings.default_instrument_id),
) -> ApiEnvelope[dict]:
    return ApiEnvelope(data=fetch_okx_market_snapshot(inst_id=instrument_id))


@router.get("/market/instruments", response_model=ApiEnvelope[dict])
def get_market_instruments(
    q: str = Query(default=""),
    limit: int = Query(default=800, ge=1, le=1200),
) -> ApiEnvelope[dict]:
    return ApiEnvelope(data=fetch_okx_instruments(query=q, limit=limit))
