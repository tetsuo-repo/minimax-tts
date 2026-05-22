"""Test bootstrap.

The integration's package ``__init__.py`` imports Home Assistant, which we do
not want to install just to unit-test the pure-logic modules (``api`` and
``const``). So we register a lightweight stand-in package and load those two
modules from file via importlib, without ever executing the real
``__init__.py``. Tests then ``import minimax_tts.api`` as usual.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PKG_DIR = _ROOT / "custom_components" / "minimax_tts"
_PKG_NAME = "minimax_tts"

if _PKG_NAME not in sys.modules:
    _pkg = types.ModuleType(_PKG_NAME)
    _pkg.__path__ = [str(_PKG_DIR)]  # make it a package for relative imports
    sys.modules[_PKG_NAME] = _pkg


def _load(name: str) -> types.ModuleType:
    full = f"{_PKG_NAME}.{name}"
    if full in sys.modules:
        return sys.modules[full]
    spec = importlib.util.spec_from_file_location(full, _PKG_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[full] = module
    spec.loader.exec_module(module)
    return module


# Order matters: api does ``from .const import ...``.
_load("const")
_load("api")
