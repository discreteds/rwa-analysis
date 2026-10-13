"""Selected ANZ capture entrypoint for ordinary DocumentSelection calls."""

from pathlib import Path

from rwa_analysis.extraction.runner import run_capture


def extract(pdf_path):
    directory = Path(__file__).parent
    return run_capture(directory / "definition.py", directory / "physical.py", pdf_path)
