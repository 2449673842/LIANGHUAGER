from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
import time
from threading import Lock

from app.config import settings
from app.services.mock_data import build_fallback_candles

# ---------------------------------------------------------------------------
# Simple in-memory caching layer
#
# Heavy upstream operations such as K‑line series queries and market snapshots
# rely on external processes (e.g. okx-cli) or HTTP requests.  Without a
# throttle these calls can overwhelm the backend when the frontend polls
# aggressively.  The `_CACHE` dict stores (timestamp, data) pairs keyed by
# request parameters.  `get_cache` returns a cached value when it is still
# within its TTL, otherwise it evicts the entry.  All access is guarded by
# a threading.Lock for thread safety.
#
# TTL values are chosen according to product requirements: orderbook and
# ticker snapshots should feel live (≈1s), candle series can be updated
# less frequently (≈5s), and watchlist and account data fall in between.  If
# these constants need to be tuned, adjust them in one place below.
# ---------------------------------------------------------------------------

_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_LOCK: Lock = Lock()

# Default time‑to‑live values in seconds for various data types.  Adjust
# accordingly if requirements change.
CANDLE_TTL: float = 5.0
SNAPSHOT_TTL: float = 1.0


def get_cache(key: str, ttl: float) -> Any | None:
    """Return cached value if it exists and has not expired."""
    now = time.time()
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry:
            ts, data = entry
            # if entry is still fresh return it
            if now - ts < ttl:
                return data
            # otherwise remove expired entry
            _CACHE.pop(key, None)
    return None


def set_cache(key: str, data: Any) -> None:
    """Store data in the cache with the current timestamp."""
    with _CACHE_LOCK:
        _CACHE[key] = (time.time(), data)


@dataclass
class UpstreamResult:
    connected: bool
    source: str
    data: Any
    error: str | None = None


def normalize_inst_id(inst_id: str) -> str:
    return inst_id.replace("/", "-").upper()


def fetch_okx_cli(command: list[str]) -> UpstreamResult:
    try:
        result = subprocess.run(
            [settings.okx_cli_path, "--json", *command],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=settings.upstream_timeout_seconds,
        )
        payload = json.loads(result.stdout)
        return UpstreamResult(connected=True, source="okx-cli", data=payload)
    except Exception as exc:  # pragma: no cover - depends on local CLI/runtime
        return UpstreamResult(connected=False, source="fallback", data=None, error=str(exc))


def _coerce_envelope(payload: Any) -> Any:
    if isinstance(payload, dict):
        if payload.get("success") is False:
            return payload
        if "data" in payload:
            return payload["data"]
    return payload


