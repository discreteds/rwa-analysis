"""Capture selected 2024 mortgages and inspect disclosure structure across vintages.

Run: uv run python -i examples/historical_mortgages.py
Inspect sessions, publications, master_publication, output, source_tables,
field_inventory, field_paths, field_timing, field_bands and field_mappings.
Every invocation retains a fresh output directory.
"""

import json
from dataclasses import fields, replace
from pathlib import Path
from tempfile import mkdtemp

import mountainash as ma

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.composition import build_consolidator, build_session
from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline
from rwa_analysis.domains.source_tables.reconstruction import reconstruct_source_tables
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings, ProjectSettings
from rwa_analysis.storage.manifests import CatalogueSelection

root = Path(__file__).resolve().parents[1]
data_root = Path(mkdtemp(prefix="historical-mortgages-", dir="/tmp/opencode"))
print(f"Retained output directory: {data_root}", flush=True)
selection = CatalogueSelection(
    release_path="catalogue/releases/historical-mortgages-v1.json"
)
catalogue = load_catalogue(root / selection.release_path)
sessions, publications = {}, []
for org, day in (
    ("cba", "2024-06-30"),
    ("westpac", "2024-09-30"),
    ("nab", "2024-09-30"),
    ("anz", "2024-09-30"),
):
    session = build_session(
        OrganisationSettings(
            project_root=root,
            organisation_id=org,
            bronze_root=data_root / "bronze",
            manifest_root=data_root / "manifests",
            staging_path=data_root / "silver" / f"{org}.duckdb",
        )
    )
    dates = (day, "2025-09-30") if org == "westpac" else (day,)
    bundles = session.extract(
        tuple(
            DocumentSelection(
                f"extractions/au/{org}/{d}/aps330/extract.py",
                f"raw/{org}-{d}-aps330.pdf",
            )
            for d in dates
        )
    )
    inputs = session.load_bronze(session.save_bronze(bundles, "historical-review"))
    candidate = session.conform(inputs, catalogue=selection)
    if org == "westpac":
        candidate = replace(
            candidate, source_tables=SourceTablePipeline().conform(inputs, catalogue)
        )
    publication = session.publish(candidate, revision=f"{org}-historical-review")
    sessions[org] = session
    publications.append(publication)
    print(
        f"Published {org}: {candidate.source_tables.cells.count_rows()} source cells",
        flush=True,
    )

master = build_consolidator(
    ProjectSettings(
        project_root=root,
        bronze_root=data_root / "bronze",
        manifest_root=data_root / "manifests",
        master_path=data_root / "silver/master.duckdb",
    )
)
master_publication = master.consolidate(
    tuple(publications), revision="historical-review"
)
output = master.store.read(master_publication)
source = output.source_tables
source_tables = reconstruct_source_tables(source)
tables = master.reconstruct(master_publication)

# Field presence comes from published fields, including all-blank or unmapped fields.
# A field can have multiple definitions; unique combinations retain that distinction.
keys = ["silver_revision_id", "table_id"]
field_inventory = (
    source.fields.join(
        source.tables.select(
            *keys,
            "organisation_id",
            "document_date",
            "source_date_label",
            "source_title",
            "source_portfolio_label",
            "bundle_key",
            "output_version",
        ),
        on=keys,
    )
    .join(
        source.meanings.select(
            *keys,
            "field_id",
            "catalogue_release_id",
            "concept_revision_ref",
            "measure_revision_ref",
        ).unique(),
        on=[*keys, "field_id"],
        how="left",
    )
    .with_columns(
        ma.when(ma.col("measure_revision_ref").is_null())
        .then(ma.lit("unresolved"))
        .otherwise(ma.lit("mapped; inspect attributes"))
        .alias("definition_status")
    )
    .sort("organisation_id", "document_date", "table_id", "position")
)

# Ordered source paths, timing and bands are independently joinable inventories.
field_paths = (
    source.references.filter(
        (ma.col("owner_kind") == "field") & (ma.col("member") == "header_path_refs")
    )
    .select(
        *keys,
        ma.col("owner_id").alias("field_id"),
        "position",
        ma.col("target_id").alias("axis_id"),
    )
    .join(
        source.axes.select(*keys, "axis_id", "kind", "source_label"),
        on=[*keys, "axis_id"],
    )
    .sort("table_id", "field_id", "position")
)
field_timing = (
    source.cells.select(*keys, "cell_id", "field_id")
    .join(source.temporal_bindings, on=[*keys, "cell_id"], how="left")
    .join(
        source.temporal_descriptors.rename({"descriptor_id": "descriptor_ref"}),
        on=[*keys, "descriptor_ref"],
        how="left",
    )
)
field_bands = (
    source.cells.select(*keys, "cell_id", "field_id")
    .join(
        source.references.filter(
            (ma.col("owner_kind") == "cell") & (ma.col("member") == "segment_refs")
        ).select(
            *keys,
            ma.col("owner_id").alias("cell_id"),
            ma.col("target_id").alias("band_id"),
        ),
        on=[*keys, "cell_id"],
        how="left",
    )
    .join(source.bands, on=[*keys, "band_id"], how="left")
)
field_mappings = source.mapping_refs

readback = data_root / "readback"
readback.mkdir()
for member in fields(source):
    getattr(source, member.name).to_polars().write_parquet(
        readback / f"source_{member.name}.parquet"
    )
for name, relation in (
    ("field_inventory", field_inventory),
    ("field_paths", field_paths),
    ("field_timing", field_timing),
    ("field_bands", field_bands),
):
    relation.to_polars().write_parquet(readback / f"{name}.parquet")
for name, table in source_tables.items():
    table.frame.write_parquet(readback / f"{name.replace('/', '__')}.parquet")

report = {
    "root": str(data_root),
    "source_tables": len(source_tables),
    "source_cells": source.cells.count_rows(),
    "body_cells": source.cells.join(
        source.fields.filter(ma.col("source_form") == "table_body").select(
            *keys, "field_id"
        ),
        on=[*keys, "field_id"],
    ).count_rows(),
    "note_cells": source.cells.join(
        source.fields.filter(ma.col("source_form") == "note").select(*keys, "field_id"),
        on=[*keys, "field_id"],
    ).count_rows(),
    "native_and_legacy_frames": len(tables),
    "cr6_rows": output.cr6.observations.count_rows(),
    "cr9_rows": output.cr9.observations.count_rows(),
}
(data_root / "result.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
print(field_inventory.to_polars())
