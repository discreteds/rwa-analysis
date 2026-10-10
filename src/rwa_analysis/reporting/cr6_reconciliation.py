"""Read-only source/Bronze/persisted-Silver review; no accounting adjustments."""

import json
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256
from html import escape
from pathlib import Path

import mountainash as ma
import pdfplumber
import polars as pl
from mountainash_data import IbisBackend

from rwa_analysis.catalogue.resolve import resolve_field
from rwa_analysis.extraction.models import SourceReference, source_objects
from rwa_analysis.normalization.cr6 import (
    interpretation,
    lineage,
    metadata_rows,
    source_binding,
    source_ids,
)
from rwa_analysis.normalization.models import FIELD_MAP, KEYS, AppliedMapping, frame
from rwa_analysis.storage.manifests import _git, load_manifest

CSS = """
body {font:14px system-ui,sans-serif;margin:1.4rem;color:#182634;background:#fafafa}
a {color:#145b91} h1 {font-size:1.6rem} h2 {font-size:1.15rem}
.views {display:grid;grid-template-columns: minmax(360px,1fr) repeat(2,minmax(480px,1.5fr));gap:16px}
.view {min-width:0} .scroll {overflow:auto;max-height:85vh;border:1px solid #9aaab6;background:white}
table {border-collapse:collapse;font-size:12px;min-width:1350px;width:100%}
th,td {border:1px solid #b5c1ca;padding:8px;text-align:right;white-space:nowrap}
th {white-space:pre-line;background:#e7edf1;vertical-align:bottom}
thead {position:sticky;top:0;z-index:2} tbody th {text-align:left;min-width:145px}
.aggregate {font-weight:bold;border-top:3px solid #405869}
.shaded {background:#d2d5d8} .missing {box-shadow:inset 0 -3px #98aab9}
.difference {background:#ffe0d8;outline:2px solid #b93419;outline-offset:-2px}
small {display:block;color:#425766;font-size:10px;font-weight:normal}
img {max-width:100%;height:auto} figure {margin:0 0 20px} pre {white-space:pre-wrap;overflow-wrap:anywhere}
.notes {max-width:1200px} details {margin:12px 0} .status {padding:10px;background:#e7edf1}
@media print {.views {display:block}.scroll {max-height:none;overflow:visible} table {min-width:0;font-size:7px} th,td {padding:3px} .view {break-before:page} thead {position:static}}
"""


def text(value):
    return escape(str(value), quote=True)


def json_text(value):
    return json.dumps(value, default=str, ensure_ascii=False, indent=2)


def details(title, value):
    return f"<details><summary>{text(title)}</summary><pre>{text(json_text(value))}</pre></details>"


def document(title, body):
    return (
        f'<!doctype html><html lang="en"><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{text(title)}</title><style>{CSS}</style><body>{body}</body></html>"
    )


def read_published(warehouse, manifest_path, revision):
    if not warehouse.is_file():
        raise FileNotFoundError(warehouse)
    with IbisBackend(dialect="duckdb", database=str(warehouse), read_only=True) as db:

        def rows(name, namespace="silver"):
            return (
                ma.relation(
                    pl.from_arrow(db.table(name, namespace=namespace).to_pyarrow())
                )
                .collect()
                .to_dicts()
            )

        markers = rows("silver_publication", "ops")
        if (
            len(markers) != 1
            or markers[0]["status"] != "published"
            or markers[0]["silver_revision_id"] != revision
        ):
            raise ValueError(
                "Warehouse publication revision does not match requested revision"
            )
        if (
            markers[0]["manifest_sha256"]
            != sha256(manifest_path.read_bytes()).hexdigest()
        ):
            raise ValueError(
                "Warehouse publication manifest differs from requested manifest"
            )
        tables = {name: rows(name) for name in KEYS}
        if any(
            r["silver_revision_id"] != revision
            for rows_ in tables.values()
            for r in rows_
        ):
            raise ValueError("Persisted table revision differs from publication")
    return tables, markers[0]


def index_rows(rows, keys):
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in result:
            raise ValueError(f"Duplicate persisted identity: {key}")
        result[key] = row
    return result


def compare_metadata(name, expected, actual, findings):
    keys = KEYS[name]
    left, right = index_rows(expected, keys), index_rows(actual, keys)
    for key in sorted(left.keys() | right.keys()):
        a, b = left.get(key), right.get(key)
        if a != b:
            findings.append(
                {
                    "kind": "metadata",
                    "table": name,
                    "identity": key,
                    "expected": a,
                    "persisted": b,
                }
            )


