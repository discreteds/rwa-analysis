"""Capture the reviewed CBA FY24 selection."""

from pathlib import Path

from rwa_analysis.extraction.runner import run_capture


def extract(pdf_path):
    root = Path(__file__).parent
    return run_capture(root / "definition.py", root / "physical.py", pdf_path)
