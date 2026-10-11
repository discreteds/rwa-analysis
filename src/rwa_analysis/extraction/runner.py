"""Invoke an explicitly selected source-specific extractor."""

import importlib.util
import sys
from pathlib import Path
from uuid import uuid4

from .datasets import ExtractionBundle


def run_extractor(script_path: Path, pdf_path: Path) -> ExtractionBundle:
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
    if not isinstance(bundle, ExtractionBundle):
        raise TypeError(f"{script_path}: extract() must return ExtractionBundle")
    return bundle