def fetch_upstream(path: str, params: dict[str, Any] | None = None) -> UpstreamResult:
    query = urlencode({key: value for key, value in (params or {}).items() if value not in (None, "")})
    url = f"{settings.upstream_base_url}{path}"
    if query:
        url = f"{url}?{query}"

    try:
        with urlopen(url, timeout=settings.upstream_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return UpstreamResult(connected=True, source="upstream", data=_coerce_envelope(payload))
    except Exception as exc:  # pragma: no cover - network path depends on local environment
        return UpstreamResult(connected=False, source="fallback", data=None, error=str(exc))


def fetch_okx_public(path: str, params: dict[str, Any] | None = None) -> UpstreamResult:
    query = urlencode({key: value for key, value in (params or {}).items() if value not in (None, "")})
    url = f"{settings.okx_public_base_url}{path}"
    if query:
        url = f"{url}?{query}"

    try:
        with urlopen(url, timeout=settings.upstream_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = payload.get("data") if isinstance(payload, dict) else payload
        return UpstreamResult(connected=True, source="okx-public", data=data)
    except Exception as exc:  # pragma: no cover - network path depends on local environment
        return UpstreamResult(connected=False, source="fallback", data=None, error=str(exc))


def _first_sequence(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "bars", "series", "rows", "records", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def normalize_candles(payload: Any, instrument_id: str, timeframe: str, limit: int) -> dict[str, Any]:
    raw_items = _first_sequence(payload)
    normalized: list[dict[str, Any]] = []

    for item in raw_items:
        if isinstance(item, dict):
            ts = item.get("ts") or item.get("timestamp") or item.get("time") or item.get("bar_ts")
            open_price = item.get("open") or item.get("o")
            high_price = item.get("high") or item.get("h")
            low_price = item.get("low") or item.get("l")
            close_price = item.get("close") or item.get("c")
            volume = item.get("volume") or item.get("vol") or item.get("v") or 0
        elif isinstance(item, (list, tuple)) and len(item) >= 5:
            ts, open_price, high_price, low_price, close_price = item[:5]
            volume = item[5] if len(item) > 5 else 0
        else:
            continue

        try:
            normalized.append(
                {
                    "ts": int(float(ts)),
                    "open": float(open_price),
                    "high": float(high_price),
                    "low": float(low_price),
                    "close": float(close_price),
                    "volume": float(volume),
                }
            )
        except (TypeError, ValueError):
            continue

    if not normalized:
        normalized = build_fallback_candles(limit)
        source = "fallback"
    else:
        source = "upstream"

    return {
        "source": source,
        "instrumentId": instrument_id,
        "timeframe": timeframe,
        "items": normalized[:limit],
    }


def fetch_bar_series(instrument_id: str, timeframe: str, limit: int = 160) -> dict[str, Any]:
    """
    Fetch a bar series for the given instrument and timeframe.

    The data source priority follows the product specification: use the
    official OKX Agent CLI first, then fall back to the public REST API,
    then to the quant_platform upstream.  If all sources fail, return a
    deterministic fallback series.  Results are cached for a short
    duration to avoid repeated expensive subprocess calls during high
    frequency polling.
    """
    instrument_id = normalize_inst_id(instrument_id)
    # check cache
    cache_key = f"candles:{instrument_id}:{timeframe}:{limit}"
    cached = get_cache(cache_key, CANDLE_TTL)
    if cached is not None:
        return cached

    # Attempt to fetch from OKX CLI (highest priority)
    okx_result = fetch_okx_cli([
        "market",
        "candles",
        instrument_id,
        "--bar",
        timeframe,
        "--limit",
        str(limit),
    ])
    if okx_result.connected:
        payload = normalize_candles(okx_result.data, instrument_id, timeframe, limit)
        payload["source"] = "okx-cli"
        set_cache(cache_key, payload)
        return payload

    # Next try the OKX public REST API
    okx_result = fetch_okx_public(
        "/api/v5/market/candles",
        {
            "instId": instrument_id,
            "bar": timeframe,
            "limit": limit,
        },
    )
    if okx_result.connected:
        payload = normalize_candles(okx_result.data, instrument_id, timeframe, limit)
        payload["source"] = "okx-public"
        set_cache(cache_key, payload)
        return payload

    # Then try the quant_platform upstream
    upstream_result = fetch_upstream(
        "/platform/data/bar-series",
        {
            "instrument_id": instrument_id,
            "timeframe": timeframe,
            "limit": limit,
        },
    )
    if upstream_result.connected:
        payload = normalize_candles(upstream_result.data, instrument_id, timeframe, limit)
        payload["source"] = "upstream"
        set_cache(cache_key, payload)
        return payload

    # Fallback: generate synthetic candles and include the error for visibility
    payload = normalize_candles(None, instrument_id, timeframe, limit)
    payload["source"] = "fallback"
    # propagate any upstream error for debugging purposes
    if 'error' not in payload and hasattr(upstream_result, 'error'):
        payload["error"] = upstream_result.error
    set_cache(cache_key, payload)
    return payload


def fetch_view(view_name: str, **params: Any) -> UpstreamResult:
    query = {"view_name": view_name}
    query.update(params)
    return fetch_upstream("/platform/views/query", query)


def fetch_paper_strategies(limit: int = 8) -> UpstreamResult:
    return fetch_upstream("/platform/paper-strategies", {"limit": limit})


def fetch_strategy_runs(limit: int = 8) -> UpstreamResult:
    return fetch_view("strategy-run-board", limit=limit)


def fetch_execution_runtime(limit: int = 8) -> UpstreamResult:
    return fetch_view("execution-runtime-console", limit=limit)


def _normalize_okx_change_pct(row: dict[str, Any]) -> float:
    try:
        last_price = float(row.get("last") or 0)
        open_24h = float(row.get("open24h") or 0)
        if open_24h == 0:
            return 0.0
        return ((last_price - open_24h) / open_24h) * 100
    except (TypeError, ValueError):
        return 0.0


def fetch_okx_market_snapshot(inst_id: str = "BTC-USDT", watchlist: list[str] | None = None) -> dict[str, Any]:
    inst_id = normalize_inst_id(inst_id)
    # use a combined cache key for the full snapshot.  Because the snapshot
    # aggregates ticker, orderbook and watchlist, caching at this level
    # prevents multiple downstream calls during rapid polling.
    cache_key = f"market_snapshot:{inst_id}:{','.join(watchlist or []) if watchlist else ''}"
    cached = get_cache(cache_key, SNAPSHOT_TTL)
    if cached is not None:
        return cached

    # Fetch ticker and orderbook from the CLI first, fallback to public REST
    ticker_result = fetch_okx_cli(["market", "ticker", inst_id])
    books_result = fetch_okx_cli(["market", "orderbook", inst_id, "--sz", "5"])
    if not ticker_result.connected:
        ticker_result = fetch_okx_public("/api/v5/market/ticker", {"instId": inst_id})
    if not books_result.connected:
        books_result = fetch_okx_public("/api/v5/market/books", {"instId": inst_id, "sz": 5})

    symbols = [normalize_inst_id(symbol) for symbol in (watchlist or ["BTC-USDT", "ETH-USDT", "SOL-USDT", "DOGE-USDT"])]
    watch_rows: list[dict[str, Any]] = []
    for symbol in symbols:
        row_result = fetch_okx_cli(["market", "ticker", symbol])
        if not row_result.connected:
            row_result = fetch_okx_public("/api/v5/market/ticker", {"instId": symbol})
        row = row_result.data[0] if row_result.connected and isinstance(row_result.data, list) and row_result.data else None
        if row:
            change_pct = _normalize_okx_change_pct(row)
            watch_rows.append(
                {
                    "symbol": symbol.replace("-", "/"),
                    "price": f"{float(row.get('last') or 0):,.4f}".rstrip("0").rstrip("."),
                    "change": f"{change_pct:+.2f}%",
                    "signal": "实时行情",
                }
            )

    ticker = ticker_result.data[0] if ticker_result.connected and isinstance(ticker_result.data, list) and ticker_result.data else None
    books = books_result.data[0] if books_result.connected and isinstance(books_result.data, list) and books_result.data else None

    if not ticker and not books and not watch_rows:
        result = {
            "source": "fallback",
            "connected": False,
            "marketPulse": [],
            "watchlist": [],
            "orderbook": None,
        }
        set_cache(cache_key, result)
        return result

    market_pulse: list[dict[str, Any]] = []
    if ticker:
        last_price = float(ticker.get("last") or 0)
        high_24h = float(ticker.get("high24h") or 0)
        low_24h = float(ticker.get("low24h") or 0)
        volume_24h = float(ticker.get("volCcy24h") or 0)
        change_pct = _normalize_okx_change_pct(ticker)
        market_pulse = [
            {"label": inst_id.replace("-", "/"), "value": f"{last_price:,.2f}", "tone": "up" if change_pct >= 0 else "down"},
            {"label": "24h 变化", "value": f"{change_pct:+.2f}%", "tone": "up" if change_pct >= 0 else "down"},
            {"label": "24h 高低", "value": f"{high_24h:,.0f} / {low_24h:,.0f}", "tone": "neutral"},
            {"label": "24h 成交额", "value": f"{volume_24h:,.0f}", "tone": "neutral"},
        ]

    orderbook = None
    if books:
        asks = books.get("asks") or []
        bids = books.get("bids") or []
        spread_text = "--"
        try:
            if asks and bids:
                ask_0 = float(asks[0][0])
                bid_0 = float(bids[0][0])
                spread = ask_0 - bid_0
                spread_pct = (spread / bid_0) * 100 if bid_0 else 0
                spread_text = f"{spread:.2f} ({spread_pct:.3f}%)"
        except (TypeError, ValueError, IndexError):
            spread_text = "--"
        orderbook = {
            "asks": [[str(row[0]), str(row[1])] for row in asks[:5]],
            "bids": [[str(row[0]), str(row[1])] for row in bids[:5]],
            "spreadText": spread_text,
        }

    result = {
        "source": "okx-cli" if ticker_result.source == "okx-cli" or books_result.source == "okx-cli" else "okx-public",
        "connected": True,
        "marketPulse": market_pulse,
        "watchlist": watch_rows,
        "orderbook": orderbook,
    }
    set_cache(cache_key, result)
    return result
