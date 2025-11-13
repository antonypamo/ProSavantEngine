from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prosavant_engine.geometry import IcosahedralField
from prosavant_engine.utils import to_psi3

app = FastAPI(title="ProSavantEngine API")

# ---- Modelos de entrada ----
class PsiIn(BaseModel):
    text: str

class TextsIn(BaseModel):
    texts: list[str]

# ---- Endpoints ligeros (no requieren Torch) ----
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/icosa/info")
def icosa_info():
    field = IcosahedralField(level=0)
    return {"nodes": len(field.coords), "edges": len(field.edges)}

@app.post("/psi")
def psi(payload: PsiIn):
    # Utilidad ligera; no levanta dependencias pesadas
    return {"psi3": to_psi3(payload.text)}

# ---- Embeddings opcional (requiere Torch + sentence-transformers) ----
def _embedder():
    try:
        # Import perezoso para evitar cargar Torch al iniciar el servidor
        from prosavant_engine.resonance import get_embedder
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                "Embeddings no disponibles. Instala dependencias:\n"
                "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
                "  pip install -e .[resonance]"
            ),
        ) from e
    return get_embedder()

@app.post("/embed")
def embed(payload: TextsIn):
    model = _embedder()  # solo aquí se intentan cargar deps pesadas
    vecs = model.encode(payload.texts)
    # Respuesta compacta: truncamos a 8 dim por vector
    return {"vectors": [v[:8] for v in vecs]}
