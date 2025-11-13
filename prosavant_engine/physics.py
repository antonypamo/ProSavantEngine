"""Dirac Hamiltonian dynamics used by the core system."""

from __future__ import annotations
from .geometry import IcosahedralField

# Prefer the Colab helper if available; otherwise define a local fallback.
try:
    # Old notebooks/helpers may define a vector-based to_psi3 in colab_utils
    from .colab_utils import to_psi3  # type: ignore[attr-defined]
except Exception:
    import numpy as _np
    from typing import Iterable as _Iterable, Union as _Union

    _ArrayLike = _Union[_np.ndarray, _Iterable[float]]

    def to_psi3(vec: _ArrayLike) -> _np.ndarray:
        """
        Map an arbitrary 1D/2D vector into a 3D psi vector compatible with
        DiracHamiltonian.

        - If dim >= 3, take the first 3 components.
        - If dim < 3, pad with zeros.
        - If a batch is provided (2D), use the first row.
        """
        arr = _np.asarray(vec, dtype=_np.float32)

        if arr.ndim == 2:
            if arr.shape[0] == 0:
                raise ValueError("to_psi3: empty batch")
            arr = arr[0]

        if arr.ndim != 1:
            raise ValueError(f"to_psi3 expects a 1D vector or 2D batch, got {arr.shape}")

        if arr.shape[0] >= 3:
            return arr[:3].copy()

        out = _np.zeros(3, dtype=_np.float32)
        out[: arr.shape[0]] = arr
        return out

import numpy as np

class DiracHamiltonian:
    """Simplified discrete Hamiltonian operating on resonance output."""

    def __init__(self, field: IcosahedralField) -> None:
        self.field = field
        self.m = 1.0
        self.gamma = np.eye(3)

    def H(self, psi: np.ndarray) -> float:
        """Compute the Hamiltonian energy for the provided wavefunction."""

        # Accept variable-length inputs by mapping into a 3-component psi.
        psi3 = to_psi3(psi)

        d = float(np.linalg.norm(psi3))
        V = self.field.V_log(d)
        # kinetic term: <psi | gamma | psi>
        kinetic = float(np.sum(psi3.T @ (self.gamma @ psi3)))
        mass_term = self.m * float(np.sum(psi3))
        return kinetic + mass_term + V


__all__ = ["DiracHamiltonian"]
