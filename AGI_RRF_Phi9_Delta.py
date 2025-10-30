"""Compatibility wrapper that exposes the original AGI–RRF entry point."""

from __future__ import annotations

from prosavant_engine import (
    AGIRRFCore,
    DEFAULT_MODEL_NAME,
    DEFAULT_SERVER_URI,
    DEFAULT_USER,
    VERSION,
    DiracHamiltonian,
    IcosahedralField,
    ResonanceSimulator,
    SelfImprover,
    harmonic_quantization,
    launch,
)
from prosavant_engine.networking import (
    listen_to_field,
    send_to_field,
    start_server,
    visualize_field,
)

__all__ = [
    "AGIRRFCore",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_SERVER_URI",
    "DEFAULT_USER",
    "VERSION",
    "DiracHamiltonian",
    "IcosahedralField",
    "ResonanceSimulator",
    "SelfImprover",
    "harmonic_quantization",
    "listen_to_field",
    "send_to_field",
    "start_server",
    "visualize_field",
    "launch",
]


if __name__ == "__main__":
    launch()
