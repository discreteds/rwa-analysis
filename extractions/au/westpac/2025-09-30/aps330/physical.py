"""Westpac word-start windows and prose columns; no financial semantics."""

import itertools
from dataclasses import replace

from rwa_analysis.extraction.definitions import CapturedFragment


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


def region(document, binding):
    p = {x.name: x.value for x in binding.parameters}
    words = document.pages[binding.source_reference.pdf_page - 1].extract_words(
        y_tolerance=p.get("y_tolerance", 3)
    )
    text = window(words, *map(float, p["box"]), multiline=p.get("multiline", 0))
    return (
        CapturedFragment(binding.revision_id, "text", text, binding.source_reference),
    )


def passage(document, binding):
    p = {x.name: x.value for x in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    page = page.crop((p.get("left", 0), 0, page.width, page.height))
    text = " ".join(page.extract_text().replace("-\n", "-").split())
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
    tops = sorted(
        w["top"] for w in words if left <= w["x0"] < right and top < w["top"] < bottom
    )
    if "last_marker" in p:
        a, b, c, d = map(float, p["last_marker"])
        tops += [
            w["top"]
            for w in words
            if a <= w["x0"] < b and c < w["top"] < d and w["text"] == p["last_prefix"]
        ]
    edges = tuple(map(float, p["edges"]))
    result = []
    for i, y in enumerate(tops):
        label_edges = (
            p["last_labels"]
            if "last_marker" in p and i == len(tops) - 1
            else p["labels"]
        )
        label = window(words, *map(float, label_edges), y - 1, y + 7)
        evidence = replace(binding.source_reference, row=label)
        result.append(
            CapturedFragment(binding.revision_id, f"row/{i}", label, evidence)
        )
        for j, (a, b) in enumerate(itertools.pairwise(edges)):
            result.append(
                CapturedFragment(
                    binding.revision_id,
                    f"{i}/{j}",
                    window(words, a, b, y - 1, y + 7),
                    replace(evidence, column=p["columns"][j]),
                )
            )
    return tuple(result)


OPERATIONS = {"region": region, "passage": passage, "grid": grid}
