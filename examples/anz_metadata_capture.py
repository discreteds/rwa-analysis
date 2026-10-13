"""Checkpoint A: ANZ v4 capture, persisted context and saved-only interpretation.

Run: uv run python -i examples/anz_metadata_capture.py
The fresh /tmp/opencode output retains Bronze, both catalogues and DuckDB readback.
"""

import json
import shutil
from pathlib import Path
from tempfile import mkdtemp

import mountainash as ma

from rwa_analysis.composition import build_session
from rwa_analysis.domains.source_tables.reconstruction import reconstruct_source_tables
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings
from rwa_analysis.storage.manifests import CatalogueSelection

root = Path(__file__).resolve().parents[1]
data_root = Path(mkdtemp(prefix="anz-metadata-checkpoint-a-", dir="/tmp/opencode"))
print(f"Retained output directory: {data_root}", flush=True)
authoring = data_root / "authoring"
shutil.copytree(root / "extractions/au/anz/2023-09-30/aps330", authoring)
pdf = data_root / "source.pdf"
shutil.copyfile(root / "raw/anz-2023-09-30-aps330.pdf", pdf)
catalogue_root = data_root / "catalogue"
shutil.copytree(root / "catalogue", catalogue_root)
original_release = catalogue_root / "releases/historical-mortgages-v2.json"
session = build_session(
    OrganisationSettings(
        project_root=root,
        organisation_id="anz",
        bronze_root=data_root / "bronze",
        staging_path=data_root / "anz.duckdb",
        manifest_root=data_root / "manifests",
    )
)
result = session.run(
    documents=(DocumentSelection(str(authoring / "extract.py"), str(pdf)),),
    catalogue=CatalogueSelection(release_path=str(original_release)),
    run_name="metadata-proof",
    revision="original",
)
manifest = session.silver.read_manifest(result.publication)
shutil.rmtree(authoring)
pdf.unlink()

# The review records the paragraph above Retail Portfolios as wholesale evidence;
# its applicability to mortgages remains unresolved. This is retained interpretation,
# not a mutation of the captured paragraph or a newly extracted value.
scope = {
    "targets": [
        {
            "bundle_key": "au/anz/2023-09-30/aps330",
            "scope": None,
            "kind": "comment",
            "local_id": "lgd-review",
            "output_version": "metadata-proof",
        }
    ]
}
common = {
    "created_on": "2026-10-13",
    "effective_from": None,
    "effective_to": None,
    "scope": scope,
}
members = [
    {
        **common,
        "id": "anz-review",
        "revision_id": "anz-review@1",
        "attributes": [
            {
                "name": "qualification_meaning",
                "value": "wholesale historical LGD review",
                "status": "established",
            }
        ],
    },
    {
        **common,
        "id": "anz-review-refinement",
        "revision_id": "anz-review@2",
        "attributes": [
            {
                "name": "qualification_meaning",
                "value": "wholesale review; mortgage applicability unresolved",
                "status": "established",
            }
        ],
        "overrides_refs": [{"kind": "mapping", "revision_id": "anz-review@1"}],
        "evidence_refs": [
            {
                "bundle_key": "au/anz/2023-09-30/aps330",
                "document_id": "anz-2023-09-30-aps330",
                "dataset_id": "",
                "kind": "comment",
                "ref_id": "lgd-review",
            }
        ],
    },
]
(catalogue_root / "checkpoint-refinement.json").write_text(
    json.dumps({"schema_version": "cr6-v1", "members": members}, indent=2)
)
release = json.loads(original_release.read_text())
release["id"] = "anz-checkpoint-refinement"
release["selection"].extend(
    {
        "path": "checkpoint-refinement.json",
        "kind": "mapping",
        "revision_id": member["revision_id"],
    }
    for member in members
)
refined_release = catalogue_root / "releases/anz-checkpoint-refinement.json"
refined_release.write_text(json.dumps(release, indent=2))
inputs = session.load_bronze(manifest.selection.bronze_refs)
candidate = session.conform(
    inputs, catalogue=CatalogueSelection(release_path=str(refined_release))
)
publication = session.publish(candidate, revision="saved-only-refinement")
output = session.silver.read(publication).source_tables
tables = reconstruct_source_tables(output)
print(
    f"Schema: {inputs[0].bundle.schema_version}; tables: {output.tables.count_rows()}; financial cells: {output.cells.count_rows()}"
)
print(
    output.occurrences.filter(ma.col("kind") == "comment")
    .select("local_id", "source_text")
    .to_polars()
)
print(
    output.attributes.filter(
        (ma.col("owner_id") == "lgd-review")
        & (ma.col("name") == "qualification_meaning")
    ).to_polars()
)
print(f"Saved-only publication: {publication.database}")
