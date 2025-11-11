"""ProSavantEngine public API (lightweight).

Avoid importing the heavy `resonance` module (pulls transformers/torch)
at import time. Those symbols are exposed lazily via __getattr__.
"""

from importlib import import_module

# Re-export lightweight modules eagerly
from .config import *            # noqa: F401,F403
from .core import *              # noqa: F401,F403
from .data import *              # noqa: F401,F403
from .geometry import *          # noqa: F401,F403
from .networking import *        # noqa: F401,F403
from .physics import *           # noqa: F401,F403
from .reflection import *        # noqa: F401,F403
from .self_improvement import *  # noqa: F401,F403
from .ui import *                # noqa: F401,F403
from .utils import *             # noqa: F401,F403

# Public names that are lazily provided from prosavant_engine.resonance
__lazy_from_resonance__ = {"ResonanceSimulator", "harmonic_quantization"}

def __getattr__(name: str):
    if name in __lazy_from_resonance__:
        mod = import_module(".resonance", __name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    # present lazy names in dir()
    return sorted(set(globals().keys()) | __lazy_from_resonance__)
