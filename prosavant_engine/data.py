"""Data discovery and loading utilities for structured Savant datasets."""

from __future__ import annotations

import csv
import json
import os
import pickle
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - pandas is optional at runtime
    import pandas as pd
except Exception:  # pragma: no cover - gracefully degrade when pandas missing
    pd = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from huggingface_hub import snapshot_download
except Exception:  # pragma: no cover - keep optional
    snapshot_download = None  # type: ignore[assignment]

DEFAULT_POSSIBLE_PATHS: tuple[str, ...] = (
    "/content/drive/MyDrive/savant_rrf1/data",
    "/content/drive/MyDrive/savant_rrf1",
    "/content/drive/MyDrive/csv files_20251002_191151",
    "/content/drive/MyDrive/json_jsonl_files_20251002_191151",
)

ENV_BASE_PATH = "SAVANT_DATA_PATH"
ENV_REMOTE_DATASET = "SAVANT_REMOTE_DATASET"
DEFAULT_CACHE_DIR = str(Path.home() / ".cache" / "prosavant" / "datasets")
STRUCTURED_MARKERS = (
    "equations.json",
    "icosahedron_nodes.json",
    "frequencies.csv",
    "constants.csv",
)

EQUATIONS_BASENAMES = ("equations.json", "dataset_rrf.json", "icosahedron_nodes.json")
ICOSAHEDRON_NODES_BASENAMES = ("icosahedron_nodes.json", "nodes_icosahedron.json")
DODECA_NODES_BASENAMES = ("nodes_dodecahedron.json",)
FREQUENCIES_BASENAMES = ("frequencies.csv",)
CONSTANTS_BASENAMES = ("constants.csv",)
FULL_MEMORY_BASENAMES = ("full_fractal_memory.pkl",)


