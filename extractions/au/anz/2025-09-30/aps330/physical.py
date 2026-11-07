"""ANZ numbered-row geometry and column-aware prose selection."""

import itertools
from dataclasses import replace

from rwa_analysis.extraction.definitions import CapturedFragment
from rwa_analysis.extraction.physical import line_match_groups, window


def region(document, binding):
    p = {x.name: x.value for x in binding.parameters}
    words = document.pages[binding.source_reference.pdf_page - 1].extract_words(
        y_tolerance=p.get("y_tolerance", 3)
    )
    text = window(words, *map(float, p["box"]), multiline=p.get("multiline", 0))
    if "second_box" in p:
        text += " " + window(words, *map(float, p["second_box"]))
    return (
        CapturedFragment(binding.revision_id, "text", text, binding.source_reference),
    )


def passage(document, binding):
    p = {x.name: x.value for x in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    if "box" in p:
        page = page.crop(tuple(map(float, p["box"])))
    text = " ".join(page.extract_text().split())
    start = text.index(p["start"])
    text = text[start : text.index(p["end"], start) + len(p["end"])]
    return (
        CapturedFragment(binding.revision_id, "text", text, binding.source_reference),
    )


def grid(document, binding):
    p = {x.name: x.value for x in binding.parameters}
    words = document.pages[binding.source_reference.pdf_page - 1].extract_words(
        y_tolerance=p.get("y_tolerance", 3)
    )
    left, right, top, bottom = map(float, p["markers"])
    markers = sorted(
        (w for w in words if left <= w["x0"] < right and top < w["top"] < bottom),
        key=lambda w: w["top"],
    )
    edges = tuple(map(float, p["edges"]))
    label_left, label_right = map(float, p["labels"])
    result = []
    for i, marker in enumerate(markers):
        y = marker["top"]
        multiline = i in tuple(map(int, p.get("multiline_rows", ())))
        label = window(
            words,
            label_left,
            label_right,
            y - (5 if multiline else 1),
            y + (14 if multiline else 8),
            multiline,
        )
        evidence = replace(binding.source_reference, row=marker["text"])
        result.append(
            CapturedFragment(binding.revision_id, f"row/{i}", label, evidence)
        )
        for j, (a, b) in enumerate(itertools.pairwise(edges)):
            result.append(
                CapturedFragment(
                    binding.revision_id,
                    f"{i}/{j}",
                    window(words, a, b, y - 1, y + 8),
                    replace(evidence, column=p["columns"][j]),
                )
            )
    return tuple(result)


OPERATIONS = {"region": region, "passage": passage, "grid": grid, "line": line_match_groups}
