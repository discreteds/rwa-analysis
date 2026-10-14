"""V4 transport owns address/snapshot retention, independently of PDF accuracy."""

from dataclasses import replace
from decimal import Decimal

from rwa_analysis.extraction.definitions import CapturedBundle
from rwa_analysis.storage.bronze import BronzeStore


def test_capture_snapshot_and_shared_occurrences_survive_saved_transport(
    cba_2024_bundle, tmp_path
):
    # A dropped snapshot or kind/scope qualifier must fail at saved transport.
    from datetime import date

    from rwa_analysis.catalogue.models import ConceptRevision, SemanticAttribute
    from rwa_analysis.extraction.definitions import (
        CapturedFragment,
        CaptureSnapshot,
        CellBinding,
        ContextDefinition,
        DomainFieldBinding,
        OccurrenceBinding,
        OccurrenceLink,
        OccurrenceRef,
        PhysicalBinding,
        PhysicalParameter,
    )

    old = cba_2024_bundle
    field = OccurrenceRef(
        old.bundle_key, old.datasets[0].id, "field", "same", "capture-proof"
    )
    axis = replace(field, kind="column")
    comment = OccurrenceRef(old.bundle_key, None, "comment", "shared")
    evidence = old.datasets[0].cells[0].value.source_reference
    snapshot = CaptureSnapshot(
        "capture@1",
        (PhysicalBinding("physical@1", "paragraph", (PhysicalParameter("page", 4),)),),
        (
            ContextDefinition(
                "context@1", (SemanticAttribute("AUD", "established", name="currency"),)
            ),
        ),
        (
            OccurrenceBinding(
                field,
                context_refs=("context@1",),
                cell=CellBinding(
                    "same",
                    "row",
                    "column",
                    missing_reason="not_applicable",
                    missing_tokens=("N/A",),
                    source_row_role="band",
                    source_aggregation_scope=("mortgage-block",),
                ),
            ),
            OccurrenceBinding(axis),
            OccurrenceBinding(
                comment,
                links=(
                    OccurrenceLink("qualifies", field),
                    OccurrenceLink("qualifies", axis),
                ),
            ),
        ),
        semantic_definitions=(
            ConceptRevision(
                id="population",
                revision_id="population@1",
                created_on=date(2026, 10, 13),
                effective_from=None,
                effective_to=None,
                name="Retained population",
                definition="Independent transport definition",
                category="population",
            ),
        ),
        domain_bindings=(
            DomainFieldBinding(
                replace(field, kind="cell"),
                "cr6",
                "original-record",
                "ead",
                "original-binding",
            ),
        ),
    )
    bundle = CapturedBundle(
        old.document,
        old.bundle_key,
        old.extractor_path,
        old.datasets,
        snapshot,
        (CapturedFragment("physical@1", "shared", "Shared wording", evidence),),
    )
    store = BronzeStore(tmp_path)
    restored = store.load(store.save(bundle, "capture-proof")).bundle
    assert restored.schema_version == "disclosure-v4"
    assert restored.snapshot == snapshot
    assert restored.fragments[0].text == "Shared wording"
    assert restored.datasets[0].cells[0].value.value == Decimal(175918)
    assert len({b.ref for b in restored.snapshot.occurrences}) == 3
    assert restored.snapshot.occurrences[-1].links[1].target.kind == "column"
    assert (
        restored.snapshot.semantic_definitions[0].definition
        == "Independent transport definition"
    )
