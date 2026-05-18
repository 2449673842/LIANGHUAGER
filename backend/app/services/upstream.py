from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
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
_REFRESHING: set[str] = set()
_REFRESH_EXECUTOR = ThreadPoolExecutor(max_workers=4)

# Default time‑to‑live values in seconds for various data types.  Adjust
# accordingly if requirements change.
CANDLE_TTL: float = 1.0
SNAPSHOT_TTL: float = 0.5
INSTRUMENTS_TTL: float = 180.0


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
    return None


def get_stale_cache(key: str) -> Any | None:
    """Return the last cached value even when it is past its live TTL."""
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        return entry[1] if entry else None


def set_cache(key: str, data: Any) -> None:
    """Store data in the cache with the current timestamp."""
    with _CACHE_LOCK:
        _CACHE[key] = (time.time(), data)


def refresh_cache_async(key: str, refresh: Any) -> None:
    """Run one background refresh for a cache key while serving stale data."""
    with _CACHE_LOCK:
        if key in _REFRESHING:
            return
        _REFRESHING.add(key)

    def _run() -> None:
        try:
            refresh()
        finally:
            with _CACHE_LOCK:
                _REFRESHING.discard(key)

    _REFRESH_EXECUTOR.submit(_run)


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


def fetch_upstream(path: str, params: dict[str, Any] | None = None, timeout: float | None = None) -> UpstreamResult:
    query = urlencode({key: value for key, value in (params or {}).items() if value not in (None, "")})
    url = f"{settings.upstream_base_url}{path}"
    if query:
        url = f"{url}?{query}"

    try:
        with urlopen(url, timeout=timeout or settings.upstream_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return UpstreamResult(connected=True, source="upstream", data=_coerce_envelope(payload))
    except Exception as exc:  # pragma: no cover - network path depends on local environment
        return UpstreamResult(connected=False, source="fallback", data=None, error=str(exc))


def fetch_okx_public(path: str, params: dict[str, Any] | None = None, timeout: float | None = None) -> UpstreamResult:
    query = urlencode({key: value for key, value in (params or {}).items() if value not in (None, "")})
    url = f"{settings.okx_public_base_url}{path}"
    if query:
        url = f"{url}?{query}"

    try:
        with urlopen(url, timeout=timeout or settings.upstream_timeout_seconds) as response:
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
        normalized.sort(key=lambda item: item["ts"])
        source = "upstream"

    return {
        "source": source,
        "instrumentId": instrument_id,
        "timeframe": timeframe,
        "items": normalized[:limit],
    }


def sync_latest_candle_with_ticker(payload: dict[str, Any], instrument_id: str) -> dict[str, Any]:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        return payload
    ticker_result = fetch_okx_public("/api/v5/market/ticker", {"instId": instrument_id}, timeout=1.5)
    if not ticker_result.connected:
        ticker_result = fetch_okx_cli(["market", "ticker", instrument_id])
    row = ticker_result.data[0] if ticker_result.connected and isinstance(ticker_result.data, list) and ticker_result.data else None
    if not row:
        return payload
    try:
        last_price = float(row.get("last") or 0)
        if last_price <= 0:
            return payload
        latest = dict(items[-1])
        latest["close"] = last_price
        latest["high"] = max(float(latest.get("high") or last_price), last_price)
        latest["low"] = min(float(latest.get("low") or last_price), last_price)
        payload["items"] = [*items[:-1], latest]
        payload["tickerSynced"] = True
    except (TypeError, ValueError):
        return payload
    return payload


def fetch_bar_series(
    instrument_id: str,
    timeframe: str,
    limit: int = 160,
    force_refresh: bool = False,
) -> dict[str, Any]:
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
    if not force_refresh:
        cached = get_cache(cache_key, CANDLE_TTL)
        if cached is not None:
            return cached
        stale = get_stale_cache(cache_key)
        if stale is not None:
            refresh_cache_async(
                cache_key,
                lambda: fetch_bar_series(instrument_id, timeframe, limit, force_refresh=True),
            )
            return stale

    # Public market data needs to feel live; OKX REST is usually much faster
    # than spawning the CLI process for every poll. Account and order execution
    # paths still use the CLI where credentials and safety controls matter.
    okx_result = fetch_okx_public(
        "/api/v5/market/candles",
        {
            "instId": instrument_id,
            "bar": timeframe,
            "limit": limit,
        },
        timeout=2.0,
    )
    if okx_result.connected:
        payload = normalize_candles(okx_result.data, instrument_id, timeframe, limit)
        payload["source"] = "okx-public"
        payload = sync_latest_candle_with_ticker(payload, instrument_id)
        set_cache(cache_key, payload)
        return payload

    # Fallback to the official CLI if the public REST path is unavailable.
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
        payload = sync_latest_candle_with_ticker(payload, instrument_id)
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
        payload = sync_latest_candle_with_ticker(payload, instrument_id)
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


def fetch_view(view_name: str, timeout: float | None = None, **params: Any) -> UpstreamResult:
    query = {"view_name": view_name}
    query.update(params)
    return fetch_upstream("/platform/views/query", query, timeout=timeout)


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


def _okx_inst_type(symbol: str) -> str:
    return "SWAP" if normalize_inst_id(symbol).endswith("-SWAP") else "SPOT"


def _fetch_okx_tickers_by_type(inst_types: set[str]) -> tuple[str, dict[str, dict[str, Any]]]:
    rows_by_symbol: dict[str, dict[str, Any]] = {}
    source = "fallback"
    for inst_type in sorted(inst_types):
        result = fetch_okx_public("/api/v5/market/tickers", {"instType": inst_type}, timeout=1.5)
        if not result.connected:
            continue
        source = result.source
        for row in result.data if isinstance(result.data, list) else []:
            inst_id = str(row.get("instId") or "").upper()
            if inst_id:
                rows_by_symbol[inst_id] = row
    return source, rows_by_symbol


def _fetch_okx_ticker(symbol: str) -> UpstreamResult:
    result = fetch_okx_public("/api/v5/market/ticker", {"instId": symbol}, timeout=1.5)
    if result.connected:
        return result
    return fetch_okx_cli(["market", "ticker", symbol])


def _fetch_okx_orderbook(symbol: str) -> UpstreamResult:
    result = fetch_okx_public("/api/v5/market/books", {"instId": symbol, "sz": 5}, timeout=1.5)
    if result.connected:
        return result
    return fetch_okx_cli(["market", "orderbook", symbol, "--sz", "5"])


def fetch_okx_market_snapshot(
    inst_id: str = "BTC-USDT",
    watchlist: list[str] | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    inst_id = normalize_inst_id(inst_id)
    # use a combined cache key for the full snapshot.  Because the snapshot
    # aggregates ticker, orderbook and watchlist, caching at this level
    # prevents multiple downstream calls during rapid polling.
    cache_key = f"market_snapshot:{inst_id}:{','.join(watchlist or []) if watchlist else ''}"
    if not force_refresh:
        cached = get_cache(cache_key, SNAPSHOT_TTL)
        if cached is not None:
            return cached
        stale = get_stale_cache(cache_key)
        if stale is not None:
            refresh_cache_async(
                cache_key,
                lambda: fetch_okx_market_snapshot(inst_id, watchlist, force_refresh=True),
            )
            return stale

    symbols = [normalize_inst_id(symbol) for symbol in (watchlist or ["BTC-USDT", "ETH-USDT", "SOL-USDT", "DOGE-USDT"])]
    query_symbols = symbols if inst_id in symbols else [inst_id, *symbols]

    ticker_source, tickers_by_symbol = _fetch_okx_tickers_by_type({_okx_inst_type(symbol) for symbol in query_symbols})
    with ThreadPoolExecutor(max_workers=2) as executor:
        ticker_future = executor.submit(_fetch_okx_ticker, inst_id) if inst_id not in tickers_by_symbol else None
        books_future = executor.submit(_fetch_okx_orderbook, inst_id)
        ticker_result = ticker_future.result() if ticker_future else UpstreamResult(
            connected=True,
            source=ticker_source,
            data=[tickers_by_symbol[inst_id]],
        )
        books_result = books_future.result()

    if ticker_result.connected and isinstance(ticker_result.data, list) and ticker_result.data:
        tickers_by_symbol[inst_id] = ticker_result.data[0]

    watch_rows: list[dict[str, Any]] = []
    for symbol in symbols:
        row = tickers_by_symbol.get(symbol)
        if row is None:
            row_result = _fetch_okx_ticker(symbol)
            row = row_result.data[0] if row_result.connected and isinstance(row_result.data, list) and row_result.data else None
        if not row:
            watch_rows.append(
                {
                    "symbol": symbol.replace("-", "/"),
                    "price": "--",
                    "change": "--",
                    "high24h": "--",
                    "low24h": "--",
                    "volume24h": "--",
                    "signal": "等待行情",
                }
            )
            continue
        change_pct = _normalize_okx_change_pct(row)
        high_24h = float(row.get("high24h") or 0)
        low_24h = float(row.get("low24h") or 0)
        volume_24h = float(row.get("volCcy24h") or row.get("vol24h") or 0)
        watch_rows.append(
            {
                "symbol": symbol.replace("-", "/"),
                "price": f"{float(row.get('last') or 0):,.4f}".rstrip("0").rstrip("."),
                "change": f"{change_pct:+.2f}%",
                "high24h": f"{high_24h:,.4f}".rstrip("0").rstrip("."),
                "low24h": f"{low_24h:,.4f}".rstrip("0").rstrip("."),
                "volume24h": f"{volume_24h:,.0f}",
                "signal": "实时行情",
            }
        )

    ticker = tickers_by_symbol.get(inst_id)
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


def fetch_okx_instruments(query: str = "", limit: int = 80) -> dict[str, Any]:
    normalized_query = query.strip().upper()
    cache_key = "okx_instruments:spot_swap"
    cached = get_cache(cache_key, INSTRUMENTS_TTL)
    if cached is None:
        items: list[dict[str, str]] = []
        source = "fallback"
        connected = False
        for inst_type, label in (("SPOT", "现货"), ("SWAP", "永续")):
            result = fetch_okx_cli(["market", "instruments", "--instType", inst_type])
            if not result.connected:
                result = fetch_okx_public("/api/v5/public/instruments", {"instType": inst_type})
            if result.connected and isinstance(result.data, list):
                connected = True
                source = result.source
                for row in result.data:
                    inst_id = str(row.get("instId") or "").upper()
                    base_ccy = str(row.get("baseCcy") or row.get("uly") or inst_id.split("-")[0]).upper()
                    quote_ccy = str(row.get("quoteCcy") or "USDT").upper()
                    if not inst_id or "USDT" not in inst_id:
                        continue
                    items.append(
                        {
                            "symbol": inst_id,
                            "base": base_ccy,
                            "quote": quote_ccy,
                            "marketType": inst_type,
                            "marketLabel": label,
                            "label": f"{inst_id} · {label}",
                        }
                    )
        cached = {"source": source, "connected": connected, "items": items}
        if connected:
            set_cache(cache_key, cached)

    items = list(cached["items"])
    if normalized_query:
        starts = [
            item for item in items
            if item["base"].startswith(normalized_query) or item["symbol"].startswith(normalized_query)
        ]
        contains = [
            item for item in items
            if item not in starts and normalized_query in item["symbol"]
        ]
        items = starts + contains

    return {
        "source": cached["source"],
        "connected": cached["connected"],
        "items": items[:limit],
    }
