"""Gradio interface helpers for the Prosavant Engine."""

from __future__ import annotations

import asyncio
from typing import Tuple

from .core import AGIRRFCore

try:  # pragma: no cover - optional dependency
    import gradio as gr
except ImportError:  # pragma: no cover - runtime guard
    gr = None  # type: ignore


class GradioUnavailableError(RuntimeError):
    """Raised when Gradio is requested but not installed."""


def _format_output(response: dict, summary: dict) -> str:
    lines = [
        f"Dominant Frequency: {response['dominant_frequency']:.3f} Hz",
        f"Φ: {response['phi']:.4f}",
        f"Ω: {response['omega']:.4f}",
        f"H: {response['hamiltonian_energy']:.3e}",
    ]
    if summary:
        lines.append("")
        lines.append("Session Summary:")
        lines.append(str(summary))
    return "\n".join(lines)


def build_interface(core: AGIRRFCore | None = None) -> "gr.Blocks":  # type: ignore[name-defined]
    """Construct the Gradio Blocks UI used in the Colab notebook."""

    if gr is None:
        raise GradioUnavailableError("Gradio is not installed. Install gradio to use the UI.")

    core = core or AGIRRFCore()

    def run_query(text: str) -> Tuple[str, object]:
        response = core.query(text)
        summary = core.omega_summary()
        figure = core.visualize_phi_omega()
        return _format_output(response, summary), figure

    def auto_run() -> Tuple[str, object]:
        asyncio.run(core.auto_reflect())
        return "Auto-reflect cycle completed.", core.visualize_phi_omega()

    with gr.Blocks(title="ProSavantEngine Φ9.1") as interface:
        gr.Markdown("## 🧬 ProSavantEngine Φ9.1 — Resonant Interface")
        txt = gr.Textbox(label="Prompt / Query")
        btn = gr.Button("Run Resonance Query")
        out_txt = gr.Textbox(label="Output")
        out_plot = gr.Plot(label="Φ-Ω Trajectory")
        btn.click(run_query, inputs=txt, outputs=[out_txt, out_plot])
        gr.Markdown("### Toggle Auto-Reflect Mode")
        auto_btn = gr.Button("Start Auto-Reflect (10 iterations)")
        auto_btn.click(auto_run, outputs=[out_txt, out_plot])

    return interface


def launch_ui(core: AGIRRFCore | None = None, *, share: bool = False) -> None:
    """Launch the interactive Gradio UI."""

    interface = build_interface(core)
    interface.launch(share=share)


__all__ = ["build_interface", "launch_ui", "GradioUnavailableError"]
