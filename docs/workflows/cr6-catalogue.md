# CR6 semantic catalogue

Task 5 implements the durable catalogue described by the
[layered contract](../04.planning/superpowers/specs/2026-10-10-layered-data-model.md)
and [contextual-mapping principle](../01.principles/b.data-semantics/layered-metric-definitions.md).
The JSON files under `catalogue/` are retained rebuild inputs outside Silver.
Create new revision/file paths for subsequent changes; retain earlier releases.

```python
from pathlib import Path
from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.catalogue.resolve import resolve_field

catalogue = load_catalogue(Path("catalogue/releases/cr6-v1.json"))
# dataset and record come from the selected saved Bronze bundle.
meaning = resolve_field(catalogue, dataset, record, "average_pd")
weighting = meaning.attribute("weighting")
```

## Seed and evidence

`cr6-v1` selects 18 concepts (including four result units), ten source-partial
measures, one already agreed interpretation, and 88 scoped mappings. The
relationship revision contract is available; this seed needs no invented
concept hierarchy. Concepts and mapping identities are distinct from Python
field names and from measure revision identities. Fields without a reusable
measure retain a concept, result unit and partial attributes.

The seed follows the reviewed
[CBA](../../extractions/au/cba/2025-06-30/aps330/review.md),
[Westpac](../../extractions/au/westpac/2025-09-30/aps330/review.md),
[NAB](../../extractions/au/nab/2025-09-30/aps330/review.md) and
[ANZ](../../extractions/au/anz/2025-09-30/aps330/review.md) disclosures:

- CBA PD references CBA's EAD measure and period-end weighting. LGD/CCF
  weighting and CBA's counted entity remain unresolved. CBA RWA includes
  overlays; density retains the unrounded-input qualification.
- NAB's PDF p. 48 agreement definition maps to arrangement count under the
  existing agreed principle. The decision record cites that authority and
  does not invent an interview date. Distinctness stays unresolved. Both
  RWA and density exclude overlays; pre-CRM exposure bases stay explicit.
- ANZ retains ANZ BH Pty Ltd, Level 2, AIRB, Suncorp exclusion and provisional
  geography. Mortgage counted entity is unresolved. Maturity retains both
  the RWA-use explanation and the separate disclosure modification.
  CMS2 overlay evidence remains attached to **unresolved** CR6 overlay
  applicability. No researcher-approved CR6 inference is available.
- Counts, monetary amounts, rates and years have distinct result units.
  Regulatory expected loss remains separate from credit provisions.

## Interfaces for Task 6

These refinements fit the existing `Cr6Dataset` and twelve-field Bronze row;
no shared extraction contract changed.

- `RevisionRef(kind, revision_id)` always pins an exact member revision.
  `CatalogueRelease.selection` contains immutable `(path, kind, revision_id)`
  selections; `members` contains their fully decoded frozen records in the
  same order. `member(ref)` resolves an internal reference. Loading checks
  reference closure, kinds, result-unit categories and dependency cycles.
  Selection retains history as well as executable revisions. At resolution an
  occurrence-matching, source-effective mapping supersedes its explicitly named
  predecessor mappings (transitively) for that occurrence. Historical members
  stay resolvable, and releases that select only the predecessors reproduce the
  earlier interpretation. Future or out-of-scope corrections do not deactivate
  an otherwise applicable predecessor. Supersession replaces the whole mapping;
  attribute-specific narrower overrides remain a separate mechanism.
- `EvidenceRef(bundle_key, document_id, dataset_id, kind, ref_id)` identifies
  a qualification, field, band, axis, context or relationship occurrence.
  Source text and page locations remain in Bronze, reached through this
  reference. **Task 6 must bind every external evidence reference used by
  the candidate to its selected Bronze inputs.** Loading a catalogue alone
  cannot establish that the external occurrence exists. Decision
  `authority_refs` identify the retained project record of an agreement.
- The existing resolver signature has no bundle argument. Applicability
  therefore uses the cell's document ID, exact dataset/template/portfolio,
  document date, observation interval and any declared entity, approach,
  published field, row or band restrictions. Candidate validation must also
  enforce the bundle/document association. Matching is conjunction, without
  label normalization or source-field-name-only fallback.
- `SemanticAttribute` is a typed scalar/reference assertion with a finite
  CR6 attribute vocabulary, per-attribute status and support. Measures and
  mappings compose immutable tuples of these assertions. A missing attribute
  returns an explicit unresolved assertion. `pd_band` references the retained
  typed Bronze band, preserving its exact bounds and inclusivity; it does not
  reconstruct bounds from labels. Aggregate roles have no fictitious band.
- Conflicts return `value=None`, `status="conflicting"`, both supports and
  typed `alternatives`. Conflicting concept/measure attributes leave their
  convenience references unset. Unknown information does not contradict
  known information; any provisional supporting assertion keeps the combined
  status provisional. A narrower mapping overrides only attributes it actually
  asserts, and only with declared, supported `overrides_refs`. File order does
  not choose an interpretation. `mapping_refs` retains applicable,
  non-superseded mappings, including broader override contributions, for
  reproducible lineage. Alternative assertions undergo the same status/value,
  decision-kind, attribute-reference and unit-category checks as their enclosing
  attribute. Their supports are retained both individually and in the combined
  conflict's support summary.
- Referenced definitions and their semantic dependencies must be source-effective
  on the observation date. This includes a measure's weight measure, concepts,
  units and supporting decisions. An inapplicable measure or dependency leaves
  its measure binding/attributes unresolved; independently applicable mapping
  concepts, attributes and explicit conversion can still contribute. Pinned
  references are never redirected to a newer definition implicitly. Historical
  supersession/override links remain closure requirements but are excluded from
  semantic effective-date dependency checks.
- `unit_factor` is an exact Decimal multiplier from the displayed value to
  unscaled money, fractional rates, integral counts or years. It is supplied
  only when both source unit and scale match the explicit conversion. Unknown
  or conflicting conversion yields `None`, independently of weighting status.
  Currency is separate: CBA's `$M` does not silently establish AUD. Task 6 owns
  the numeric multiplication, count typing, availability and Silver validation.
- The catalogue JSON decoder rejects unknown fields, missing required fields,
  unsupported versions, invalid statuses and non-string Decimal inputs.
  Omitted optional members use the declared immutable dataclass defaults.
  This differs deliberately from Bronze's fully explicit wire payload and
  does not change that payload's codec. Effective intervals are inclusive;
  the initial mappings are limited to the reviewed observation dates.

## Verification

`uv run pytest tests/catalogue -q` exercises real extracted samples and copied,
edited release files. Tests own semantic isolation, closure, conflict/override
behavior and strict decoding; source goldens continue to own extraction values
and metadata. `uv run pytest tests/bronze -q` verifies all four sources.
