"""Dirac Hamiltonian dynamics used by the core system."""

from __future__ import annotations

import numpy as np

from .geometry import IcosahedralField
from .utils import to_psi3


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
