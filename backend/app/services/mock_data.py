OVERVIEW = {
    "marketPulse": [
        {"label": "BTC/USDT", "value": "103,842.8", "tone": "up"},
        {"label": "24h 变化", "value": "+2.41%", "tone": "up"},
        {"label": "活跃策略", "value": "12", "tone": "neutral"},
        {"label": "实时告警", "value": "3", "tone": "down"},
    ],
    "watchlist": [
        {"symbol": "BTC/USDT", "price": "103,842.8", "change": "+2.41%", "signal": "趋势延续"},
        {"symbol": "ETH/USDT", "price": "4,978.2", "change": "+1.34%", "signal": "突破回踩"},
        {"symbol": "SOL/USDT", "price": "238.7", "change": "-0.84%", "signal": "观望"},
        {"symbol": "DOGE/USDT", "price": "0.2281", "change": "+4.92%", "signal": "量价共振"},
    ],
    "positions": [
        {"strategy": "趋势跟随-A", "symbol": "BTC/USDT", "side": "做多", "pnl": "+842.40", "size": "0.75 BTC"},
        {"strategy": "突破回踩-B", "symbol": "ETH/USDT", "side": "做多", "pnl": "+192.60", "size": "8 ETH"},
        {"strategy": "均值回归-C", "symbol": "SOL/USDT", "side": "做空", "pnl": "-54.22", "size": "320 SOL"},
    ],
    "activity": [
        {"time": "09:42:18", "message": "BTC/USDT 触发 15m 做多加仓信号", "tone": "up"},
        {"time": "09:37:06", "message": "ETH/USDT 实盘策略进入人工确认队列", "tone": "neutral"},
        {"time": "09:32:44", "message": "SOL/USDT 触发保护止损", "tone": "down"},
        {"time": "09:29:11", "message": "邮件告警发送成功: trend-follow-btc", "tone": "neutral"},
    ],
    "orderbook": {
        "asks": [
            ["103845.2", "12.84"],
            ["103844.6", "9.22"],
            ["103844.1", "5.90"],
            ["103843.7", "4.11"],
            ["103843.2", "2.34"],
        ],
        "bids": [
            ["103842.5", "10.71"],
            ["103842.0", "8.19"],
            ["103841.4", "7.88"],
            ["103840.9", "4.70"],
            ["103840.4", "3.16"],
        ],
        "spreadText": "2.7 (0.003%)",
    },
    "controlState": {
        "running": True,
        "cooldownSeconds": 124,
        "executionMode": "人工确认",
        "lastSync": "2026-05-16 09:42:24",
    },
}

EXECUTION = {
    "mode": "paper",
    "accounts": [
        {"name": "OKX 主账户", "venue": "OKX", "equity": "128,420.33 USDT", "status": "在线"},
        {"name": "OKX Alpha", "venue": "OKX", "equity": "48,210.11 USDT", "status": "待确认"},
    ],
    "sessions": [
        {"name": "paper-btc-grid", "strategy": "趋势跟随-A", "symbol": "BTC/USDT", "mode": "模拟", "state": "运行中"},
        {"name": "live-eth-breakout", "strategy": "突破回踩-B", "symbol": "ETH/USDT", "mode": "实盘", "state": "人工确认"},
        {"name": "live-sol-mean", "strategy": "均值回归-C", "symbol": "SOL/USDT", "mode": "实盘", "state": "告警中"},
    ],
    "queues": [
        {"time": "09:37:06", "strategy": "突破回踩-B", "symbol": "ETH/USDT", "action": "开多", "reason": "1H 突破确认", "state": "待确认"},
        {"time": "09:34:18", "strategy": "趋势跟随-A", "symbol": "BTC/USDT", "action": "加仓", "reason": "15m 二次放量", "state": "已发送"},
        {"time": "09:31:55", "strategy": "均值回归-C", "symbol": "SOL/USDT", "action": "平空", "reason": "止盈到达", "state": "待确认"},
    ],
    "runtime": {
        "activeTasks": 4,
        "activeSessions": 7,
        "pendingConfirmations": 2,
        "notificationsSent": 18,
    },
}

BACKTEST = {
    "periods": ["1M", "3M", "6M", "1Y"],
    "metrics": [
        {"label": "净收益", "value": "+24.8%", "tone": "up"},
        {"label": "最大回撤", "value": "-7.4%", "tone": "down"},
        {"label": "Sharpe", "value": "1.82", "tone": "up"},
        {"label": "胜率", "value": "58.3%", "tone": "neutral"},
    ],
    "trades": [
        {"time": "2026-04-12 13:45", "side": "买入", "price": "101,224", "reason": "15m 突破"},
        {"time": "2026-04-13 09:30", "side": "卖出", "price": "103,118", "reason": "止盈"},
        {"time": "2026-04-15 22:10", "side": "卖出", "price": "100,840", "reason": "反转确认"},
    ],
    "equityCurve": [
        {"time": "2026-04-01", "value": 10000},
        {"time": "2026-04-04", "value": 10180},
        {"time": "2026-04-08", "value": 10340},
        {"time": "2026-04-12", "value": 10490},
        {"time": "2026-04-16", "value": 10680},
        {"time": "2026-04-20", "value": 10810},
        {"time": "2026-04-24", "value": 11140},
        {"time": "2026-04-28", "value": 11410},
        {"time": "2026-05-02", "value": 11760},
        {"time": "2026-05-06", "value": 12110},
        {"time": "2026-05-10", "value": 12390},
        {"time": "2026-05-14", "value": 12480},
    ],
}

STRATEGIES = {
    "source": "fallback",
    "upstreamConnected": False,
    "items": [
        {
            "strategyId": "trend_follow_btc",
            "versionId": "trend_follow_btc:v1.2.0",
            "label": "趋势跟随-A",
            "instrumentId": "BTC-USDT",
            "timeframe": "15m",
            "status": "已发布",
            "updatedAt": "2026-05-16 09:20",
        },
        {
            "strategyId": "breakout_eth",
            "versionId": "breakout_eth:v0.9.4",
            "label": "突破回踩-B",
            "instrumentId": "ETH-USDT",
            "timeframe": "1H",
            "status": "待审核",
            "updatedAt": "2026-05-16 08:42",
        },
        {
            "strategyId": "mean_revert_sol",
            "versionId": "mean_revert_sol:v2.1.1",
            "label": "均值回归-C",
            "instrumentId": "SOL-USDT",
            "timeframe": "15m",
            "status": "运行中",
            "updatedAt": "2026-05-15 22:31",
        },
    ],
}


def build_fallback_candles(limit: int = 160) -> list[dict]:
    candles: list[dict] = []
    base = 96000.0
    for index in range(limit):
        # deterministic synthetic series for local fallback use
        drift = (index % 11 - 5) * 82
        open_price = base + drift + index * 17
        close_price = open_price + ((index % 7) - 3) * 46
        high_price = max(open_price, close_price) + 110 + (index % 5) * 16
        low_price = min(open_price, close_price) - 95 - (index % 4) * 21
        candles.append(
            {
                "ts": 1714550400000 + index * 900000,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": round(220 + (index % 9) * 38 + index * 0.8, 2),
            }
        )
    return candles
