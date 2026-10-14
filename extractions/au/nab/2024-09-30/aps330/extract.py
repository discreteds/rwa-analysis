"""Capture the reviewed NAB FY24 selection through the shared metadata runner."""

from pathlib import Path

from rwa_analysis.extraction.runner import run_capture


def extract(pdf_path):
    source = Path(__file__).parent
    return run_capture(source / "definition.py", source / "physical.py", pdf_path)
