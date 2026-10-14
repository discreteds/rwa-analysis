"""NAB physical text/geometry readers; all selections come from bindings."""

import re
from dataclasses import replace
from itertools import pairwise

from rwa_analysis.extraction.definitions import CapturedFragment
from rwa_analysis.extraction.physical import paragraph


def rows(document, binding):
    p = {p.name: p.value for p in binding.parameters}
    text = document.pages[binding.source_reference.pdf_page - 1].extract_text()
    text = text.split(p["panel"], 1)[1]
    text = re.split(r"As at |Table 5\.1\.J", text, maxsplit=1)[0]
    lines = [line for line in text.splitlines() if line.startswith(p["prefix"])]
    fragments = []
    for i, line in enumerate(lines):
        label, *tokens = line.rsplit(" ", p["columns"])
        evidence = replace(binding.source_reference, row=label)
        fragments.append(
            CapturedFragment(binding.revision_id, f"row/{i}", label, evidence)
        )
        for j, token in enumerate(tokens):
            fragments.append(
                CapturedFragment(
                    binding.revision_id,
                    f"{i}/{j}",
                    token,
                    replace(evidence, column=p["labels"][j]),
                )
            )
    return tuple(fragments)


def bands(document, binding):
    p = {p.name: p.value for p in binding.parameters}
    text = document.pages[binding.source_reference.pdf_page - 1].extract_text()
    line = next(line for line in text.splitlines() if line.startswith(p["prefix"]))
    return tuple(
        CapturedFragment(
            binding.revision_id,
            str(i),
            token,
            replace(binding.source_reference, column=token),
        )
        for i, token in enumerate(line.split())
    )


def column_headers(document, binding):
    p = {p.name: p.value for p in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    top = page.search(p["panel"], regex=False)[0]["bottom"] + 1
    bottom = next(
        m["top"] for m in page.search(p["end"], regex=False) if m["top"] > top
    )
    edges = tuple(float(n) for n in p["edges"])
    return tuple(
        CapturedFragment(
            binding.revision_id,
            str(i),
            " ".join(page.crop((left, top, right, bottom)).extract_text().split()),
            binding.source_reference,
        )
        for i, (left, right) in enumerate(pairwise(edges))
    )


def region(document, binding):
    p = {p.name: p.value for p in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    text = page.crop(tuple(float(n) for n in p["box"])).extract_text()
    if "start" in p:
        text = p["start"] + text.split(p["start"], 1)[1].split(p["end"], 1)[0]
    return (
        CapturedFragment(
            binding.revision_id,
            "text",
            " ".join(text.split()),
            binding.source_reference,
        ),
    )


OPERATIONS = {
    "paragraph": paragraph,
    "rows": rows,
    "bands": bands,
    "column_headers": column_headers,
    "region": region,
}
