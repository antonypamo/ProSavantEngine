"""Data discovery and loading utilities for structured Savant datasets."""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional

DEFAULT_POSSIBLE_PATHS: tuple[str, ...] = (
    "/content/drive/MyDrive/savant_rrf1/",
    "/content/drive/MyDrive/SAVANT_CORE/",
    "/content/drive/MyDrive/SavantRRF/",
)


@dataclass
class DataRepository:
    """Locate and load auxiliary structured data for the engine."""

    base_path: Optional[str] = None
    possible_paths: Iterable[str] = field(default_factory=lambda: DEFAULT_POSSIBLE_PATHS)
    log_filename: str = "omega_log.jsonl"

    def __post_init__(self) -> None:
        if self.base_path is None:
            self.base_path = self._detect_base_path()

    def _detect_base_path(self) -> Optional[str]:
        for path in self.possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _resolve(self, *parts: str) -> Optional[str]:
        if self.base_path is None:
            return None
        return os.path.join(self.base_path, *parts)

    def load_structured(self) -> Dict[str, Mapping[str, object] | List[Mapping[str, object]]]:
        """Load JSON/CSV structured data when available."""

        data: Dict[str, Mapping[str, object] | List[Mapping[str, object]]] = {}
        data["equations"] = self._load_json("equations.json")
        data["nodes"] = self._load_json("icosahedron_nodes.json")
        data["freq"] = self._load_csv("frequencies.csv")
        data["const"] = self._load_csv("constants.csv")
        return data

    def _load_json(self, filename: str) -> Mapping[str, object]:
        path = self._resolve(filename)
        if not path or not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _load_csv(self, filename: str) -> List[Mapping[str, object]]:
        path = self._resolve(filename)
        if not path or not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]

    def resolve_log_path(self) -> str:
        """Return a writable path for Ω-reflection logging."""

        if self.base_path:
            directory = self.base_path
        else:
            directory = os.path.join(os.path.expanduser("~"), ".prosavant")
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, self.log_filename)


__all__ = ["DataRepository", "DEFAULT_POSSIBLE_PATHS"]
