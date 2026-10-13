"""DISPOSABLE: physical operations only; no imports of ANZ configuration/semantics."""


def line(page, parameters):
    return {"text": next(x for x in page.extract_text().splitlines()
                         if x.startswith(parameters["prefix"]))}


def numeric_row(page, parameters):
    text = line(page, parameters)["text"]
    parts = text.rsplit(maxsplit=parameters["count"])
    return {"label": parts[0], **{str(i): token for i, token in enumerate(parts[1:])}}


def crops(page, parameters):
    return {str(i): page.crop(box).extract_text() for i, box in enumerate(parameters["boxes"])}


def passage(page, parameters):
    text = page.extract_text()
    if parameters["after"]:
        text = text.split(parameters["after"], 1)[1]
    return {"text": parameters["start"] + text.split(parameters["start"], 1)[1].split(parameters["end"], 1)[0]}


def ruled_matrix(page, parameters):
    # Bespoke geometry operation selected explicitly by the source declaration.
    rows = page.extract_tables({"vertical_strategy": "explicit",
        "explicit_vertical_lines": parameters["edges"], "horizontal_strategy": "lines"})[0]
    clean = lambda text: " ".join((text or "").split())
    headers = [clean(value) for value in rows[0]]
    output = {f"header/{i}": value for i, value in enumerate(headers)}
    output["title"] = next(x for x in page.extract_text().splitlines() if x.startswith("Table "))
    for key, prefix, section_prefix in parameters["rows"]:
        row = next(r for r in rows if clean(r[0]).startswith(prefix))
        section = next(x for x in page.extract_text().splitlines() if x.startswith(section_prefix))
        output[f"{key}/section"] = section
        output.update({f"{key}/{i}": clean(value) for i, value in enumerate(row)})
        output[key] = section + "\n" + "\n".join(
            f"{header}: {clean(value)}" for header, value in zip(headers, row, strict=True))
    return output
