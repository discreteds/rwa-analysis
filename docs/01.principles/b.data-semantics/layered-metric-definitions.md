# Layered, evidence-backed definitions

> **Status:** AGREED
> **Scope:** metadata, Bronze, Silver

## Principle

Metric metadata separates canonical concepts, measurement definitions, reporting definitions and presentation. Published labels map to canonical roles and semantic variants using scoped, versioned evidence. Hierarchical inheritance and overrides are explicit and traceable.

## Rationale

Organisations report similar concepts under different labels, while the same label can hide different counting, weighting or adjustment conventions. Those conventions can evolve independently of the label.

## Implications

- Canonical concepts describe what is measured. Measurement definitions describe population, weighting, denominator, counting unit and adjustment treatment.
- Canonical concepts and their semantic relationships are long-lived, slowly changing, first-class research assets. They have durable identities independent of published labels, Python field names and disposable Silver tables. Retained revisions capture changes to definitions and relationships without silently rewriting the meaning used by earlier analyses.
- Build the hierarchy organically through source discovery and researcher interviews. New terminology prompts comparison with existing concepts, not automatic creation of a new concept or variant. Establish a meaningful semantic or analytical distinction before introducing one.
- Maintain source statements separately from researcher interpretations. Record the agreed rationale and decision context, including the interview outcome, alongside applicable source evidence. Agents revisit uncertain mappings with the researcher and preserve the resulting knowledge for future maintenance.
- Renaming a concept or adding a source alias need not change its identity. A genuine split, merge or replacement requires explicit relationships and revised mappings; preserve the prior interpretation for reproducibility. Definition and relationship revisions belong to durable rebuild inputs.
- Reporting definitions establish entity, portfolio, regulatory basis and effective period. Presentation preserves labels, units, scale, precision and missing-value conventions.
- Conformed financial fields use measure-specific fixed scales: base-unit monetary amounts use `Decimal(16,2)`, rates and other small-valued measures needing eight fractional digits use `Decimal(16,8)`, and actual counts use integers. The researcher agreed this on 2026-10-11: trillion-dollar amounts do not require eight fractional places. Scale belongs to the field contract, not a per-value magnitude heuristic. Bronze retains the original value and displayed precision.
- Attributes such as geography and currency cut across concept hierarchies and remain reusable rather than generating duplicated branches.
- Mapping applicability includes organisation/entity, domain, table, portfolio, relevant rules and observation dates; document/template restrictions disambiguate comparatives and changed publication conventions.
- Footnotes, introductions, glossaries, methodology sections and appendices can establish variant attributes. Preserve the supporting text, location, scope and whether the interpretation is explicit or inferred from evidence.
- A table-specific qualification can refine a broader definition. Unsupported inheritance or conflicting evidence leaves the affected interpretation unresolved.
- Each conformed observation identifies the effective definition and mapping versions used. A matching canonical concept does not by itself imply analytical comparability.
- Segmentation definitions are similarly scoped. Band boundaries, inclusivity, defaults, omissions and row roles form part of the data contract.
- Shared row grain and context do not merge field semantics. Segmentation selects a population; each measure field describes it through its own definition. PD-band membership and average PD remain distinct even though both use percent units. Typed domain rows carry explicit field-to-definition bindings; source aggregate labels and canonical aggregate roles remain distinguishable.
- Resolve table semantics from both axes: a row can identify a measure, temporal role or population, while a column can identify a period, measure or population. Preserve multi-level header paths and applicable qualifications. Typed domain records express these bindings explicitly.
- Capture source `of which`, comprising, parent/child and total relationships across rows and columns, including relationships established in notes. Keep their source labels, endpoints, scope and evidence. These source aggregation relationships are distinct from the canonical concept hierarchy and are necessary to avoid double-counting a parent alongside its subsets.
- A disclosed subset relationship does not by itself establish exhaustive coverage or mutual exclusivity among children. Do not infer hierarchy solely from indentation, similar labels or row numbering when the source is ambiguous; retain the uncertainty. Aggregation selects an appropriate level or established disjoint components rather than summing every visible value.

## Examples

