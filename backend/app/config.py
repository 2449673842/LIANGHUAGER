from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    upstream_base_url: str = os.getenv("CODEX_UPSTREAM_BASE_URL", "http://127.0.0.1:5000")
    upstream_timeout_seconds: float = float(os.getenv("CODEX_UPSTREAM_TIMEOUT", "6"))
    default_instrument_id: str = os.getenv("CODEX_DEFAULT_INSTRUMENT", "BTC-USDT")
    default_timeframe: str = os.getenv("CODEX_DEFAULT_TIMEFRAME", "15m")
    okx_public_base_url: str = os.getenv("CODEX_OKX_BASE_URL", "https://www.okx.com")
    okx_cli_path: str = os.getenv("CODEX_OKX_CLI_PATH", r"C:\Users\SZC\AppData\Roaming\npm\okx.cmd")


settings = Settings()
