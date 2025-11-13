"""Utilities for configuring the data repository inside Google Colab."""

from __future__ import annotations

import os
import warnings
from typing import Iterable, Optional, Sequence

from .data import (
    DataRepository,
    DEFAULT_CACHE_DIR,
    DEFAULT_POSSIBLE_PATHS,
    ENV_BASE_PATH,
    ENV_REMOTE_DATASET,
)

try:  # pragma: no cover - optional dependency available only on Colab
    from google.colab import drive as _colab_drive  # type: ignore
except Exception:  # pragma: no cover - keep import lightweight elsewhere
    _colab_drive = None  # type: ignore[assignment]

COLAB_DRIVE_MOUNT_POINT = "/content/drive"
COLAB_DEFAULT_SUBDIRS: tuple[str, ...] = (
    "MyDrive/savant_rrf1",
    "MyDrive/SAVANT_CORE",
    "MyDrive/SavantRRF",
)


def _drive_subdir_paths(root: str, subdirs: Sequence[str]) -> list[str]:
    return [os.path.join(root, subdir) for subdir in subdirs]


def mount_google_drive(
    mount_point: str = COLAB_DRIVE_MOUNT_POINT,
    *,
    force_remount: bool = False,
) -> str:
    """Ensure Google Drive is mounted and return the root path."""

    if _colab_drive is None:
        raise RuntimeError(
            "google.colab is not available. This helper must be executed inside a Colab runtime.",
        )

    mydrive = os.path.join(mount_point, "MyDrive")
    if not os.path.exists(mydrive) or force_remount:
        _colab_drive.mount(mount_point, force_remount=force_remount)
    return mount_point


def setup_data_repository(
    *,
    remote_dataset: Optional[str] = None,
    additional_paths: Optional[Iterable[str]] = None,
    mount_drive: bool = True,
    force_drive_remount: bool = False,
    cache_dir: Optional[str] = None,
    strict: bool = False,
) -> DataRepository:
    """Create a :class:`~prosavant_engine.data.DataRepository` configured for Colab."""

    possible_paths: list[str] = list(DEFAULT_POSSIBLE_PATHS)

    if mount_drive:
        try:
            drive_root = mount_google_drive(force_remount=force_drive_remount)
        except RuntimeError:
            drive_root = None
        else:
            possible_paths = _drive_subdir_paths(drive_root, COLAB_DEFAULT_SUBDIRS) + possible_paths

    if additional_paths:
        possible_paths.extend(additional_paths)

    # Remove duplicates while preserving ordering
    unique_paths = list(dict.fromkeys(possible_paths))

    repository = DataRepository(
        base_path=os.getenv(ENV_BASE_PATH),
        additional_paths=tuple(unique_paths),
        remote_dataset=remote_dataset or os.getenv(ENV_REMOTE_DATASET),
        cache_dir=cache_dir or DEFAULT_CACHE_DIR,
    )

    if repository.base_path is None:
        message = (
            "Could not locate the structured dataset. Upload it to Google Drive or set"
            f" {ENV_REMOTE_DATASET}=<namespace/dataset> to trigger a Hugging Face download."
        )
        if repository.remote_dataset:
            message += (
                " Ensure the `huggingface-hub` package is installed in the runtime and that"
                " your token has permission to access the dataset."
            )
        if strict:
            raise FileNotFoundError(message)
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        raise FileNotFoundError(message)

    return repository


__all__ = [
    "COLAB_DRIVE_MOUNT_POINT",
    "COLAB_DEFAULT_SUBDIRS",
    "mount_google_drive",
    "setup_data_repository",
]
