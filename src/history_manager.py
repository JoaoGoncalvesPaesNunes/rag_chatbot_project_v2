from __future__ import annotations

from pathlib import Path
from typing import Dict

from src.utils import append_json_list


class HistoryManager:
    def __init__(self, history_path: Path):
        self.history_path = history_path

    def save_interaction(self, record: Dict) -> None:
        append_json_list(self.history_path, record)
