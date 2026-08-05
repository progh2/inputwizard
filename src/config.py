import json
import sys
from pathlib import Path


def _config_path() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "InputWizard"
    elif sys.platform == "win32":
        base = Path.home() / "AppData" / "Roaming" / "InputWizard"
    else:
        base = Path.home() / ".config" / "inputwizard"
    base.mkdir(parents=True, exist_ok=True)
    return base / "config.json"


_DEFAULTS = {
    "x": 100,
    "y": 100,
    "scroll_ticks": 3,
    "always_on_top": True,
}


def load() -> dict:
    path = _config_path()
    if not path.exists():
        return dict(_DEFAULTS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {**_DEFAULTS, **data}
    except Exception:
        return dict(_DEFAULTS)


def save(data: dict) -> None:
    _config_path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
