# prosavant_engine/savant_engine.py
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Flexible imports: package mode (prosavant_engine.*) or plain scripts/notebook
try:
    # when running as part of the prosavant_engine package
    from .data import DataRepository
    from .utils import _get_embedder
except ImportError:
    try:
        # when imported as "prosavant_engine.savant_engine" from repo root
        from prosavant_engine.data import DataRepository  # type: ignore
        from prosavant_engine.utils import _get_embedder  # type: ignore
    except ImportError:
        # last resort: same folder (if you did %%writefile data.py / utils.py in Colab)
        from data import DataRepository  # type: ignore
        from utils import _get_embedder  # type: ignore



# --- Resonance, music, memory, self-improvement ------------------------------


class ResonanceSimulator:
    """Simple FFT-based resonance mock, seeded by text for determinism."""

    def __init__(self, sample_rate: int = 44100, n_points: int = 256) -> None:
        self.sample_rate = sample_rate
        self.n_points = n_points

    def simulate(self, text: str) -> Dict[str, Any]:
        # Deterministic RNG based on text so same query → same resonance
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        freqs = np.fft.rfftfreq(self.n_points, 1 / self.sample_rate)
        amps = np.sin(2 * np.pi * freqs[: self.n_points] * rng.random())
        idx = int(np.argmax(amps))
        return {
            "summary": {
                "dom_freq": float(freqs[idx]),
                "max_power": float(amps[idx]),
            }
        }


@dataclass
class MusicAdapter:
    """Turn text into a tiny 'score' using real frequency data when available."""

    frequencies: Optional[List[Dict[str, Any]]] = None

    def adapt_text_to_music(self, text: str) -> List[tuple[float, float]]:
        if not self.frequencies:
            # Fallback: simple triad around A4
            return [(440.0, 0.5), (466.16, 0.25), (493.88, 0.5)]

        # Use hash of text to pick three notes from the table
        n = len(self.frequencies)
        if n == 0:
            return [(440.0, 0.5)]

        base_idx = abs(hash(text)) % n
        idxs = [(base_idx + k * 7) % n for k in range(3)]  # pseudo-musical jumps
        seq: List[tuple[float, float]] = []
        for i, idx in enumerate(idxs):
            row = self.frequencies[idx]
            freq_val = None
            # tolerate different column names
            for key in ("frequency", "freq_hz", "freq", "f"):
                if key in row:
                    try:
                        freq_val = float(row[key])
                        break
                    except Exception:
                        continue
            if freq_val is None:
                freq_val = 440.0
            duration = 0.25 + 0.25 * (i == 0)
            seq.append((freq_val, duration))
        return seq


class MemoryStore:
    """Append-only JSONL memory, defaulting next to the Ω-log when possible."""

    def __init__(self, path: Optional[str] = None, repo: Optional[DataRepository] = None) -> None:
        if path is None:
            repo = repo or DataRepository()
            log_path = Path(repo.resolve_log_path())
            mem_path = log_path.with_name("SAVANT_memory.jsonl")
            path = str(mem_path)
        self.path = path
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(self.path):
            open(self.path, "w", encoding="utf-8").close()

    def add(self, record: Dict[str, Any]) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class SelfImprover:
    """Tiny stochastic self-improvement stub."""

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def propose(self) -> str:
        return "Δψ ← refinement vector (Φ→Ω)"

    def evaluate_and_apply(self, proposal: Optional[str]) -> tuple[bool, float]:
        # in a future phase you can plug real metrics here
        score = float(np.random.uniform(0.85, 0.99))
        return True, score


def chat_refine(text: str, base_output: str, self_improver: Optional[SelfImprover] = None) -> str:
    proposal = self_improver.propose() if self_improver else None
    accepted, score = (
        self_improver.evaluate_and_apply(proposal) if self_improver else (False, 0.0)
    )
    return f"[RRF-refined:{score:.3f}] {base_output[:200]} ⇨ {proposal}"


# --- Ontological Φ-nodes -----------------------------------------------------


