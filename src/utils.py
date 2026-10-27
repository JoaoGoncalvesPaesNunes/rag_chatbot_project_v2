from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return datetime.utcnow().isoformat(timespec='seconds') + 'Z'


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9._-]+', '_', name.strip())
    return name.strip('._') or 'documento'


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return [] if default is None else default
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def append_json_list(path: Path, item: Any) -> None:
    data = read_json(path, default=[])
    if not isinstance(data, list):
        data = []
    data.append(item)
    write_json(path, data)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
