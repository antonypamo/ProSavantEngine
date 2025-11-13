"""Shared helper utilities for lightweight tensor munging."""

from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike


def _hash_to_unit_vector(text: str) -> np.ndarray:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    ints = np.frombuffer(digest, dtype=np.uint32)
    vec = ints[:3].astype(np.float64)
    max_uint = np.iinfo(np.uint32).max
    if max_uint:
        vec /= max_uint
    return vec


def to_psi3(value: ArrayLike | Iterable[float] | float | int | str | None) -> np.ndarray:
    """Map arbitrary inputs into a 3-component numpy vector.

    Strings are deterministically hashed, scalars are broadcast, and longer arrays
    are truncated. Short arrays are zero-padded.
    """

    if isinstance(value, str):
        arr = _hash_to_unit_vector(value)
    elif value is None:
        arr = np.zeros(3, dtype=np.float64)
    else:
        arr = np.asarray(value, dtype=np.float64).ravel()

    if arr.size == 0:
        arr = np.zeros(3, dtype=np.float64)
    elif arr.size < 3:
        arr = np.pad(arr, (0, 3 - arr.size), mode="constant")
    elif arr.size > 3:
        arr = arr[:3]

    return arr.astype(np.float64, copy=False)


__all__ = ["to_psi3"]
