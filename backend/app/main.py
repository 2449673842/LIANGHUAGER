from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.market import router as market_router
from app.routers.health import router as health_router
from app.routers.strategies import router as strategies_router
from app.routers.trading import router as trading_router
from app.routers.workbench import router as workbench_router

app = FastAPI(
    title="Codex 实盘回测",
    version="0.1.0",
    description="独立重建中的 OKX 实盘 / 模拟 / 回测工作台后端骨架",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(market_router)
app.include_router(strategies_router)
app.include_router(workbench_router)
app.include_router(trading_router)


@app.get("/")
def root() -> dict:
    return {
        "service": "codex-live-backtest",
        "frontend": "http://127.0.0.1:9502",
        "next_step": "migrate quant_platform backend slices and trading-dashboard terminal logic",
    }
