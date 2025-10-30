"""Primary AGI RRF controller wiring together all subsystems."""

from __future__ import annotations

from typing import Dict

import numpy as np

from .geometry import IcosahedralField
from .physics import DiracHamiltonian
from .resonance import ResonanceSimulator
from .self_improvement import SelfImprover


class AGIRRFCore:
    """Facade that exposes the text → resonance → response pipeline."""

    def __init__(self) -> None:
        self.field = IcosahedralField()
        self.hamiltonian = DiracHamiltonian(self.field)
        self.simulator = ResonanceSimulator()
        self.self_improver = SelfImprover()

    def query(self, text: str) -> Dict[str, float]:
        """Process *text* and return spectral and coherence metrics."""

        resonance = self.simulator.simulate(text)
        dominant_frequency = resonance["dominant_frequency"]
        hamiltonian_energy = self.hamiltonian.H(np.array([dominant_frequency]))
        coherence = self.self_improver.update(hamiltonian_energy)
        return {
            "input": text,
            "dominant_frequency": dominant_frequency,
            "hamiltonian_energy": hamiltonian_energy,
            "coherence": coherence,
        }


__all__ = ["AGIRRFCore"]
