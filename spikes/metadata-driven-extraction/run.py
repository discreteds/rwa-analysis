"""DISPOSABLE demonstration, not a production entrypoint or test suite."""

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from tempfile import mkdtemp

from mountainash_files import FileSinkSpec, write

from anz_2023 import EXTRACTION, REFINEMENT, REFINEMENT_TARGETS
from capture import capture
from config import RunConfig
from conformance import conform, publish_and_read
from metadata import Definition
from physical import crops, line, numeric_row, passage, ruled_matrix


config = RunConfig(Path(__file__).resolve().parents[2],
                   Path(mkdtemp(prefix="metadata-extraction-spike-", dir="/tmp/opencode")))
operations = {"line": line, "numeric_row": numeric_row, "crops": crops,
              "passage": passage, "ruled_matrix": ruled_matrix}

bronze = capture(config.project_root / EXTRACTION.pdf_path, EXTRACTION, operations)
path = config.output_root / "bronze-spike.json"
write(FileSinkSpec(path=str(path), format="json"), bronze)
saved = json.loads(path.read_text())
baseline = publish_and_read(conform(saved), config.output_root / "baseline.duckdb")

# New interpretation is retained separately. Neither call below takes a PDF or reader.
revision_path = config.output_root / "interpretation-spike.json"
revision_path.write_text(json.dumps({"status": "DISPOSABLE source-supported enrichment",
    "definition": asdict(REFINEMENT), "targets": REFINEMENT_TARGETS}, indent=2))
retained_revision = json.loads(revision_path.read_text())
refined = publish_and_read(conform(saved, ((Definition(**retained_revision["definition"]),
                                           retained_revision["targets"]),)),
                           config.output_root / "refined.duckdb")

# Independent development evidence; expected content is NOT generated from declarations.
golden = json.loads((config.project_root /
    "tests/bronze/au/anz/2023-09-30/aps330/golden.json").read_text())
actual = {r["id"]: r for r in baseline["occurrences"].to_dicts()}
numeric_agreement = all(actual[f"cell/{key}"]["original_text"] == token
                        for key, label, unit, token in golden["backtesting"])
comment_keys = {"pd": "pd-history", "ead": "ead-history", "lgd": "lgd-history",
                "review": "lgd-review", "framework": "framework"}
comment_agreement = all(" ".join(actual[f"comment/{key}"]["original_text"].split()) ==
                        golden["notes"][golden_key][1] for key, golden_key in comment_keys.items())
matrix_agreement = all(actual[f"comment/matrix-{key}"]["original_text"] == golden["notes"][golden_key][1]
                       for key, golden_key in (("mortgage", "regulatory-basis"), ("nz", "nz-separation")))

for name, relations in (("baseline", baseline), ("refined", refined)):
    for table, rows in relations.items():
        (config.output_root / f"{name}-{table}.json").write_text(json.dumps(rows.to_dicts(), indent=2, default=str))

def loss_basis(relations):
    return [row for row in relations["attributes"].to_dicts()
            if row["owner"] == "cell/actual_lgd" and row["name"] == "loss_basis"]

summary = {"status": "DISPOSABLE SPIKE — shape evidence only", "root": str(config.output_root),
    "occurrences": len(actual), "numeric_cells": baseline["values"].count_rows(),
    "kinds": sorted({r["kind"] for r in actual.values()}),
    "golden_agreement": {"five_numbers": numeric_agreement, "five_comments": comment_agreement,
                         "matrix_evidence": matrix_agreement},
    "nz_pre_framework_token": actual["matrix/cell/nz/2"]["original_text"],
    "baseline_loss_basis": loss_basis(baseline), "refined_loss_basis": loss_basis(refined),
    "same_persisted_numbers": baseline["values"].to_dicts() == refined["values"].to_dicts(),
    "reconformance_inputs": [path.name, revision_path.name]}
(config.output_root / "summary.json").write_text(json.dumps(summary, indent=2))
shutil.copytree(Path(__file__).parent, config.output_root / "disposable-code",
                ignore=shutil.ignore_patterns("__pycache__"))
print(json.dumps(summary, indent=2))
print(baseline["values"].select("id", "original_text", "source_number", "normalised_value").to_polars())
