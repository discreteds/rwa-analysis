"""Offline single-writer commands for the four reviewed CR6 source bundles."""

import json
from contextlib import contextmanager
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Annotated

import mountainash as ma
import polars as pl
import typer
from mountainash_data import IbisBackend

from rwa_analysis.extraction.runner import run_extractor
from rwa_analysis.storage.bronze import save_bronze
from rwa_analysis.storage.manifests import (
    RebuildRequest,
    _git,
    _implementation,
    load_manifest,
    save_manifest,
)
from rwa_analysis.storage.silver import rebuild as rebuild_silver

app = typer.Typer(no_args_is_help=True, help=__doc__)
Root = Annotated[
    Path, typer.Option(help="Project inputs root; relative paths resolve here.")
]
Warehouse = Annotated[
    Path | None,
    typer.Option(help="Defaults to data/warehouse.duckdb under project root."),
]

# Deliberate inventory: no guessed document or arbitrary extractor dispatch.
REVIEWED = {
    "au/cba/2025-06-30/aps330": (
        "extractions/au/cba/2025-06-30/aps330/extract.py",
        "raw/cba-2025-06-30-aps330.pdf",
    ),
    "au/westpac/2025-09-30/aps330": (
        "extractions/au/westpac/2025-09-30/aps330/extract.py",
        "raw/westpac-2025-09-30-aps330.pdf",
    ),
    "au/nab/2025-09-30/aps330": (
        "extractions/au/nab/2025-09-30/aps330/extract.py",
        "raw/nab-2025-09-30-aps330.pdf",
    ),
    "au/anz/2025-09-30/aps330": (
        "extractions/au/anz/2025-09-30/aps330/extract.py",
        "raw/anz-2025-09-30-aps330.pdf",
    ),
}


@contextmanager
def errors(context):
    try:
        yield
    except Exception as error:
        message = (
            f"Already exists; choose a new explicit version/revision: {error}"
            if isinstance(error, FileExistsError)
            else str(error)
        )
        typer.echo(f"Error [{context}]: {message}", err=True)
        raise typer.Exit(1) from error


