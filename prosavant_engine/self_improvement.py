"""Adaptive coherence management for the Savant self-improver."""

from __future__ import annotations

import numpy as np


class SelfImprover:
    """Smoothly adjusts the coherence metric based on Hamiltonian energy."""

    def __init__(
        self,
        base_coherence: float = 0.8,
        smoothing: float = 0.1,
        energy_scale: float = 1e5,
    ) -> None:
        self.counter = 0
        self.coherence = base_coherence
        self.smoothing = smoothing
        self.energy_scale = energy_scale

    def update(self, hamiltonian_energy: float) -> float:
        """Update coherence using a scaled tanh response."""

        self.counter += 1
        scaled = np.tanh(abs(hamiltonian_energy) / self.energy_scale)
        target = 0.5 + 0.5 * scaled
        self.coherence = (1 - self.smoothing) * self.coherence + self.smoothing * float(target)
        if self.counter % 10 == 0:
            print(f"🧬 Coherence adjusted → {self.coherence:.3f}")
        return self.coherence


__all__ = ["SelfImprover"]