def render_images(bundle, dataset, root, out):
    refs = [r for r in source_objects(dataset) if isinstance(r, SourceReference)]
    main = dataset.records[0].ead.source_reference.pdf_page
    pages = sorted({r.pdf_page for r in refs}, key=lambda p: (p != main, p))
    figures = []
    with pdfplumber.open(root / bundle.document.local_path) as pdf:
        for page in pages:
            name = f"{bundle.document.organisation_id}-pdf-{page}.png"
            pdf.pages[page - 1].to_image(resolution=110).save(out / "images" / name)
            printed = sorted(
                {r.printed_page for r in refs if r.pdf_page == page and r.printed_page}
            )
            caption = f"Original PDF p. {page}; printed " + (
                ", ".join(printed) if printed else "label not captured"
            )
            figures.append(
                f'<figure id="pdf-{page}"><a href="images/{text(name)}"><img src="images/{text(name)}" alt="{text(caption)}" loading="lazy"></a><figcaption>{text(caption)}</figcaption></figure>'
            )
    return figures[0], "".join(figures[1:])


def silver_cell(cell, obs, lin, meaning, valid_lineage):
    """Return numeric-derived display and exact source-scale value before rounding."""
    if obs is None:
        return "absent row", None, "absent row"
    if lin is None or meaning is None:
        return "absent field metadata", None, "absent field metadata"
    if not valid_lineage:
        return "lineage mismatch", None, "lineage mismatch"
    state = meaning["value_state"]
    value = obs.get(lin["field_key"])
    if state == "not_conformed":
        return "not_conformed", None, "not_conformed"
    if state == "source_missing":
        if (
            value is None
            and cell.value is None
            and lin["missing_reason"] == cell.missing_reason
        ):
            return cell.original_text, None, cell.missing_reason
        return "missingness mismatch", None, "missingness mismatch"
    if value is None:
        return "absent value", None, "absent value"
    if cell.value is None or not lin["unit_factor"]:
        return "availability mismatch", None, "availability mismatch"
    with localcontext() as ctx:
        ctx.prec = 80
        exact = Decimal(value) / Decimal(lin["unit_factor"])
        precision = lin["displayed_precision"]
        if precision is None:
            return "precision unresolved", exact, "precision unresolved"
        # Only punctuation conventions come from the token, never its digits.
        grouping = "," if "," in cell.original_text else ""
        token = format(exact, f"{grouping}.{precision}f")
        if "%" in cell.original_text:
            token += "%"
    return token, exact, state


def table_view(view, bundle, ds, tables, expected_lineage, findings):
    axes = {a.id: a for a in ds.axes}
    observations = index_rows(tables["observations"], ("observation_id",))
    lineages = index_rows(tables["lineage"], ("observation_id", "field_key"))
    meanings = index_rows(tables["interpretations"], ("observation_id", "field_key"))
    expected = index_rows(expected_lineage, ("observation_id", "field_key"))
    first = ds.records[0]
    sources = sorted(
        FIELD_MAP,
        key=lambda s: min(
            axes[c].order for c in source_binding(ds, first, s)[0].column_refs
        ),
    )
    headers = []
    for source in sources:
        binding, field = source_binding(ds, first, source)
        path = " / ".join(axes[a].source_label for a in field.header_path_refs)
        headers.append(
            f'<th title="{text(path)}">{text(field.source_label)}<small>{text(field.source_unit)} · {text(", ".join(binding.column_refs))}</small></th>'
        )
    result = [
        "<table><thead><tr><th>Source row / PD band</th>",
        *headers,
        "</tr></thead><tbody>",
    ]
    for record in sorted(ds.records, key=lambda r: axes[r.source_row_ref].order):
        oid = source_ids(bundle, ds, record)
        axis = axes[record.source_row_ref]
        aggregate = (
            record.source_row_role in ("subtotal", "aggregate", "portfolio_aggregate")
            or record.record_id == "portfolio-aggregate"
        )
        result.append(
            f'<tr class="{"aggregate" if aggregate else ""}"><th>{text(axis.source_label)}<small>{text(axis.source_reference.row or axis.id)} · {text(record.source_row_role)}</small></th>'
        )
        for source in sources:
            target = FIELD_MAP[source]
            cell = getattr(record, source)
            binding, field = source_binding(ds, record, source)
            lin = lineages.get((oid, target))
            meaning = meanings.get((oid, target))
            status, exact = cell.missing_reason or "present", cell.value
            token = cell.original_text
            mismatch = False
            if view == "silver":
                token, exact, status = silver_cell(
                    cell,
                    observations.get((oid,)),
                    lin,
                    meaning,
                    lin == expected.get((oid, target)),
                )
                mismatch = exact != cell.value or status not in (
                    "present",
                    cell.missing_reason,
                )
                if mismatch:
                    findings.append(
                        {
                            "kind": "value",
                            "observation_id": oid,
                            "field_key": source,
                            "source_value": str(cell.value)
                            if cell.value is not None
                            else None,
                            "reconstructed_value": str(exact)
                            if exact is not None
                            else None,
                            "source_token": cell.original_text,
                            "displayed": token,
                            "status": status,
                        }
                    )
            shaded = cell.value is None and any(
                a.value == "shaded" for a in field.attributes
            )
            classes = " ".join(
                c
                for c, enabled in (
                    ("shaded", shaded),
                    ("missing", cell.value is None),
                    ("difference", mismatch),
                )
                if enabled
            )
            tip = {
                "status": status,
                "exact_source_units": exact,
                "displayed_precision": cell.displayed_precision,
                "source": asdict(cell.source_reference),
                "qualifications": [
                    *binding.qualification_refs,
                    *field.qualification_refs,
                ],
            }
            if view == "silver":
                tip["interpretation"] = meaning
            result.append(
                f'<td class="{classes}" data-view="{view}" data-observation-id="{text(oid)}" data-field-key="{text(source)}" title="{text(json_text(tip))}">{text(token)}</td>'
            )
        result.append("</tr>")
    result.append("</tbody></table>")
    return "".join(result)


