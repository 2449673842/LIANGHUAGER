from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STATE_DIR = Path(__file__).resolve().parents[2] / "data"
EXECUTION_STATE_PATH = STATE_DIR / "execution_state.json"
WORKBENCH_STATE_PATH = STATE_DIR / "workbench_state.json"
AI_SETTINGS_STATE_PATH = STATE_DIR / "ai_settings_state.json"


def load_json_state(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
      if path.exists():
          return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
      pass
    return fallback


def save_json_state(path: Path, payload: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
