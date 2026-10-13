# Historical mortgage capture implementation lessons

Date: 2026-10-13. Evidence: historical source-table branch, final 173-test run and
retained example `/tmp/opencode/historical-mortgages-vnzcoqbr/`. Final review is
recorded in the [implementation plan](../04.planning/superpowers/plans/2026-10-12-historical-source-tables.md).

## Source-defined capture earns its place

The four 2024 disclosures contain 574 selected body positions and eight numerical
note observations in 23 dated datasets. A dataset is a selected panel, not necessarily
a separately numbered table. Three banks place measures down rows and PD bands across
columns; Westpac puts bands down rows. Fixed modern CR6/CR9 members would omit older
average EAD, portfolio backtesting and supplementary figures.

Original fields/cells are therefore the source inventory. Table bodies and numeric
notes remain distinguishable through `source_form`; a missing field is different from
a retained blank, dash or lexical `N/A`. The source frame does not turn narrative
figures into table positions. Original tokens and precision remain available after
publication, independently of unit-normalised values.

## Keep layout code local and semantics explicit

The bespoke extractors own PDF coordinates, repeated headings and transposed panels.
They share source dataclasses and primitive parsing, not a generic PDF-template engine.
Metadata composition, typed transport, normalised relations and persistence are shared.

- CBA's three exposure panels retain their LGD-row attachment for the RWA-overlay
  note and the one-year/long-run PD and downturn LGD definitions. A correctness review
  found missing definition passages despite all captured figures matching; source
  tests must assert meaning as well as numeric matrices.
- Westpac's 2023 backtesting continuation is on a different page. Its `(1%)` EAD
  variance remains negative percentage variance, not an estimated/actual ratio.
  Supplementary IRB and standardised RWA figures remain distinct from the body total.
- NAB's main and RBNZ mortgage populations remain separate rows with separate
  qualifications. Arrangement-based average EAD is evidence-backed; it does not imply
  that every bank's average EAD has the same denominator.
- ANZ's PD/EAD history, estimated LGD window and actual-LGD cutoff remain distinct
  temporal descriptors. No single observation date replaces their different roles.

Source review can leave uncertain population, weighting or temporal boundaries
unresolved. CBA's exposure-LGD definition is reused across its three panels while
mapping evidence remains panel-specific; unknown average-EAD counting basis stays
queryable. The catalogue does not declare cross-bank equivalence from similar labels.

## Legacy projection is a separate view

The explicit Westpac 2025 projection contributes 180 cells, including 16 lexical
rating positions. It calls the original CR6/CR9 resolvers on their original addresses
before assigning source-cell IDs. This preserves date-aware CR6 selection and CR9's
absence of a fabricated common date.

Legacy rating columns and numeric columns used separate ordinal ranges. The adapter
must recover their source order without losing paths or evidence. Within-row new-
default subsets need cell endpoints; row self-edges lose the distinction. Row roles
and aggregation scopes also survive the projection. Existing numeric frame keys
retain their old output; the explicit source-table function supplies lexical views.

## Native declarations must reach ingress

The complete comparison exposed Mountainash item 302: flat nullable scalar columns
whose first non-null appeared after row 100 failed before conformance. It affected
both lexical `N/A` and later missingness text. A passing smaller CBA path had not
exercised that shape.

The upstream repair in PR #377 preserves model-declared source types during native
construction; conversion targets remain separate. After pinning `c98f35ac`, the full
suite and actual four-bank example pass without reordered rows, sampling changes or
a local ingestion workaround. This confirms why the complete real path, rather than
more synthetic refinement, is the useful checkpoint.

## Persisted proof and limits

Master tests change stored values and metadata, delete staging databases and verify
readback, then replace the input selection and verify removed child rows disappear.
The example exports field, ordered-path, timing and band inventories from persisted
relations. Field presence does not depend on numeric non-nullness or a canonical mapping.

This is evidence for the selected 2024 reports and explicit Westpac 2025 comparison,
not fifteen-year coverage, automatic semantic matching or historical snapshot storage.
Mutable publication paths and retained-manifest limits remain as documented in the
[architecture](../architecture.md#current-publication-and-provenance-limits).
