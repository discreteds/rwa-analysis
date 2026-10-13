"""Invoke an explicitly selected source-specific extractor."""

import importlib.util
import sys
from pathlib import Path
from uuid import uuid4

from .datasets import ExtractionBundle
from .definitions import CapturedBundle


def run_extractor(script_path: Path, pdf_path: Path) -> ExtractionBundle | CapturedBundle:
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    if not script_path.is_file():
        raise FileNotFoundError(script_path)
    name = f"_rwa_extractor_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load extractor {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        bundle = module.extract(pdf_path)
    finally:
        del sys.modules[name]
    if not isinstance(bundle, (ExtractionBundle, CapturedBundle)):
        raise TypeError(f"{script_path}: extract() must return ExtractionBundle")
    return bundle


def _load(path):
    name = f"_rwa_capture_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        del sys.modules[name]
    return module


def run_capture(definition_path, operations_path, pdf_path):
    from .capture import capture

    declarations = _load(definition_path)
    physical = _load(operations_path)
    return capture(
        pdf_path,
        declarations.DEFINITION,
        declarations.SELECTED_DEFINITIONS,
        physical.OPERATIONS,
    )
