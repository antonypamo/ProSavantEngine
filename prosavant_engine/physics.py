"""Dirac Hamiltonian dynamics used by the core system."""

from __future__ import annotations

import numpy as np

from .geometry import IcosahedralField


class DiracHamiltonian:
    """Simplified discrete Hamiltonian operating on resonance output."""

    def __init__(self, field: IcosahedralField) -> None:
        self.field = field
        self.m = 1.0
        # Start with a small identity metric; it will be resized on demand.
        self.gamma = np.eye(1)

    def H(self, psi: np.ndarray) -> float:
        """Compute the Hamiltonian energy for the provided wavefunction."""

        psi = np.asarray(psi, dtype=float).reshape(-1)
        if psi.size == 0:
            raise ValueError("psi must contain at least one component")

        if self.gamma.shape[0] != psi.size:
            # Promote the gamma matrix to match the incoming wavefunction dimension.
            self.gamma = np.eye(psi.size)

        d = float(np.linalg.norm(psi))
        V = self.field.V_log(d)
        kinetic = float(np.sum(psi.T @ (self.gamma @ psi)))
        mass_term = self.m * float(np.sum(psi))
        return kinetic + mass_term + V


__all__ = ["DiracHamiltonian"]
