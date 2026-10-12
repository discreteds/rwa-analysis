# Catalogue and compare disclosure tables across banks

**Type:** research

**Status:** IN PROGRESS — initial all-domain table-family location matrix and source-backed
comparisons recorded; detailed per-panel semantic inventory and researcher review remain open.

**Research output:** [Four-bank table catalogue and comparison](../../../00.ideation/2026-10-11-cross-bank-table-catalogue.md).

**Owner:** rwa-analysis disclosure discovery / semantic catalogue

**Requested:** 2026-10-11. Catalogue all tables across the four banks' selected
Pillar 3 reports and compare their coverage, meaning and analytical usefulness.

## Scope

Start with the retained CBA June 2025 and Westpac, NAB and ANZ September 2025 reports
listed in [raw/index.md](../../../../raw/index.md). Cover every disclosure table,
including bank-specific tables, appendices, regulatory template modifications and
non-mortgage domains. Include qualitative templates and surrounding definitions
where they establish the meaning or applicability of quantitative tables.

Inventorying a table does not commit us to extracting it. Investor presentations,
annual reports and APRA statistical releases can be linked as supporting sources;
their full inventories and further banks/periods follow demonstrated research needs.

## Deliverables

1. **Per-document table inventory.** Record source document and PDF/printed pages,
   template identifier where present, original title, continued pages, table purpose,
   measures and units, row/column dimensions and grain, populations, geography,
   regulatory basis, reporting entity, observation dates/windows and comparatives.
   Link material footnotes, glossary definitions and disclosure modifications.
   Distinguish tables actually present from index references, omissions, stated
   non-applicability and items not yet located.
2. **Cross-bank comparison matrix.** Align equivalent purposes and concepts, retaining
   bank-specific labels and variants. Compare available measures, segmentation,
   hierarchy/subsets, missingness, weighting/counting conventions, denominators,
   timing, scope and precision. Matching template IDs are evidence of intended
   comparability, not proof of identical semantics. Distinguish direct comparison,
   comparison with an explicit bridge/assumption, materially different measures and
   unresolved meaning, with the reason and source evidence.
3. **Analytical connections and extraction priorities.** Identify which tables can
   support each other, what would be needed for a join, and which current research
   question warrants extraction. Record candidate connections without imposing
   accounting identities or building a universal reconciliation framework.

Use compact research tables/notes in the existing discovery area first. Reuse existing
source reviews and catalogue definitions; do not create a new registry application
or duplicate the existing semantic catalogue. Promote reusable interpretations only
after source review and researcher agreement.

## Initial comparison questions

- CR6 versus CR9: assigned PDs, exposure/count populations, cohort anchors, outcome
  windows and historical-rate definitions. Preserve the distinction between observed
  default events, defaulted stocks, arrears and model estimates.
- CR1/CR2 versus CR6/CR9: credit quality and default/non-performing stocks and flows;
  inspect entry, cure, exit, write-off and exposure-basis differences before relating them.
- CMS1/CMS2, OV1 and CR6: modelled versus standardised capital, reported overlays,
  floors and portfolio coverage. Equality of totals alone does not establish scope.
- Other credit-risk, leverage, liquidity and capital tables: identify measures and
  segmentation available across banks, even where current calculations do not use them.
- Bank-specific mortgage composition and model commentary: locate useful evidence
  and connect to the [mortgage distribution evidence backlog](mortgage-distribution-evidence.md)
  rather than duplicating its acquisition/extraction work.

## Join and interpretation requirements

Record source-backed entity/portfolio relationships, dates, grain, measure definitions
and revisions that make a proposed comparison meaningful. Explicitly identify scope,
time and denominator bridges, and whether each is observed, derived or assumed.
Preserve multiple interpretations when evidence is incomplete. Do not broadcast a
portfolio attribute into band-level observations or double-count totals and subsets.

This catalogue should reveal missing evidence and possible constraints on analysis,
including assumed PD/product distributions. It does not turn exploratory comparisons
into processing validators or make every discovered table a mandatory core entity.

## Work and completion evidence

- [ ] Inspect each report's contents, disclosure index and actual table pages;
  catalogue all tables and track continued pages, comparatives and modifications.
- [ ] Build the four-bank comparison matrix with source references and explicit
  gaps/differences, retaining all domains rather than only CR6/CR9.
- [ ] Review uncertain equivalences and material assumptions with the researcher;
  preserve agreed interpretations separately from source statements.
- [ ] Identify source-backed join opportunities and prioritise extraction against
  current research questions. Link existing backlog owners before creating new work.
- [x] Demonstrate the usefulness of the catalogue with a CR6–CR9 comparison and a
  second cross-table connection, recording what can and cannot be inferred.

Completion means the inventory, comparison matrix and prioritised findings are
available with traceable evidence. It does not require implementing all extractors.

## Governing principles

- [Evidence and interpretation](../../../01.principles/a.architecture/evidence-and-interpretation.md).
- [Layered, evidence-backed definitions](../../../01.principles/b.data-semantics/layered-metric-definitions.md).
- [Emergent analysis and selective persistence](../../../01.principles/a.architecture/emergent-analysis-and-selective-persistence.md).
