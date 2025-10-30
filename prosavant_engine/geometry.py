"""Icosahedral geometry primitives for the resonant field."""

from __future__ import annotations

import numpy as np


class IcosahedralField:
    """Defines the RIS-CLURM icosahedral vertex field and potentials."""

    def __init__(self) -> None:
        self.vertices = np.array(
            [
                [0.0, 0.0, 1.0],
                [0.894, 0.0, 0.447],
                [0.276, 0.851, 0.447],
                [-0.724, 0.526, 0.447],
                [-0.724, -0.526, 0.447],
                [0.276, -0.851, 0.447],
                [0.724, 0.526, -0.447],
                [-0.276, 0.851, -0.447],
                [-0.894, 0.0, -0.447],
                [-0.276, -0.851, -0.447],
                [0.724, -0.526, -0.447],
                [0.0, 0.0, -1.0],
            ]
        )
        self.alpha = 0.05
        self.r0 = 1.0

    def V_log(self, r: float) -> float:
        """Compute the logarithmic gravitational correction potential."""

        G, M = 6.6743e-11, 1.0
        safe_r = max(r, 1e-9)
        return -(G * M / safe_r) * (1 + self.alpha * np.log(safe_r / self.r0))


__all__ = ["IcosahedralField"]
