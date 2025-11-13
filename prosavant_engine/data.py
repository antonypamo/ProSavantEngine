"""Data discovery and loading utilities for structured Savant / RRF datasets."""

from __future__ import annotations

import csv
import json
import os
import pickle
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # pandas is optional at runtime
    import pandas as pd  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    pd = None  # type: ignore[assignment]

try:  # huggingface_hub is optional
    from huggingface_hub import snapshot_download  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    snapshot_download = None  # type: ignore[assignment]

DEFAULT_POSSIBLE_PATHS: tuple[str, ...] = (
    "/content/drive/MyDrive/savant_rrf1/data",
    "/content/drive/MyDrive/savant_rrf1",
    "/content/drive/MyDrive/csv files_20251002_191151",
    "/content/drive/MyDrive/json_jsonl_files_20251002_191151",
)

# ---------------------------------------------------------------------------
# Canonical layout (taken from 3.oSA structured_data_paths and your folders)
# ---------------------------------------------------------------------------

ENV_BASE_PATH = "SAVANT_DATA_PATH"
ENV_REMOTE_DATASET = "SAVANT_REMOTE_DATASET"
DEFAULT_CACHE_DIR = str(Path.home() / ".cache" / "prosavant" / "datasets")

# Drive layout you actually use
DEFAULT_POSSIBLE_PATHS: tuple[str, ...] = (
    "/content/drive/MyDrive/savant_rrf1/data",                    # preferred root
    "/content/drive/MyDrive/savant_rrf1",                         # original root
    "/content/drive/MyDrive/csv files_20251002_191151",           # extra CSVs
    "/content/drive/MyDrive/json_jsonl_files_20251002_191151",    # extra JSON/JSONL
    "/content/drive/MyDrive/pkl files_20251002_191151",           # full_fractal_memory.pkl
)

# Any directory containing these is considered a structured-data root
STRUCTURED_MARKERS = (
    "equations.json",
    "icosahedron_nodes.json",
    "frequencies.csv",
    "constants.csv",
)

# Filenames we’ll try, in order, for each logical asset
EQUATIONS_BASENAMES = (
    "equations.json",          # main file from structured_data_paths
    "dataset_rrf.json",        # alternative dataset file if you add it later
    "icosahedron_nodes.json",  # last resort: take ecuaciones from here
)
ICOSAHEDRON_NODES_BASENAMES = (
    "icosahedron_nodes.json",  # canonical nodes file
    "nodes_icosahedron.json",  # legacy fallback
)
DODECA_NODES_BASENAMES = (
    "nodes_dodecahedron.json",  # as in structured_data_paths
    "dodecahedron_nodes.json",  # possible alternative name
)
FREQUENCIES_BASENAMES = ("frequencies.csv",)
CONSTANTS_BASENAMES = ("constants.csv",)
FULL_MEMORY_BASENAMES = ("full_fractal_memory.pkl",)


