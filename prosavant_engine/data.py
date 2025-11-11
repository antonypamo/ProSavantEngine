"""Data discovery and loading utilities for structured Savant datasets."""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

try:  # pragma: no cover - optional dependency
    from huggingface_hub import snapshot_download
except Exception:  # pragma: no cover - safety net for partial installs
    snapshot_download = None  # type: ignore[assignment]


ENV_BASE_PATH = "SAVANT_DATA_PATH"
ENV_REMOTE_DATASET = "SAVANT_REMOTE_DATASET"
DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "prosavant", "datasets")
STRUCTURED_MARKERS: tuple[str, ...] = (
    "equations.json",
    "icosahedron_nodes.json",
    "frequencies.csv",
    "constants.csv",
)
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
    remote_dataset: Optional[str] = None
    cache_dir: str = DEFAULT_CACHE_DIR
    log_filename: str = "omega_log.jsonl"
    remote_repo: Optional[str] = None
    remote_revision: Optional[str] = None
    remote_subdir: Optional[str] = None
    cache_dir: Optional[str] = None

    def __post_init__(self) -> None:
        self.base_path = self._initial_base_path()
        if self.base_path is None and self.remote_dataset:
            self.base_path = self._download_remote_dataset(self.remote_dataset)

    def _initial_base_path(self) -> Optional[str]:
        """Determine the starting base path, considering env vars and fallbacks."""

        if self.base_path and os.path.exists(self.base_path):
            return self.base_path

        env_base = os.getenv(ENV_BASE_PATH)
        if env_base and os.path.exists(env_base):
            return env_base

        if self.remote_dataset is None:
            env_remote = os.getenv(ENV_REMOTE_DATASET)
            if env_remote:
                self.remote_dataset = env_remote

        detected = self._detect_base_path()
        if detected:
            return detected

        return None
        self.remote_repo = self.remote_repo or os.getenv("SAVANT_REMOTE_DATASET") or None
        self.remote_revision = self.remote_revision or os.getenv("SAVANT_REMOTE_DATASET_REVISION") or None
        self.remote_subdir = self.remote_subdir or os.getenv("SAVANT_REMOTE_DATASET_SUBDIR") or None
        self.cache_dir = self.cache_dir or os.getenv("SAVANT_DATASET_CACHE_DIR") or None

        if self.base_path is None and self.remote_repo:
            self.base_path = self._download_remote_dataset(
                repo_id=self.remote_repo,
                revision=self.remote_revision,
                subdir=self.remote_subdir,
                cache_dir=self.cache_dir,
            )

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

    # ------------------------------------------------------------------
    # Remote dataset support
    # ------------------------------------------------------------------

    def _download_remote_dataset(self, repo_id: str) -> Optional[str]:
        """Download a remote dataset via ``huggingface_hub`` when available."""

        if not repo_id:
            return None

        if snapshot_download is None:
            warnings.warn(
                "huggingface_hub is not installed; cannot download remote dataset",
                RuntimeWarning,
                stacklevel=2,
            )
            return None

        cache_dir = Path(self.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        local_dir = cache_dir / repo_id.replace("/", "__")

        try:
            snapshot_path = snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                local_dir=str(local_dir),
            )
        except Exception as exc:  # pragma: no cover - network errors at runtime
            warnings.warn(
                f"Failed to download dataset '{repo_id}': {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            return None

        structured_root = self._locate_structured_root(snapshot_path)
        return structured_root or snapshot_path

    def _locate_structured_root(self, root: str) -> Optional[str]:
        """Search ``root`` for a directory containing structured data markers."""

        markers = set(STRUCTURED_MARKERS)
        for current, _dirs, files in os.walk(root):
            if markers.intersection(files):
                return current
        return None
    def _download_remote_dataset(
        self,
        *,
        repo_id: str,
        revision: Optional[str],
        subdir: Optional[str],
        cache_dir: Optional[str],
    ) -> Optional[str]:
        """Download a dataset snapshot from the Hugging Face Hub."""

        hub_spec = importlib.util.find_spec("huggingface_hub")
        if hub_spec is None:
            raise RuntimeError(
                "Remote dataset support requires the 'huggingface-hub' package."
            )

        from huggingface_hub import snapshot_download

        target_cache = cache_dir
        if target_cache is None:
            safe_repo = repo_id.replace("/", "__")
            target_cache = os.path.join(
                os.path.expanduser("~"),
                ".prosavant",
                "datasets",
                safe_repo,
            )
        os.makedirs(target_cache, exist_ok=True)

        download_kwargs = {
            "repo_id": repo_id,
            "repo_type": "dataset",
            "local_dir": target_cache,
        }
        if revision:
            download_kwargs["revision"] = revision

        dataset_path = snapshot_download(**download_kwargs)

        candidate_paths = [dataset_path]
        if subdir:
            candidate_paths.append(os.path.join(dataset_path, subdir))
        candidate_paths.extend(
            [
                os.path.join(dataset_path, "data"),
                os.path.join(dataset_path, repo_id.split("/")[-1]),
            ]
        )

        for candidate in candidate_paths:
            if candidate and os.path.exists(candidate):
                return candidate
        return dataset_path

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


__all__ = [
    "DataRepository",
    "DEFAULT_POSSIBLE_PATHS",
    "STRUCTURED_MARKERS",
    "ENV_BASE_PATH",
    "ENV_REMOTE_DATASET",
]