def rooted(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


@app.command()
def reconcile_tables(
    manifest: Annotated[Path, typer.Option()],
    output: Annotated[Path, typer.Option()],
    project_root: Root = Path("."),
    warehouse: Warehouse = None,
):
    """Render local source/Bronze/persisted-Silver pages without publication."""
    from rwa_analysis.reporting.cr6_reconciliation import render_cr6_reconciliation

    with errors(f"reconcile {manifest}"):
        root = project_root.resolve(strict=True)
        typer.echo(
            render_cr6_reconciliation(
                rooted(root, manifest),
                root,
                rooted(root, warehouse or Path("data/warehouse.duckdb")),
                rooted(root, output),
            )
        )


def committed_selection(root: Path, paths: tuple[str, ...]) -> str:
    """Verify executing package and selected input bytes against a real commit.

    Separate data roots can use the installed checkout's Git history. Deleted
    PDFs/extractors are deliberately irrelevant to manifest rebuild/inspection.
    """
    installed = Path(__file__).resolve().parents[2]
    repo = root if (root / ".git").exists() else installed
    revision = _git(repo, "rev-parse", "HEAD").decode().strip()
    _implementation(root, revision)
    for relative in paths:
        path = root / relative
        selected = (
            sorted(
                p
                for p in path.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts
            )
            if path.is_dir()
            else [path]
        )
        tracked = (
            _git(repo, "ls-tree", "-r", "--name-only", revision, relative)
            .decode()
            .splitlines()
        )
        if {p.relative_to(root).as_posix() for p in selected} != set(tracked):
            raise ValueError(
                f"Commit selected input files before publication: {relative}"
            )
        for file in selected:
            name = file.relative_to(root).as_posix()
            if file.read_bytes() != _git(repo, "show", f"{revision}:{name}"):
                raise ValueError(
                    f"Selected input differs from committed revision; commit before publication: {name}"
                )
    return revision


@app.command()
def extract(
    bundle: Annotated[str, typer.Option()],
    output_version: Annotated[str, typer.Option()],
    project_root: Root = Path("."),
):
    """Extract a reviewed PDF into a new immutable Bronze version."""
    with errors(f"extract {bundle}"):
        root = project_root.resolve(strict=True)
        if bundle not in REVIEWED:
            raise ValueError(
                f"Unknown reviewed bundle {bundle!r}; select one of: {', '.join(REVIEWED)}"
            )
        script, pdf = REVIEWED[bundle]
        for path in (root / pdf, root / script):
            if not path.is_file():
                raise FileNotFoundError(f"Restore extraction prerequisite: {path}")
        revision = committed_selection(root, (script,))
        captured = run_extractor(root / script, root / pdf)
        if captured.bundle_key != bundle:
            raise ValueError(f"{script}: returned wrong bundle {captured.bundle_key}")
        ref = save_bronze(captured, output_version, root, revision)
        typer.echo(
            root / "data/bronze" / ref.bundle_key / ref.output_version / "bundle.json"
        )


@app.command()
def manifest(
    request: Annotated[Path, typer.Option()],
    project_root: Root = Path("."),
):
    """Freeze a committed request, catalogue and saved Bronze selection."""
    with errors(f"manifest {request}"):
        root = project_root.resolve(strict=True)
        path = rooted(root, request).resolve(strict=True)
        selected = RebuildRequest.model_validate_json(path.read_bytes())
        revision = committed_selection(
            root, (path.relative_to(root).as_posix(), "catalogue")
        )
        typer.echo(save_manifest(selected, root, revision))


@app.command()
def rebuild(
    manifest: Annotated[Path, typer.Option()],
    project_root: Root = Path("."),
    warehouse: Warehouse = None,
):
    """Rebuild Silver from retained inputs; never reads PDFs or extractors."""
    with errors(f"rebuild {manifest}"):
        root = project_root.resolve(strict=True)
        target = rooted(root, warehouse or Path("data/warehouse.duckdb"))
        revision = rebuild_silver(rooted(root, manifest), root, target)
        typer.echo(f"Published {revision}: {target}")


def inspect_observation(root: Path, warehouse: Path, observation: str) -> dict:
    if not warehouse.is_file():
        raise FileNotFoundError(
            f"Warehouse missing; run rwa rebuild first: {warehouse}"
        )
    with IbisBackend(dialect="duckdb", database=str(warehouse)) as db:

        def rows(name, predicate=None, namespace="silver"):
            relation = ma.relation(
                pl.from_arrow(db.table(name, namespace=namespace).to_pyarrow())
            )
            if predicate is not None:
                relation = relation.filter(predicate)
            return relation.collect().to_dicts()

        markers = rows("silver_publication", namespace="ops")
        if len(markers) != 1 or markers[0]["status"] != "published":
            raise ValueError("Warehouse has no unique successful publication")
        marker = markers[0]
        path = rooted(root, Path(marker["manifest_path"]))
        if sha256(path.read_bytes()).hexdigest() != marker["manifest_sha256"]:
            raise ValueError(f"Publication manifest changed: {path}")
        manifest, bundles, catalogue, supporting = load_manifest(path, root)
        if manifest.request.revision_id != marker["silver_revision_id"]:
            raise ValueError("Publication revision differs from manifest")
        predicate = (ma.col("observation_id") == observation) & (
            ma.col("silver_revision_id") == marker["silver_revision_id"]
        )
        selected = rows("observations", predicate)
        if len(selected) != 1:
            raise ValueError(
                f"Observation not found in published revision: {observation}"
            )
        record = selected[0]
        result = {
            name: rows(name, predicate)
            for name in ("interpretations", "applied_mappings", "lineage")
        }
        result["observation"] = record
        result["context"] = rows(
            "contexts", ma.col("context_id") == record["context_id"]
        )[0]
        result["relationships"] = rows(
            "relationships",
            (ma.col("parent_observation_id") == observation)
            | (ma.col("child_observation_id") == observation),
        )
        result["segment"] = (
            rows("segments", ma.col("segment_id") == record["segment_id"])
            if record["segment_id"]
            else []
        )
    # The retained catalogue has full provenance closure, including evidence
    # outside the published scope. Return its original definitions and evidence,
    # not guessed interpretations reconstructed from adjacent numeric columns.
    result["catalogue"] = asdict(catalogue)
    result["source_evidence"] = []
    for bundle in (*bundles, *supporting):
        source = asdict(bundle)
        for dataset in source["datasets"]:
            dataset["records"] = [
                r
                for r in dataset["records"]
                if f"{bundle.bundle_key}/{dataset['id']}/{r['record_id']}"
                == observation
            ]
        result["source_evidence"].append(source)
    return result


@app.command(name="inspect")
def inspect_command(
    observation: Annotated[str, typer.Option()],
    project_root: Root = Path("."),
    warehouse: Warehouse = None,
):
    """Print exact Decimal strings, typed counts, statuses and archived evidence."""
    with errors(f"inspect {observation}"):
        root = project_root.resolve(strict=True)
        result = inspect_observation(
            root, rooted(root, warehouse or Path("data/warehouse.duckdb")), observation
        )
        typer.echo(json.dumps(result, default=str, indent=2))