@dataclass
class DataRepository:
    """
    Locate and load auxiliary structured data for the AGI–RRF / Savant engine.

    This class is wired to the SAME layout as your one-click SavantEngine cell:
      - equations.json
      - icosahedron_nodes.json
      - nodes_dodecahedron.json
      - frequencies.csv
      - constants.csv
      - full_fractal_memory.pkl
    living under /content/drive/MyDrive/savant_rrf1 and sibling folders.
    """

    base_path: Optional[Path | str] = None
    additional_paths: tuple[str, ...] = ()
    remote_dataset: Optional[str] = None
    cache_dir: str = DEFAULT_CACHE_DIR
    log_filename: str = "omega_log.jsonl"

    def __post_init__(self) -> None:
        self.base_path = self._initial_base_path()
        if self.base_path is None and self.remote_dataset:
            self.base_path = self._download_remote_dataset(self.remote_dataset)

    # ------------------------------------------------------------------
    # Base path resolution
    # ------------------------------------------------------------------

    def _initial_base_path(self) -> Optional[Path]:
        """
        Choose a base path using:
        1. Explicit base_path argument (if exists)
        2. Env vars: RRF_DATA_ROOT / SAVANT_RRF_DATA_DIR / AGIRRF_DATA_DIR / SAVANT_DATA_PATH
        3. DEFAULT_POSSIBLE_PATHS
        4. repo_root/data as a last local fallback
        """
        # 1) explicit override
        if self.base_path:
            candidate = Path(self.base_path).expanduser()
            if candidate.exists():
                return candidate

        # 2) env overrides used across your notebooks/scripts
        env = (
            os.getenv("RRF_DATA_ROOT")
            or os.getenv("SAVANT_RRF_DATA_DIR")
            or os.getenv("AGIRRF_DATA_DIR")
            or os.getenv(ENV_BASE_PATH)
        )
        if env:
            p = Path(env).expanduser()
            if p.exists():
                return p

        # 3) drive defaults + additional hints
        search_roots: List[str] = list(DEFAULT_POSSIBLE_PATHS)
        if self.additional_paths:
            search_roots.extend(self.additional_paths)

        for raw in search_roots:
            p = Path(raw).expanduser()
            if p.exists():
                return p

        # 4) repo-local data/ as a last resort
        repo_root = Path(__file__).resolve().parent.parent
        candidate = repo_root / "data"
        return candidate if candidate.exists() else None

    def _candidate_roots(self) -> List[Path]:
        """
        Build an ordered list of directories to search for structured files.
        """
        roots: List[Path] = []

        if self.base_path is not None:
            bp = Path(self.base_path).expanduser()
            roots.append(bp)
            roots.append(bp / "data")
            roots.append(bp / "datasets")

            # If base_path is savant_rrf1 root, include its siblings:
            drive_root = bp.parent if bp.name == "data" else bp
        else:
            drive_root = Path("/content/drive/MyDrive")

        drive_candidates = [
            drive_root,
            drive_root / "data",
            drive_root / "datasets",
            Path("/content/drive/MyDrive") / "csv files_20251002_191151",
            Path("/content/drive/MyDrive") / "json_jsonl_files_20251002_191151",
            Path("/content/drive/MyDrive") / "pkl files_20251002_191151",
        ]

        for raw in DEFAULT_POSSIBLE_PATHS:
            roots.append(Path(raw).expanduser())

        for d in drive_candidates:
            roots.append(d)

        # de-duplicate while preserving order
        uniq: List[Path] = []
        seen = set()
        for r in roots:
            r = r.expanduser()
            key = r.resolve()
            if key not in seen:
                uniq.append(r)
                seen.add(key)
        return uniq

    def _resolve_first_existing(self, *names: str) -> Optional[Path]:
        if not names:
            return None
        for root in self._candidate_roots():
            for name in names:
                candidate = root / name
                if candidate.is_file():
                    return candidate
        return None

    # ------------------------------------------------------------------
    # Remote dataset support via Hugging Face Hub (optional)
    # ------------------------------------------------------------------

    def _download_remote_dataset(self, repo_id: str) -> Optional[Path]:
        """
        Download a remote dataset snapshot from the Hugging Face Hub and
        return a directory that contains our structured markers.
        """
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
        except Exception as exc:  # pragma: no cover
            warnings.warn(
                f"Failed to download dataset '{repo_id}': {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            return None

        structured_root = self._locate_structured_root(Path(snapshot_path))
        return structured_root or Path(snapshot_path)

    def _locate_structured_root(self, root: Path) -> Optional[Path]:
        """Search `root` for a directory containing structured data markers."""
        markers = set(STRUCTURED_MARKERS)
        for current, _dirs, files in os.walk(root):
            if markers.intersection(files):
                return Path(current)
        return None

    # ------------------------------------------------------------------
    # Typed loaders for your six core assets
    # ------------------------------------------------------------------

    def load_equations(self) -> List[Dict[str, Any]]:
        """
        Load equations as a list[dict] from:
          - equations.json           (preferred)
          - dataset_rrf.json         (optional)
          - icosahedron_nodes.json   (fallback: uses 'ecuaciones' field)
        """
        path = self._resolve_first_existing(*EQUATIONS_BASENAMES)
        if not path:
            return []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # matches icosahedron_nodes.json structure
            if "ecuaciones" in data:
                return data["ecuaciones"]
            if "ecuaciones_maestras" in data:
                return data["ecuaciones_maestras"]
        return []

    def load_icosahedron_nodes(self) -> List[Dict[str, Any]]:
        """
        Load icosahedral nodes as list[dict] with keys (id, x, y, z, ...).
        """
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
        """
        Load dodecahedral nodes if you provide a nodes_dodecahedron.json file.
        """
        path = self._resolve_first_existing(*DODECA_NODES_BASENAMES)
        if not path:
            return []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("nodes", data) if isinstance(data, dict) else data

    def _load_csv(self, *names: str) -> List[Dict[str, Any]]:
        """
        CSV loader that returns list[dict]. Uses pandas if available,
        otherwise csv.DictReader.
        """
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
        """
        Frequencies CSV → list of rows with keys e.g. 'note', 'frequency'.
        """
        return self._load_csv(*FREQUENCIES_BASENAMES)

    def load_constants(self) -> List[Dict[str, Any]]:
        """
        Constants CSV → list of rows with keys e.g. 'name', 'value'.
        """
        return self._load_csv(*CONSTANTS_BASENAMES)

    def load_full_fractal_memory(self) -> Any:
        """
        Load full_fractal_memory.pkl if available, otherwise return None.
        """
        path = self._resolve_first_existing(*FULL_MEMORY_BASENAMES)
        if not path:
            return None
        with path.open("rb") as f:
            return pickle.load(f)

    # ------------------------------------------------------------------
    # Bundles compatible with existing code
    # ------------------------------------------------------------------

    def load_structured_bundle(self) -> Dict[str, Any]:
        """
        Rich bundle used by AGI–RRF or Savant-style cores.
        """
        return {
            "equations": self.load_equations(),
            "icosahedron_nodes": self.load_icosahedron_nodes(),
            "dodecahedron_nodes": self.load_dodecahedron_nodes(),
            "frequencies": self.load_frequencies(),
            "constants": self.load_constants(),
            "full_fractal_memory": self.load_full_fractal_memory(),
        }

    def load_structured(self) -> Dict[str, Any]:
        """
        Backwards-compatible dict for older code that expects:
          - 'equations'
          - 'nodes' (icosa nodes)
          - 'freq'  (frequencies)
          - 'const' (constants)
        """
        bundle = self.load_structured_bundle()
        return {
            "equations": bundle["equations"],
            "nodes": bundle["icosahedron_nodes"],
            "freq": bundle["frequencies"],
            "const": bundle["constants"],
        }

    # ------------------------------------------------------------------
    # Ω-reflection log path
    # ------------------------------------------------------------------

    def resolve_log_path(self) -> str:
        """
        Return a writable path for Ω-reflection logging.

        If base_path is known, log next to the dataset; otherwise fall
        back to ~/.prosavant/omega_log.jsonl
        """
        if self.base_path is not None:
            directory = Path(self.base_path)
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
