"""Text resonance simulator mapping embeddings to synthetic spectra."""

from __future__ import annotations

from threading import Lock
from typing import Dict, Iterable

import numpy as np
from scipy.fft import fft, fftfreq
from sentence_transformers import SentenceTransformer

from .config import DEFAULT_MODEL_NAME

_embedder: SentenceTransformer | None = None
_embedder_lock = Lock()


def get_embedder() -> SentenceTransformer:
    """Return a shared SentenceTransformer instance, loading lazily."""

    global _embedder
    with _embedder_lock:
        if _embedder is None:
            _embedder = SentenceTransformer(DEFAULT_MODEL_NAME)
    return _embedder


class ResonanceSimulator:
    """Converts text into a synthetic waveform and FFT spectrum."""

    def __init__(self, freq_base: float = 440.0) -> None:
        self.freq_base = freq_base

    def simulate(self, text: str) -> Dict[str, np.ndarray | float]:
        embedder = get_embedder()
        vector = embedder.encode(text)
        base = float(np.linalg.norm(vector))
        freq = self.freq_base * (1 + (base % 0.1))
        t = np.linspace(0, 1, 2048)
        signal = np.sin(2 * np.pi * freq * t)
        spectrum = np.abs(fft(signal))[:1024]
        dom_freq = float(fftfreq(2048, 1 / 44100)[:1024][np.argmax(spectrum)])
        return {"signal": signal, "dominant_frequency": dom_freq, "embedding": vector}

    @property
    def embedder(self) -> SentenceTransformer:
        """Expose the shared embedding model used internally."""

        return get_embedder()


def harmonic_quantization(base_freq: float = 440.0, steps: int = 12) -> Iterable[float]:
    """Generate an equal-tempered scale anchored at *base_freq*."""

    return [base_freq * (2 ** (k / 12)) for k in range(steps)]


__all__ = ["ResonanceSimulator", "harmonic_quantization", "get_embedder"]