@dataclass
class DataRepository:
    """Locate structured CSV/JSON artefacts regardless of runtime."""

    base_path: Optional[Path | str] = None
    additional_paths: tuple[str, ...] = ()
    remote_dataset: Optional[str] = None
    cache_dir: str = DEFAULT_CACHE_DIR
    log_filename: str = "omega_log.jsonl"

    def __post_init__(self) -> None:
        self.base_path = self._initial_base_path()
        if self.base_path is None and self.remote_dataset:
            self.base_path = self._download_remote_dataset(self.remote_dataset)

    def _initial_base_path(self) -> Optional[Path]:
        if self.base_path:
            candidate = Path(self.base_path).expanduser()
            if candidate.exists():
                return candidate

        # explicit env variable wins
        env = (
            os.getenv("SAVANT_RRF_DATA_DIR")
            or os.getenv("AGIRRF_DATA_DIR")
            or os.getenv(ENV_BASE_PATH)
        )
        if env:
            p = Path(env).expanduser()
            if p.exists():
                return p

        # try default candidates plus any additional hints
        search_roots = list(DEFAULT_POSSIBLE_PATHS)
        if self.additional_paths:
            search_roots.extend(self.additional_paths)

        for raw in search_roots:
            p = Path(raw).expanduser()
            if p.exists():
                return p

        # as last resort, look for data/ directory next to this file
        repo_root = Path(__file__).resolve().parent.parent
        candidate = repo_root / "data"
        return candidate if candidate.exists() else None

    def _resolve_first_existing(self, *names: str) -> Optional[Path]:
        if self.base_path is None:
            return None

        search_dirs = [self.base_path]

        # if base path is savant_rrf1 or data, also look into sibling csv/json dirs
        root = self.base_path
        if root.name == "data":
            drive_root = root.parent
        else:
            drive_root = root

        drive_candidates = [
            drive_root / "data",
            drive_root,
            Path("/content/drive/MyDrive") / "csv files_20251002_191151",
            Path("/content/drive/MyDrive") / "json_jsonl_files_20251002_191151",
            Path("/content/drive/MyDrive") / "pkl files_20251002_191151",
        ]
        for d in drive_candidates:
            if d.exists() and d not in search_dirs:
                search_dirs.append(d)

        for d in search_dirs:
            for name in names:
                candidate = d / name
                if candidate.exists():
                    return candidate
        return None

    def _download_remote_dataset(self, repo_id: str) -> Optional[Path]:
        if not repo_id:
            return None
        if snapshot_download is None:
            warnings.warn(
                "huggingface_hub is not installed; cannot download remote dataset",
                RuntimeWarning,
                stacklevel=2,
            )
            return None

        cache_dir = Path(self.cache_dir).expanduser()
        cache_dir.mkdir(parents=True, exist_ok=True)
        local_dir = cache_dir / repo_id.replace("/", "__")
        try:
            snapshot_path = snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                local_dir=str(local_dir),
            )
        except Exception as exc:  # pragma: no cover - runtime network errors
            warnings.warn(
                f"Failed to download dataset '{repo_id}': {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            return None

        structured_root = self._locate_structured_root(Path(snapshot_path))
        return structured_root or Path(snapshot_path)

    def _locate_structured_root(self, root: Path) -> Optional[Path]:
        markers = set(STRUCTURED_MARKERS)
        for current, _dirs, files in os.walk(root):
            if markers.intersection(files):
                return Path(current)
        return None

    def load_equations(self) -> List[Dict[str, Any]]:
        path = self._resolve_first_existing(*EQUATIONS_BASENAMES)
        if not path:
            return []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # handle different schemas
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "ecuaciones" in data:
                return data["ecuaciones"]
            if "ecuaciones_maestras" in data:
                return data["ecuaciones_maestras"]
        return []

    def load_icosahedron_nodes(self) -> List[Dict[str, Any]]:
        path = self._resolve_first_existing(*ICOSAHEDRON_NODES_BASENAMES)
        if not path:
            return []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "nodes" in data:
            return data["nodes"]
        if isinstance(data, list):
            return data
        return []

    def load_dodecahedron_nodes(self) -> List[Dict[str, Any]]:
        path = self._resolve_first_existing(*DODECA_NODES_BASENAMES)
        if not path:
            return []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("nodes", data) if isinstance(data, dict) else data

    def _load_csv(self, *names: str) -> List[Dict[str, Any]]:
        path = self._resolve_first_existing(*names)
        if not path:
            return []
        if pd is None:
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader]
        df = pd.read_csv(path)
        return df.to_dict(orient="records")

    def load_frequencies(self) -> List[Dict[str, Any]]:
        return self._load_csv(*FREQUENCIES_BASENAMES)

    def load_constants(self) -> List[Dict[str, Any]]:
        return self._load_csv(*CONSTANTS_BASENAMES)

    def load_full_fractal_memory(self) -> Any:
        path = self._resolve_first_existing(*FULL_MEMORY_BASENAMES)
        if not path:
            return None
        with path.open("rb") as f:
            return pickle.load(f)

    def load_structured_bundle(self) -> Dict[str, Any]:
        return {
            "equations": self.load_equations(),
            "icosahedron_nodes": self.load_icosahedron_nodes(),
            "dodecahedron_nodes": self.load_dodecahedron_nodes(),
            "frequencies": self.load_frequencies(),
            "constants": self.load_constants(),
            "full_fractal_memory": self.load_full_fractal_memory(),
        }

    def load_structured(self) -> Dict[str, Any]:
        bundle = self.load_structured_bundle()
        return {
            "equations": bundle["equations"],
            "nodes": bundle["icosahedron_nodes"],
            "freq": bundle["frequencies"],
            "const": bundle["constants"],
        }

    def resolve_log_path(self) -> str:
        if self.base_path is not None:
            directory = self.base_path
        else:
            directory = Path.home() / ".prosavant"
        directory.mkdir(parents=True, exist_ok=True)
        return str(directory / self.log_filename)


__all__ = [
    "DataRepository",
    "DEFAULT_POSSIBLE_PATHS",
    "EQUATIONS_BASENAMES",
    "ICOSAHEDRON_NODES_BASENAMES",
    "DODECA_NODES_BASENAMES",
    "FREQUENCIES_BASENAMES",
    "CONSTANTS_BASENAMES",
    "FULL_MEMORY_BASENAMES",
]
