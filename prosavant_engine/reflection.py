"""Ω-reflection logging utilities."""

from __future__ import annotations

import json
import os
import time
from typing import Dict, Iterable, List


class OmegaReflection:
    """Persistent logger for Φ/Ω resonance metrics."""

    def __init__(self, log_path: str) -> None:
        self.log_path = log_path
        directory = os.path.dirname(log_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def log(self, phi: float, omega: float) -> None:
        entry = {"time": time.time(), "phi": float(phi), "omega": float(omega)}
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

    def entries(self) -> List[Dict[str, float]]:
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def summarize(self) -> Dict[str, float | int]:
        records = self.entries()
        if not records:
            return {}
        phi_values = [float(item["phi"]) for item in records]
        omega_values = [float(item["omega"]) for item in records]
        count = len(records)
        return {
            "avg_phi": sum(phi_values) / count,
            "avg_omega": sum(omega_values) / count,
            "count": count,
        }

    def has_history(self) -> bool:
        return os.path.exists(self.log_path)

    def tail(self, limit: int = 50) -> Iterable[Dict[str, float]]:
        return self.entries()[-limit:]


__all__ = ["OmegaReflection"]
