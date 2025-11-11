"""Primary AGI RRF controller wiring together all subsystems."""

from __future__ import annotations

import asyncio
from typing import Dict

import numpy as np
import plotly.graph_objects as go

from .geometry import IcosahedralField
from .utils import to_psi3
from .physics import DiracHamiltonian
from .resonance import ResonanceSimulator
from .self_improvement import SelfImprover
from .data import DataRepository
from .reflection import OmegaReflection


class AGIRRFCore:
    """Facade that exposes the text → resonance → response pipeline."""

    def __init__(self, *, data_repository: DataRepository | None = None) -> None:
        self.field = IcosahedralField()
        self.hamiltonian = DiracHamiltonian(self.field)
        self.simulator = ResonanceSimulator()
        self.self_improver = SelfImprover()
        self.data_repository = data_repository or DataRepository()
        self.structured_data = self.data_repository.load_structured()
        self.omega_reflection = OmegaReflection(self.data_repository.resolve_log_path())

    def query(self, text: str) -> Dict[str, float]:
        """Process *text* and return spectral and coherence metrics."""

        resonance = self.simulator.simulate(text)
        dominant_frequency = resonance["dominant_frequency"]
        # Map the resonance embedding (or the dominant frequency) to the
        # 3-component psi expected by the Hamiltonian using a shared helper.
        psi_source = resonance.get("embedding", np.array([dominant_frequency]))
        psi = to_psi3(psi_source)
        hamiltonian_energy = self.hamiltonian.H(psi)
        coherence = self.self_improver.update(hamiltonian_energy)
        phi = float(np.tanh(abs(hamiltonian_energy) * 1e-6))
        omega = float(np.tanh(dominant_frequency / 1000.0))
        self.omega_reflection.log(phi, omega)
        return {
            "input": text,
            "dominant_frequency": dominant_frequency,
            "hamiltonian_energy": hamiltonian_energy,
            "coherence": coherence,
            "phi": phi,
            "omega": omega,
        }

    def omega_summary(self) -> Dict[str, float | int]:
        """Return aggregate Φ/Ω statistics from the reflection log."""

        return self.omega_reflection.summarize()

    def visualize_phi_omega(self) -> go.Figure:
        """Render a 3D trajectory of Φ/Ω over time."""

        entries = list(self.omega_reflection.tail())
        if len(entries) < 2:
            return go.Figure()
        times = [entry["time"] for entry in entries]
        phi_values = [entry["phi"] for entry in entries]
        omega_values = [entry["omega"] for entry in entries]
        figure = go.Figure(
            data=[
                go.Scatter3d(
                    x=times,
                    y=phi_values,
                    z=omega_values,
                    mode="lines+markers",
                )
            ]
        )
        figure.update_layout(
            title="Φ-Ω Trajectory",
            scene=dict(xaxis_title="Time", yaxis_title="Φ", zaxis_title="Ω"),
        )
        return figure

    async def auto_reflect(self, text: str = "Quantum resonance unification", steps: int = 10, delay: float = 1.0) -> None:
        """Continuously query the core and log Φ/Ω dynamics."""

        for index in range(steps):
            result = self.query(f"{text} #{index}")
            print(
                f"Iteration {index + 1}: Φ={result['phi']:.4f}, Ω={result['omega']:.4f}"
            )
            await asyncio.sleep(delay)


__all__ = ["AGIRRFCore"]
