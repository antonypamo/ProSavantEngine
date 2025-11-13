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
**Repository:** [antonypamo/ProSavantEngine](https://huggingface.co/antonypamo/ProSavantEngine)

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

## ☁️ Use in Google Colab

```python
from huggingface_hub import login
from prosavant_engine import setup_data_repository

# 1. Authenticate with Hugging Face once per runtime so private datasets are reachable.
login(token="hf_your_token")

# 2. Build a repository. This mounts Google Drive (if available) and falls back
#    to downloading the remote dataset into ~/.cache/prosavant/datasets.
repo = setup_data_repository(remote_dataset="antonympamo/savant_rrf1")

# 3. Load the structured CSV/JSON artefacts required by the engine.
structured_data = repo.load_structured()
```

If you already synchronized the dataset manually, pass `mount_drive=False` and
provide your own `additional_paths` so the repository skips the drive mounting
step.
### Remote dataset support

Set the `SAVANT_REMOTE_DATASET` environment variable to automatically download
structured data from the Hugging Face Hub. Optional variables include
`SAVANT_REMOTE_DATASET_REVISION` (specific commit), `SAVANT_REMOTE_DATASET_SUBDIR`
(subdirectory containing the files), and `SAVANT_DATASET_CACHE_DIR` (custom
cache path).

pip install -r requirements.txt
python AGI_RRF_Phi9_Delta.py
