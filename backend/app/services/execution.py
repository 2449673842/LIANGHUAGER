from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import shlex
import subprocess
from typing import Any

from app.config import settings


@dataclass
class ExecutionResult:
    ok: bool
    mode: str
    dry_run: bool
    source: str
    message: str
    command: list[str]
    submitted_at: str
    raw_output: str | None = None
    raw_error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "dryRun": self.dry_run,
            "source": self.source,
            "message": self.message,
            "command": self.command,
            "submittedAt": self.submitted_at,
            "rawOutput": self.raw_output,
            "rawError": self.raw_error,
        }


def normalize_symbol(symbol: str | None) -> str:
    """Normalize instrument ids to OKX style, e.g. BTC/USDT -> BTC-USDT."""
    if not symbol:
        return settings.default_instrument_id
    return symbol.replace("/", "-").upper()


def infer_side(action: str | None) -> str:
    """Infer OKX side from Chinese action text."""
    text = action or ""
    if any(token in text for token in ("空", "卖", "平多")):
        return "sell"
    return "buy"


def build_okx_order_command(task: dict[str, Any]) -> list[str]:
    """Build the OKX Agent CLI command for a queue task."""
    okx_cli = settings.okx_cli_path
    instrument_id = normalize_symbol(task.get("symbol"))
    side = infer_side(task.get("action"))
    size = str(task.get("size") or os.getenv("CODEX_DEFAULT_ORDER_SIZE", "0.001"))
    trade_mode = str(task.get("tradeMode") or os.getenv("CODEX_DEFAULT_TRADE_MODE", "cross"))

    return [
        okx_cli,
        "trade",
        "order",
        "--instId",
        instrument_id,
        "--side",
        side,
        "--ordType",
        "market",
        "--sz",
        size,
        "--tdMode",
        trade_mode,
    ]


def execute_queue_task(task: dict[str, Any], *, mode: str) -> dict[str, Any]:
    """Execute a queue task through the configured OKX Agent CLI.

    Safety default: unless CODEX_TRADING_ALLOW_LIVE=true, this function returns
    a dry-run result and does not call the CLI.
    """
    command = build_okx_order_command(task)
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allow_live = os.getenv("CODEX_TRADING_ALLOW_LIVE", "false").lower() == "true"

    if not allow_live:
        return ExecutionResult(
            ok=True,
            mode=mode,
            dry_run=True,
            source="okx-cli-dry-run",
            message="dry-run: 未启用 CODEX_TRADING_ALLOW_LIVE=true，未真实下单",
            command=command,
            submitted_at=submitted_at,
        ).as_dict()

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=float(os.getenv("CODEX_TRADE_TIMEOUT", "12")),
            check=False,
        )
    except FileNotFoundError as exc:
        return ExecutionResult(
            ok=False, mode=mode, dry_run=False, source="okx-cli",
            message=f"OKX CLI 未找到: {command[0]}", command=command,
            submitted_at=submitted_at, raw_error=str(exc),
        ).as_dict()
    except Exception as exc:
        return ExecutionResult(
            ok=False, mode=mode, dry_run=False, source="okx-cli",
            message="OKX CLI 执行异常", command=command,
            submitted_at=submitted_at, raw_error=str(exc),
        ).as_dict()

    ok = completed.returncode == 0
    return ExecutionResult(
        ok=ok, mode=mode, dry_run=False, source="okx-cli",
        message="OKX CLI 已提交" if ok else "OKX CLI 返回失败",
        command=command, submitted_at=submitted_at,
        raw_output=completed.stdout.strip() or None,
        raw_error=completed.stderr.strip() or None,
    ).as_dict()


def format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)
