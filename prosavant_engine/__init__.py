"""Prosavant Engine package exposing the AGI RRF core primitives."""

from .config import VERSION, DEFAULT_MODEL_NAME, DEFAULT_SERVER_URI, DEFAULT_USER
from .geometry import IcosahedralField
from .physics import DiracHamiltonian
from .resonance import ResonanceSimulator, harmonic_quantization
from .self_improvement import SelfImprover
from .core import AGIRRFCore
from .main import launch

__all__ = [
    "VERSION",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_SERVER_URI",
    "DEFAULT_USER",
    "IcosahedralField",
    "DiracHamiltonian",
    "ResonanceSimulator",
    "harmonic_quantization",
    "SelfImprover",
    "AGIRRFCore",
    "launch",
]
