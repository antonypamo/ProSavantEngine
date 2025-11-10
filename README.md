---
license: mit
datasets:
- antonypamo/savantorganized
language:
- en
- es
base_model:
- antonypamo/ProSavantRRF
tags:
- chemistry
- biology
- art
- text-generation-inference
- agent
- medical
- climate
- code
---
# 🧠 AGI–RRF Φ9.1 — Resonance of Reality Framework

**Author:** Antony Padilla Morales  
**Version:** Φ9.1
**Repository:** [antonympamo/ProSavantEngine](https://huggingface.co/antonympamo/ProSavantEngine)

---

## 🌌 Overview
The **AGI–RRF Φ9.0-Δ** system unifies:
- **SavantEngine** (cognitive orchestration)
- **AGORA Resonant Field Φ8.5** (distributed semantic field)
- **RIS-CLURM** (icosahedral geometry with logarithmic correction)
- **RRF Predictions** (quantized Dirac-harmonic model of reality)

It models cognition, resonance, and geometry as a **self-organizing icosahedral network** of energy-semantic interactions.

---

## ⚙️ Key Components
| Module | Description |
|---------|--------------|
| `IcosahedralField` | Discrete 12-node geometric substrate. |
| `DiracHamiltonian` | Discrete energy operator with logarithmic potential. |
| `ResonanceSimulator` | Maps text → waveform → FFT for harmonic coherence. |
| `DataRepository` | Auto-detects Google Drive datasets and loads auxiliary CSV/JSON files. |
| `OmegaReflection` | Persists Φ/Ω metrics and produces 3D trajectory visualizations. |
| `SelfImprover` | Meta-learning loop adjusting system coherence. |

---

## 🚀 Run Locally

```bash
pip install -r requirements.txt
python AGI_RRF_Phi9_Delta.py
```

The launcher now also supports direct command-line arguments:

```bash
python -m prosavant_engine --mode server --host 0.0.0.0 --port 8765
python -m prosavant_engine --mode client --server-uri ws://localhost:8765
```

To experiment with the Colab-style Gradio interface, install the optional
`gradio` dependency and launch:

```bash
pip install gradio
python -c "from prosavant_engine.ui import launch_ui; launch_ui()"
```

### Remote dataset support

Set the `SAVANT_REMOTE_DATASET` environment variable to automatically download
structured data from the Hugging Face Hub. Optional variables include
`SAVANT_REMOTE_DATASET_REVISION` (specific commit), `SAVANT_REMOTE_DATASET_SUBDIR`
(subdirectory containing the files), and `SAVANT_DATASET_CACHE_DIR` (custom
cache path).

