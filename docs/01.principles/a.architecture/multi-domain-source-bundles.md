# Multi-domain source bundles

> **Status:** AGREED
> **Scope:** core, extraction, Bronze

## Principle

One source PDF has a bespoke extractor and one logical Bronze bundle, which can contain multiple typed datasets. Portfolio, domain, jurisdiction and observation period belong to the relevant dataset context rather than being imposed by the source folder.

## Rationale

Australian mortgages are the initial research slice. The same reports disclose other credit portfolios, provisions, capital and additional domains across entities and jurisdictions. Duplicating the source bundle for each interpretation would fragment lineage and encourage double-counting.

## Implications

- The path jurisdiction describes the source disclosure's reporting jurisdiction; the path date describes the document reporting date.
- Record context distinguishes portfolio geography, entity domicile, regulatory-rule jurisdiction, consolidation scope and currency.
- A comparative table has its own observation date. A multi-country aggregate remains one observation unless the source supplies a breakdown.
- Shared provenance and context support typed domain records. PD bands and regulatory approaches apply only to domains that require them.
- Additional selected tables extend the existing file's golden set, extractor and bundle. Output revisions are versions of that bundle.
- Shared extraction components evolve from real source-backed requirements.

## Example

An ANZ APRA disclosure under `au/anz/` can contain Australian AIRB mortgages, separately disclosed NZ mortgages and March comparatives in one September document. A later request for provisions extends the same extraction without copying the PDF or treating all its records as Australian September mortgages.

## References

- [Initial data model](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md), sections 2–6.
- [NAB/ANZ source review](../../00.ideation/2025-nab-anz-metadata-spike.md).