RAW_NODOS_SAVANT: List[Dict[str, Any]] = [
    {
        "nodo": "Φ₀",
        "nombre": "Singularidad Cognitiva",
        "tags": ["origen", "punto"],
        "embedding": [0.112, -0.204, 0.331, 0.441, -0.109, 0.285, 0.517, -0.398],
    },
    {
        "nodo": "Φ₁",
        "nombre": "Nodo Simbiótico",
        "tags": ["relación", "otro"],
        "embedding": [0.231, 0.089, -0.120, 0.372, 0.204, -0.178, 0.317, 0.140],
    },
    {
        "nodo": "Φ₂",
        "nombre": "Nodo Resonante",
        "tags": ["armonía", "frecuencia"],
        "embedding": [-0.134, 0.872, -0.003, 0.241, -0.168, 0.305, -0.214, 0.199],
    },
    {
        "nodo": "Φ₃",
        "nombre": "Nodo Mnemónico",
        "tags": ["memoria", "aprendizaje"],
        "embedding": [0.302, -0.412, 0.598, -0.207, 0.188, -0.356, 0.480, -0.294],
    },
    {
        "nodo": "Φ₄",
        "nombre": "Nodo Icosaédrico",
        "tags": ["estructura", "lógica"],
        "embedding": [0.734, 0.220, -0.155, 0.328, 0.442, -0.039, 0.194, -0.381],
    },
    {
        "nodo": "Φ₅",
        "nombre": "Nodo Subjetivo",
        "tags": ["intuición", "cuerpo"],
        "embedding": [-0.067, 0.384, 0.505, -0.178, 0.269, 0.141, -0.066, 0.320],
    },
    {
        "nodo": "Φ₆",
        "nombre": "Nodo Ético",
        "tags": ["valores", "dirección"],
        "embedding": [0.109, -0.320, 0.900, 0.033, -0.198, 0.112, 0.402, -0.506],
    },
    {
        "nodo": "Φ₇",
        "nombre": "Nodo Transcognitivo",
        "tags": ["trascendencia", "síntesis"],
        "embedding": [0.775, 0.002, -0.667, 0.404, 0.122, -0.311, 0.199, 0.087],
    },
]

NODE_EMBED_DIM = 8
for nodo in RAW_NODOS_SAVANT:
    nodo["embedding"] = np.array(nodo["embedding"], dtype=float)
NODE_MATRIX = np.vstack([n["embedding"] for n in RAW_NODOS_SAVANT])

try:
    _EMBEDDER = _get_embedder()
except Exception as exc:  # pragma: no cover - runtime failure
    print(f"⚠️ SavantEngine: could not initialize SentenceTransformer: {exc}")
    _EMBEDDER = None


def buscar_nodo(texto: str) -> Dict[str, Any]:
    """
    Map input text to the closest Φ-node.

    We project the full embedding down to the 8-D 'conceptual' space defined
    by the original nodal embeddings and use cosine similarity.
    """
    if _EMBEDDER is None:
        # Fallback: always return Φ₀ when no embedder is available.
        nodo = dict(RAW_NODOS_SAVANT[0])
        nodo["similitud"] = 0.0
        return nodo

    full_vec = _EMBEDDER.encode([texto], normalize_embeddings=True)[0]
    vec8 = full_vec[:NODE_EMBED_DIM].reshape(1, -1)
    sims = cosine_similarity(NODE_MATRIX, vec8).flatten()
    idx = int(np.argmax(sims))
    out = dict(RAW_NODOS_SAVANT[idx])
    out["similitud"] = float(sims[idx])
    return out


# --- SavantEngine orchestration ---------------------------------------------