| Source evidence | Canonical interpretation |
|---|---|
| CBA mortgage `Sub-total`; Westpac `Total Residential Mortgages` | Portfolio aggregate over the disclosed mortgage PD bands, retaining different source presentation roles |
| NAB mortgage `Number of borrowers` and its CR6 introduction | Arrangement count (#); source counting term is agreement |
| CBA CR6 overlay footnote; NAB CR6 exclusion statement | RWA concept with different overlay-treatment variants |

A changed footnote can require a revised mapping even if the published column title stays the same.

Across reporting vintages, do not presume semantic continuity from organisation,
label or column position. Follow [complete capture across evolving disclosures](../a.architecture/historical-disclosure-capture.md): preserve absence and changed grain,
and leave gap filling and construction of comparable histories to downstream analysis.

Arrangements are counted entities (#); exposures are monetary amounts ($). An arrangement may carry an exposure amount, but these are distinct concepts. Earlier discussion used the ambiguous term `modelled exposure unit`; the researcher corrected that interpretation. Source borrower, counterparty, loan, agreement and arrangement terminology requires contextual mapping: NAB's mortgage agreement count maps to arrangement count, without asserting that every counterparty count in every portfolio counts arrangements. Preserve each source definition and investigate distinctness and aggregation where relevant.

Measures over arrangements can have multiple meaningful variants: account/arrangement-weighted or monetary-exposure-weighted aggregation, and population or treatment rules that include, exclude or conditionally include arrangements. Represent these as composable attributes of the measurement definition rather than creating a separate top-level concept for every combination. Keep the counted entity distinct from how a measure over those entities is weighted. An exposure-weighted measure must identify the applicable monetary exposure basis; account weighting must establish what counts as an account and its contribution.

A single table or row can contain arrangement counts (#), exposure totals ($) and rates (%) weighted by monetary exposure. Each measure field therefore has its own semantic definition, unit, aggregation and weighting references. Shared row context does not impose a common measure type or unit. A percentage weighted by EAD still has a percentage result unit; its weight measure has currency units. Weighting is distinct from a ratio denominator. Do not infer either from the presence of adjacent count or exposure columns. Counts and monetary totals may support additive aggregation over compatible disjoint populations; rates require their own defined aggregation rules rather than summation or unweighted averaging.

Inclusion rules identify the affected population or treatment and, when conditional, the predicate and its applicability. Conditional inclusion is an explicit rule, not a synonym for unknown inclusion. Record unresolved rules as unresolved. Resolve the semantic meaning of each attribute through evidence and researcher dialogue before mapping terminology to a canonical variant.

## Temporal and cohort semantics

Default state and default event are distinct reusable concepts. A stock default measure includes arrangements already in default at an observation point. The canonical forward 12-month default-outcome measure follows arrangements not in default at that anchor and identifies those entering default during the subsequent 12 months. This definition was established through researcher dialogue; a published measure maps to it only when its disclosed conventions support that interpretation.

Compose temporal measures from cohort eligibility at an anchor, qualifying event/transition rules and an observation window with explicit boundaries. Reusable definitions express relative timing; observation instances supply actual dates. Counts and rates remain distinct, with rates referencing denominator and weighting definitions. Cure, exit, repeated events and incomplete follow-up require explicit rules when relevant. Published CR9 measures do not automatically inherit the canonical forward-cohort definition.

Researcher clarification, 2026-10-12: temporal metadata must resolve for each datapoint,
not merely each table or record. Adjacent CR9 columns can describe PD measurement dates,
opening/closing populations, annual default events and historical averaging windows.
Shared temporal descriptors may be referenced by multiple fields; their physical
representation remains a design decision. Preserve the source's actual wording and
knowledge status when a duration is known but exact boundaries are not.

Keep publication vintage separate from the period measured, disclosed methodology
changes and our extraction/interpretation revisions. Retain successive published
occurrences so research can examine repeated or revised historical values. A changed
rolling-window average alone does not establish a restatement or reveal its annual
components. Capture and tag the evidence; period alignment, vintage selection,
aggregation and reconstruction of longer histories are bespoke analytical choices,
not implicit conformance or publication policies.

## References

- [Current CR6 contracts](../../../src/rwa_analysis/domains/cr6/contracts.py) and
  [conformance evidence](../../../tests/silver/test_cr6_conformance.py) implement the
  measure-specific numeric declarations for the selected slice. The complete semantic
  hierarchy and additional temporal domains are not implied implemented by that proof.
- [Initial data model — semantic catalogue](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md#7-durable-semantic-catalogue) and [contextual mappings](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md#8-contextual-mappings-and-effective-meaning).
- [NAB/ANZ source review](../../00.ideation/2025-nab-anz-metadata-spike.md).