def render_cr6_reconciliation(
    manifest_path: Path, project_root: Path, warehouse_path: Path, output_dir: Path
) -> Path:
    """Return index.html for the manifest's persisted, published revision."""
    manifest, bundles, catalogue, _ = load_manifest(
        manifest_path, project_root, verify_runtime=False
    )
    revision = manifest.request.revision_id
    tables, marker = read_published(warehouse_path, manifest_path, revision)
    # Every artifact directory is immutable, whether reviewed yet or not.
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "images").mkdir()
    findings, links = [], []
    expected = metadata_rows(bundles, manifest.request.bronze_refs, revision)
    expected.update(lineage=[], interpretations=[], applied_mappings=[])
    identities = []
    for bundle, ref in zip(bundles, manifest.request.bronze_refs, strict=True):
        for ds in bundle.datasets:
            for record in ds.records:
                oid = source_ids(bundle, ds, record)
                cid = source_ids(bundle, ds)
                identities.append(
                    {
                        "silver_revision_id": revision,
                        "observation_id": oid,
                        "context_id": cid,
                        "segment_id": f"{cid}/{record.source_segment_memberships[0]}"
                        if record.source_segment_memberships
                        else None,
                        "source_record_id": record.record_id,
                        "source_row_ref": record.source_row_ref,
                        "source_row_role": record.source_row_role,
                    }
                )
                for source, target in FIELD_MAP.items():
                    meaning = resolve_field(catalogue, ds, record, source)
                    expected["lineage"].append(
                        lineage(
                            revision,
                            oid,
                            target,
                            bundle,
                            ref,
                            ds,
                            record,
                            source,
                            meaning,
                        )
                    )
                    expected["interpretations"].append(
                        interpretation(
                            revision,
                            oid,
                            target,
                            getattr(record, source),
                            meaning,
                            catalogue,
                        )
                    )
                    expected["applied_mappings"].extend(
                        AppliedMapping(
                            revision, oid, target, catalogue.id, m.revision_id
                        )
                        for m in meaning.mapping_refs
                    )
    identity_keys = tuple(identities[0]) if identities else tuple(KEYS["observations"])
    compare_metadata(
        "observations",
        identities,
        [{k: r[k] for k in identity_keys} for r in tables["observations"]],
        findings,
    )
    for name, rows in expected.items():
        expected[name] = frame(name, rows).to_dicts()
        compare_metadata(name, expected[name], tables[name], findings)
    for bundle in bundles:
        for ds in bundle.datasets:
            name = f"{bundle.document.organisation_id}-{bundle.document.document_reporting_date}-cr6.html"
            title = f"{bundle.document.organisation_id.upper()} · {ds.context.source_date_label} · {ds.context.source_portfolio_label}"
            main, supporting = render_images(bundle, ds, project_root, output_dir)
            bronze = table_view(
                "bronze", bundle, ds, tables, expected["lineage"], findings
            )
            silver = table_view(
                "silver", bundle, ds, tables, expected["lineage"], findings
            )
            notes = "".join(
                f'<li id="note-{text(q.id)}"><b>{text(q.id)}</b>: {text(q.source_text)}{details("Applicability and source location", asdict(q))}</li>'
                for q in ds.qualifications
            )
            headings = " · ".join(
                a.source_label
                for a in sorted(ds.axes, key=lambda a: a.order)
                if a.axis == "header"
            )
            context = ds.context
            scope = " · ".join(
                f"{label}: {item.value or 'unresolved'} ({item.status})"
                for label, item in (
                    ("Entity", context.reporting_entity),
                    ("Consolidation", context.consolidation_scope),
                    ("Regulatory approach", context.regulatory_scope),
                    ("Geography", context.geography),
                    ("Currency", context.currency),
                )
            )
            body = f"""<a href="index.html">Review index</a><h1>{text(title)}</h1>
<p>{text(ds.context.source_title)}</p><p>{text(headings)}</p>
<p>{text(scope)}</p>
<p class="status">Published Silver: {text(revision)}. Automated review findings are not visual approval.
<a href="differences.json">Exact differences and metadata findings</a> · <a href="review-inputs.json">Input / renderer provenance</a></p>
<p>Legend: grey shading only where captured; blue underline = source missing (hover for reason);
red = exact mismatch, including errors hidden by display rounding. Blank and dash tokens are retained.
Hover each Silver cell for exact value, precision, missingness and established/unresolved/conflicting interpretation attributes.
Scroll each table horizontally; both retain all twelve field positions. Source row and column identifiers appear beside labels.</p>
<div class="views"><section class="view"><h2>Original source PDF</h2><div class="scroll">{main}</div></section>
<section class="view"><h2>Bronze · captured source tokens</h2><div class="scroll">{bronze}</div></section>
<section class="view"><h2>Silver · persisted numeric values in source units</h2><div class="scroll">{silver}</div></section></div>
<section class="notes"><h2>Source context, bands and relationships</h2>
{details("Captured context (entity, dates, scope, units)", asdict(ds.context))}
{details("Segmentation, exact bounds and inclusion", [asdict(s) for s in ds.segmentations])}
{details("Aggregate / subset relationships; do not double-count", [asdict(r) for r in ds.relationships])}
{details("Full captured axes, field headings and bindings", {k: asdict(ds)[k] for k in ("axes", "published_fields", "bindings")})}
<h2>Applicable source notes and definitions</h2><ul>{notes}</ul>
<h2>Persisted Silver metadata and interpretations</h2>
{details("Published metadata (including unresolved meanings)", {k: [r for r in rows if bundle.bundle_key in json_text(r)] for k, rows in tables.items() if k != "observations"})}
<h2>Surrounding / cross-table source evidence</h2>{supporting}</section>
<script>
const tables = [...document.querySelectorAll('.view')].slice(1).map(x => x.querySelector('.scroll'));
for (const pane of tables) pane.addEventListener('scroll', () => {{
  for (const other of tables) if (other !== pane && other.scrollLeft !== pane.scrollLeft) other.scrollLeft = pane.scrollLeft;
}});
</script>"""
            (output_dir / name).write_text(document(title, body))
            links.append(
                f'<li><a href="{text(name)}">{text(title)}</a> — {len(ds.records)} rows × {len(FIELD_MAP)} fields per reconstruction</li>'
            )
    (output_dir / "differences.json").write_text(json_text(findings) + "\n")
    repo = Path(__file__).resolve().parents[3]
    code = _git(repo, "rev-parse", "HEAD").decode().strip()
    changed = (
        _git(repo, "status", "--porcelain", "--", "src/rwa_analysis").decode().strip()
    )
    inputs = {
        "created_at": datetime.now(UTC).isoformat(),
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
        "publication": marker,
        "manifest": manifest.model_dump(mode="json"),
        "renderer_revision": code,
        "renderer_dirty": bool(changed),
        "renderer_source_sha256": {
            p.relative_to(repo).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in sorted((repo / "src/rwa_analysis").rglob("*.py"))
        },
        "visual_review": "Not performed by renderer. Consult the separate review.md when supplied; automated findings are not visual approval.",
    }
    (output_dir / "review-inputs.json").write_text(json_text(inputs) + "\n")
    index = output_dir / "index.html"
    index.write_text(
        document(
            f"CR6 review · {revision}",
            f'<h1>CR6 source / Bronze / Silver review</h1><p>Published revision: {text(revision)}; renderer: {text(code)} (dirty: {bool(changed)}).</p><p>{len(findings)} exact-value / metadata findings. No totals or averages recomputed. Automated rendering does not imply visual approval; consult the separate review.md when supplied.</p><ul>{"".join(links)}</ul><a href="differences.json">Differences</a> · <a href="review-inputs.json">Provenance</a>'
            + details("Finding summary", findings),
        )
    )
    return index
