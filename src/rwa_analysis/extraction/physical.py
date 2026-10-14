"""Shared physical readers; no financial or contextual interpretation."""

import re
from dataclasses import replace

from .definitions import CapturedFragment


def window(words, left, right, top, bottom, multiline=False):
    lines = []
    selected = (
        w for w in words if left <= w["x0"] < right and top <= w["top"] < bottom
    )
    for word in sorted(selected, key=lambda w: (w["top"], w["x0"])):
        if not lines or abs(word["top"] - lines[-1][0]["top"]) > 1:
            lines.append([])
        lines[-1].append(word)
    return ("\n" if multiline else " ").join(
        " ".join(w["text"] for w in sorted(line, key=lambda w: w["x0"]))
        for line in lines
    )


def cropped_text_region(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    text = " ".join(page.crop(tuple(float(v) for v in p["box"])).extract_text().split())
    if "start" in p:
        text = p["start"] + text.split(p["start"], 1)[1].split(p["end"], 1)[0]
    return (
        CapturedFragment(
            binding.revision_id, "text", text.strip(), binding.source_reference
        ),
    )


def line_match_groups(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    text = document.pages[binding.source_reference.pdf_page - 1].extract_text()
    if "after" in p:
        text = text.split(p["after"], 1)[1]
    match = re.search(p["pattern"], text, re.MULTILINE)
    return tuple(
        CapturedFragment(binding.revision_id, key, value, binding.source_reference)
        for key, value in match.groupdict().items()
    )


def anchored_prefix_rows(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    text = document.pages[binding.source_reference.pdf_page - 1].extract_text()
    text = text.split(p["after"], 1)[1]
    if "before" in p:
        text = text.split(p["before"], 1)[0]
    fragments = []
    for i, row in enumerate(
        line for line in text.splitlines() if line.startswith(p["prefix"])
    ):
        tokens = row.split()[-p["columns"] :]
        label = " ".join(row.split()[: -p["columns"]])
        source = replace(binding.source_reference, row=label)
        fragments.append(
            CapturedFragment(binding.revision_id, f"row/{i}", label, source)
        )
        for j, token in enumerate(tokens):
            fragments.append(
                CapturedFragment(
                    binding.revision_id,
                    f"{i}/{j}",
                    token,
                    replace(source, column=p["labels"][j]),
                )
            )
    return tuple(fragments)


def line_band_matches(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    text = document.pages[binding.source_reference.pdf_page - 1].extract_text()
    row = next(line for line in text.splitlines() if line.startswith(p["prefix"]))
    return tuple(
        CapturedFragment(
            binding.revision_id,
            str(i),
            label,
            replace(binding.source_reference, column=label),
        )
        for i, label in enumerate(re.findall(p["pattern"], row))
    )


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
