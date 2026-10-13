"""Physical paragraph selection; no financial or contextual interpretation."""

from .definitions import CapturedFragment


def paragraph(document, binding):
    parameters = {p.name: p.value for p in binding.parameters}
    text = document.pages[binding.source_reference.pdf_page - 1].extract_text()
    if "after" in parameters:
        text = text.split(parameters["after"], 1)[1]
    start, end = parameters["start"], parameters["end"]
    text = " ".join((start + text.split(start, 1)[1].split(end, 1)[0]).split())
    return (
        CapturedFragment(binding.revision_id, "text", text, binding.source_reference),
    )
