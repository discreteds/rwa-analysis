"""Real Westpac PDF → mixed Bronze → persisted CR6/CR9 → source-unit tables.

Run with explicit output locations, for example:
uv run python examples/westpac_cr9.py --data-root /tmp/opencode/westpac-cr9 --run-name review-1
"""

import argparse
from pathlib import Path

import polars as pl

from rwa_analysis.composition import build_session
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings
from rwa_analysis.storage.manifests import CatalogueSelection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--run-name", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = args.data_root.resolve()
    session = build_session(
        OrganisationSettings(
            project_root=root,
            organisation_id="westpac",
            bronze_root=data / "bronze",
            manifest_root=data / "manifests",
            staging_path=data / "silver/westpac.duckdb",
        )
    )
    result = session.run(
        documents=(
            DocumentSelection(
                "extractions/au/westpac/2025-09-30/aps330/extract.py",
                "raw/westpac-2025-09-30-aps330.pdf",
            ),
        ),
        catalogue=CatalogueSelection(release_path="catalogue/releases/cr6-cr9-v1.json"),
        run_name=args.run_name,
        revision=args.run_name,
    )
    output = session.silver.read(result.publication)
    artifacts = data / "readback" / args.run_name
    artifacts.mkdir(parents=True, exist_ok=True)
    with pl.Config(trim_decimal_zeros=True, tbl_cols=13, tbl_width_chars=200):
        for key, frame in result.tables.items():
            name = key.rsplit("/", 1)[1]
            frame.write_parquet(artifacts / f"{name}.parquet")
            print(f"{name}: {frame.height} rows")
            print(frame)
        for member in ("temporal_descriptors", "temporal_bindings", "relationships"):
            frame = getattr(output.cr9, member).to_polars()
            frame.write_parquet(artifacts / f"cr9_{member}.parquet")
        print(output.cr9.temporal_descriptors.to_polars())
        print(
            output.cr9.relationships.to_polars()
            .select(
                "parent_observation_id",
                "parent_field_key",
                "child_observation_id",
                "child_field_key",
                "relationship_kind",
            )
            .head(1)
        )
    print(f"CR6 observations: {output.cr6.observations.count_rows()}")
    print(f"CR9 observations: {output.cr9.observations.count_rows()}")
    print(
        f"Temporal roles: {sorted(set(output.cr9.temporal_bindings.to_polars()['role']))}"
    )
    print(f"Publication: {result.publication}")
    print(f"Readback artifacts: {artifacts}")


if __name__ == "__main__":
    main()
