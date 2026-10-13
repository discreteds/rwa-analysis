"""ANZ's text rows and explicit-edge matrix, driven only by physical parameters."""

from dataclasses import replace

from rwa_analysis.extraction.definitions import CapturedFragment
from rwa_analysis.extraction.physical import paragraph


def rows(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    lines = page.extract_text().splitlines()
    selected = [line for line in lines if line.startswith(p["prefix"])]
    fragments = []
    for i, line in enumerate(selected):
        tokens = line.split()[-p["columns"] :]
        label = " ".join(line.split()[: -p["columns"]])
        fragments.append(
            CapturedFragment(
                binding.revision_id,
                f"row/{i}",
                label,
                replace(binding.source_reference, row=label),
            )
        )
        for j, token in enumerate(tokens):
            evidence = replace(
                binding.source_reference, row=p["prefix"], column=p["labels"][j]
            )
            fragments.append(
                CapturedFragment(binding.revision_id, f"{i}/{j}", token, evidence)
            )
    return tuple(fragments)


def bands(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    lines = (
        document.pages[binding.source_reference.pdf_page - 1]
        .extract_text()
        .splitlines()
    )
    i = next(i for i, line in enumerate(lines) if line.startswith(p["prefix"]))
    lower, upper = lines[i].split(), lines[i + 1].split()
    labels = [lower[j] + "\n" + upper[j] for j in range(p["intervals"])] + lower[
        p["intervals"] :
    ]
    return tuple(
        CapturedFragment(
            binding.revision_id,
            str(j),
            text,
            replace(binding.source_reference, column=text),
        )
        for j, text in enumerate(labels)
    )


def matrix(document, binding):
    p = {v.name: v.value for v in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    rows = page.extract_tables(
        {
            "vertical_strategy": "explicit",
            "explicit_vertical_lines": [float(v) for v in p["edges"]],
            "horizontal_strategy": "lines",
        }
    )[0]
    headers = [" ".join(v.split()) for v in rows[0]]
    fragments = [
        CapturedFragment(
            binding.revision_id,
            "header/" + key,
            text,
            replace(binding.source_reference, column=text),
        )
        for key, text in zip(p["columns"], headers)
    ]
    lines = page.extract_text().splitlines()
    for key, prefix, section in zip(p["rows"], p["prefixes"], p["sections"]):
        row = next(row for row in rows if row[0] and row[0].startswith(prefix))
        heading = next(line for line in lines if line.startswith(section))
        values = [" ".join(v.split()) for v in row]
        fragments.append(
            CapturedFragment(
                binding.revision_id,
                key,
                "\n".join([heading] + [h + ": " + v for h, v in zip(headers, values)]),
                binding.source_reference,
            )
        )
        for column, header, text in zip(p["columns"], headers, values):
            fragments.append(
                CapturedFragment(
                    binding.revision_id,
                    key + "/" + column,
                    text,
                    replace(binding.source_reference, row=values[0], column=header),
                )
            )
    return tuple(fragments)


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


OPERATIONS = {
    "paragraph": paragraph,
    "rows": rows,
    "bands": bands,
    "matrix": matrix,
    "region": region,
}
