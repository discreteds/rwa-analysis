"""Physical text-layer, region and token selection for the reviewed 2023 PDF."""

import re
from dataclasses import replace

from rwa_analysis.extraction.definitions import CapturedFragment


def passage(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    if "font_prefix" in p:
        page = page.filter(
            lambda obj: (
                obj.get("object_type") != "char"
                or obj.get("fontname", "").startswith(p["font_prefix"])
            )
        )
    text = page.extract_text()
    if "after" in p:
        text = text.split(p["after"], 1)[1]
    text = p["start"] + text.split(p["start"], 1)[1]
    if p["end"]:
        text = text.split(p["end"], 1)[0]
    text = " ".join(text.split()).replace("transaction- managed", "transaction-managed")
    return (
        CapturedFragment(binding.revision_id, "text", text, binding.source_reference),
    )


def token(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    (fragment,) = passage(document, binding)
    return (
        replace(fragment, text=re.findall(p["pattern"], fragment.text)[p["index"]]),
    )


def region(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    text = (
        document.pages[binding.source_reference.pdf_page - 1]
        .crop(tuple(float(v) for v in p["box"]))
        .extract_text()
    )
    return (
        CapturedFragment(
            binding.revision_id,
            "text",
            " ".join(text.split()),
            binding.source_reference,
        ),
    )


def rows(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    text = document.pages[binding.source_reference.pdf_page - 1].extract_text()
    lines = text.split(p["after"], 1)[1].splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(p["prefix"]))
    fragments = []
    for i, line in enumerate(lines[start : start + p["rows"]]):
        tokens = line.split()
        label = " ".join(tokens[: -p["columns"]])
        fragments.append(
            CapturedFragment(
                binding.revision_id,
                f"row/{i}",
                label,
                replace(binding.source_reference, row=label),
            )
        )
        for j, value in enumerate(tokens[-p["columns"] :]):
            fragments.append(
                CapturedFragment(
                    binding.revision_id,
                    f"{i}/{j}",
                    value,
                    replace(binding.source_reference, row=label, column=p["labels"][j]),
                )
            )
    return tuple(fragments)


OPERATIONS = {"passage": passage, "token": token, "region": region, "rows": rows}
