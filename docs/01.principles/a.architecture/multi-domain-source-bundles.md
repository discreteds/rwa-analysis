# Multi-domain source bundles

> **Status:** AGREED
> **Scope:** core, extraction, Bronze

> **Clause supersession, accepted 2026-10-13:** The [metadata-driven journey](metadata-driven-extraction-and-conformance.md#clause-supersessions-and-retained-decisions)
> replaces the required complete bespoke extractor per PDF with metadata-defined
> capture and selected physical operations. The one-source-bundle boundary and
> contextual distinctions remain AGREED.

## Principle

One source PDF owns one logical Bronze bundle, whose selected capture is described by source bindings and can span multiple datasets. Bespoke physical operations are supplied where needed. Portfolio, domain, jurisdiction and observation period belong to the relevant occurrence and dataset context rather than being imposed by the source folder.

## Rationale

Australian mortgages are the initial research slice. The same reports disclose other credit portfolios, provisions, capital and additional domains across entities and jurisdictions. Duplicating the source bundle for each interpretation would fragment lineage and encourage double-counting.

## Implications

- The path jurisdiction describes the source disclosure's reporting jurisdiction; the path date describes the document reporting date.
- Record context distinguishes portfolio geography, entity domicile, regulatory-rule jurisdiction, consolidation scope and currency.
- A comparative panel retains its disclosed period; applicable measurement and other temporal roles resolve at the occurrence level. A multi-country aggregate remains one observation unless the source supplies a breakdown.
- Shared provenance and context support typed domain records. PD bands and regulatory approaches apply only to domains that require them.
- Additional selected tables extend the existing file's capture bindings, independent golden expectations and bundle, with physical operations extended where needed. Output revisions are versions of that bundle; preserve retained versions and their wire formats.
- Shared extraction components evolve from real source-backed requirements.

## Example

An ANZ APRA disclosure under `au/anz/` can contain Australian AIRB mortgages, separately disclosed NZ mortgages and March comparatives in one September document. A later request for provisions extends the same capture selection without copying the PDF or treating all its records as Australian September mortgages.

## References

- [Current implementation](../../architecture.md#source-contracts-and-normalised-silver):
  composed dataset protocol and CR6 container are implemented; the retained `cr6-v1`
  codec and pipeline currently support CR6 only. Other domains need their own selected
  source contracts and transport support.
- [Initial data model](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md), sections 2–6.
- [NAB/ANZ source review](../../00.ideation/2025-nab-anz-metadata-spike.md).
