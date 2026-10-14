"""Physical text rows, two-line bands and bounded header regions."""

from dataclasses import replace

from rwa_analysis.extraction.definitions import CapturedFragment
from rwa_analysis.extraction.physical import paragraph


def rows(document, binding):
    parameters = {p.name: p.value for p in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    selected = [
        line
        for line in page.extract_text().splitlines()
        if line.startswith(parameters["prefix"])
    ]
    fragments = []
    for i, line in enumerate(selected):
        tokens = line.split()[-parameters["columns"] :]
        label = " ".join(line.split()[: -parameters["columns"]])
        fragments.append(
            CapturedFragment(
                binding.revision_id,
                f"row/{i}",
                label,
                replace(binding.source_reference, row=label),
            )
        )
        for j, token in enumerate(tokens):
            fragments.append(
                CapturedFragment(
                    binding.revision_id,
                    f"{i}/{j}",
                    token,
                    replace(
                        binding.source_reference,
                        row=label,
                        column=parameters["labels"][j],
                    ),
                )
            )
    return tuple(fragments)


def bands(document, binding):
    parameters = {p.name: p.value for p in binding.parameters}
    lines = (
        document.pages[binding.source_reference.pdf_page - 1]
        .extract_text()
        .splitlines()
    )
    index = next(
        i for i, line in enumerate(lines) if line.startswith(parameters["prefix"])
    )
    lower, upper = lines[index].split(), lines[index + 1].split()
    count = parameters["intervals"]
    labels = [lower[j] + "\n" + upper[j] for j in range(count)] + lower[count:]
    return tuple(
        CapturedFragment(
            binding.revision_id,
            str(j),
            label,
            replace(binding.source_reference, column=label),
        )
        for j, label in enumerate(labels)
    )


def region(document, binding):
    parameters = {p.name: p.value for p in binding.parameters}
    page = document.pages[binding.source_reference.pdf_page - 1]
    text = page.crop(tuple(float(v) for v in parameters["box"])).extract_text()
    return (
        CapturedFragment(
            binding.revision_id,
            "text",
            " ".join(text.split()),
            binding.source_reference,
        ),
    )


OPERATIONS = {"paragraph": paragraph, "rows": rows, "bands": bands, "region": region}
