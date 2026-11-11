"""Persistent settings (JSON in ~/.config/__APP_NAME__)."""
from __future__ import annotations

import json
import os
# droopy:feature history begin
import time
# droopy:feature history end
from pathlib import Path
from typing import Any

from .core import OPTION_DEFAULTS

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "__APP_NAME__"

DEFAULTS: dict[str, Any] = {
    "outputMode": "source",     # source (next to the original) | custom
    "customDir": "",
    "overwrite": "rename",      # rename | overwrite
    # droopy:feature delete begin
    "deleteMode": "ask",        # ask | never | always  (delete the original after success)
    "useTrash": True,
    # droopy:feature delete end
    "theme": "auto",            # auto (follow system) | light | dark
    "lowPower": False,          # calmer background animation
    "lastDir": "",              # last folder something was dropped from
    **OPTION_DEFAULTS,
}

# droopy:feature history begin
HISTORY_LIMIT = 300
# droopy:feature history end


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write(path: Path, data) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


class Store:
    def __init__(self) -> None:
        self.settings_path = CONFIG_DIR / "settings.json"
        self.data: dict[str, Any] = {**DEFAULTS}
        loaded = _read(self.settings_path, {})
        if isinstance(loaded, dict):
            self.data.update({k: v for k, v in loaded.items() if k in DEFAULTS})
        # droopy:feature history begin
        self.history_path = CONFIG_DIR / "history.json"
        hist = _read(self.history_path, [])
        self.history: list[dict[str, Any]] = hist if isinstance(hist, list) else []
        # droopy:feature history end

    def set(self, key: str, value: Any) -> bool:
        if key not in DEFAULTS or self.data.get(key) == value:
            return False
        self.data[key] = value
        _write(self.settings_path, self.data)
        return True

    # droopy:feature history begin
    def add_history(self, source: str, output: str, status: str) -> None:
        self.history.append({"source": source, "output": output, "status": status,
                             "time": int(time.time())})
        del self.history[:-HISTORY_LIMIT]
        _write(self.history_path, self.history)

    def clear_history(self) -> None:
        self.history = []
        _write(self.history_path, self.history)
    # droopy:feature history end
