"""Dirac Hamiltonian dynamics used by the core system."""

from __future__ import annotations

import numpy as np

from .geometry import IcosahedralField


class DiracHamiltonian:
    """Simplified discrete Hamiltonian operating on resonance output."""

    def __init__(self, field: IcosahedralField) -> None:
        self.field = field
        self.m = 1.0
        self.gamma = np.eye(3)

    def H(self, psi: np.ndarray) -> float:
        """Compute the Hamiltonian energy for the provided wavefunction."""

        d = float(np.linalg.norm(psi))
        V = self.field.V_log(d)
        kinetic = float(np.sum(psi.T @ (self.gamma @ psi)))
        mass_term = self.m * float(np.sum(psi))
        return kinetic + mass_term + V


__all__ = ["DiracHamiltonian"]