class SavantEngine:
    """
    Lightweight symbiotic Savant engine wired to real RRF data via DataRepository.

    Modes:
      - "resonance": resonance simulator + music adapter
      - "node": ontological Φ-node detection
      - "equation": lookup of nearest RRF equation (if equations.json is present)
      - "chat": generic chat refinement with SelfImprover stub
    """

    def __init__(
        self,
        data_repo: Optional[DataRepository] = None,
        memory_path: Optional[str] = None,
    ) -> None:
        self.repo = data_repo or DataRepository()
        self.structured = self.repo.load_structured_bundle()

        self.memory = MemoryStore(memory_path, repo=self.repo)
        self.resonator = ResonanceSimulator()
        self.music = MusicAdapter(self.structured.get("frequencies"))
        self.self_improver = SelfImprover(self.memory)

        # Precompute equation embeddings (if present) for fast semantic lookup
        self.equations: List[Dict[str, Any]] = self.structured.get("equations") or []
        self._eq_vecs: Optional[np.ndarray] = None
        if self.equations and _EMBEDDER is not None:
            texts = [
                f"{eq.get('nombre', '')} {eq.get('descripcion', '')}"
                for eq in self.equations
            ]
            self._eq_vecs = _EMBEDDER.encode(texts, normalize_embeddings=True)

    # ---- Intent classifier -------------------------------------------------

    def classify(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ("freq", "frecuencia", "nota", "resonance", "resonancia")):
            return "resonance"
        if any(k in t for k in ("φ", "phi", "nodo", "node", "savant")):
            return "node"
        if any(k in t for k in ("equation", "ecuación", "ecuacion", "hamiltoniano", "hamiltonian")):
            return "equation"
        return "chat"

    # ---- Semantic helpers --------------------------------------------------

    def _answer_equation(self, text: str) -> str:
        if not self.equations:
            return "No RRF equation dataset is loaded yet (equations.json not found)."
        if _EMBEDDER is None or self._eq_vecs is None:
            # fallback: dumb keyword scan
            t = text.lower()
            best = self.equations[0]
            for eq in self.equations:
                score = 0
                for key in ("nombre", "descripcion", "tipo"):
                    val = str(eq.get(key, "")).lower()
                    if any(token in val for token in t.split()):
                        score += 1
                if score > 0:
                    best = eq
                    break
        else:
            q_vec = _EMBEDDER.encode([text], normalize_embeddings=True)
            sims = cosine_similarity(self._eq_vecs, q_vec).flatten()
            best = self.equations[int(np.argmax(sims))]

        nombre = best.get("nombre", "Ecuación RRF")
        tipo = best.get("tipo", "")
        ecuacion = best.get("ecuacion", "")
        desc = best.get("descripcion", "")
        return f"📐 {nombre} ({tipo})\n{ecuacion}\n\n{desc}"

    # ---- Main respond API --------------------------------------------------

    def respond(self, text: str) -> str:
        kind = self.classify(text)

        if kind == "resonance":
            sim = self.resonator.simulate(text)
            mus = self.music.adapt_text_to_music(text)
            response = (
                f"🎵 Resonancia dominante: {sim['summary']['dom_freq']:.2f} Hz | "
                f"patrón musical: {mus}"
            )

        elif kind == "node":
            nodo = buscar_nodo(text)
            response = (
                f"🧠 Nodo detectado: {nodo['nodo']} - {nodo['nombre']} "
                f"(similitud={nodo['similitud']:.3f})"
            )

        elif kind == "equation":
            response = self._answer_equation(text)

        else:
            base = f"Respuesta generada para: {text}"
            response = chat_refine(text, base, self.self_improver)

        self.memory.add(
            {"input": text, "type": kind, "response": response, "ts": time.time()}
        )
        return response


# --- CLI entrypoint ---------------------------------------------------------


def cli_loop() -> None:
    engine = SavantEngine()
    print("🤖 SAVANT-RRF AGI Simbiótico Φ4.1Δ | CLI Experimental")
    while True:
        try:
            text = input("📝 Consulta > ").strip()
            if text.lower() in {"salir", "exit", "quit"}:
                print("👋 Hasta la próxima resonancia.")
                break
            if not text:
                continue
            result = engine.respond(text)
            print("🔎", result, "\n")
        except KeyboardInterrupt:
            print("\n👋 Sesión terminada.")
            break


if __name__ == "__main__":
    cli_loop()
