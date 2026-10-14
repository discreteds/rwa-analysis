# Principles and architecture

Durable decisions for the disclosure research platform, starting with Australian mortgage capital analysis and extending across domains and jurisdictions.

Read [PRINCIPLES.md](PRINCIPLES.md) for status definitions, ownership and maintenance. Principle documents own the decisions; category indexes provide navigation and status summaries.

## Categories

- [a. Architecture](a.architecture/INDEX.md): capture-and-tag research goals, contextual source occurrences, metadata-driven extraction/conformance, evidence boundaries, multi-domain bundles, rebuildable layers and selective persistence of emergent analysis.
- [Complete capture across evolving disclosures](a.architecture/historical-disclosure-capture.md): full selected-table capture over changing formats and meanings, with declared physical sourcing and separately owned semantics.
- [b. Data semantics](b.data-semantics/INDEX.md): layered metric definitions, contextual mappings and correction-safe identity.
- [c. Extraction and validation](c.extraction-and-validation/INDEX.md): document-led extraction, independently authored golden sets, and validation as a separate, not-yet-defined process.
- [d. Coding practices](d.coding-practices/INDEX.md): Mountainash-first implementation, explicit library boundaries and capability-gap handling.

## Supporting material

- [Contextual source occurrences](a.architecture/contextual-source-occurrences.md)
  and [metadata-driven journey](a.architecture/metadata-driven-extraction-and-conformance.md):
  accepted 2026-10-13, with enacted clause supersessions and continuing constraints
  recorded in the affected principles. AGREED establishes design authority, not an
  implemented replacement pipeline; existing capture remains supported.
- [Metadata-driven extraction design](../04.planning/superpowers/specs/2026-10-13-metadata-driven-extraction-design.md):
  design, disposable spike shape and implementation plan approved; Tasks 1–3 are
   accepted at checkpoint A. Tasks 4–6 cover all twelve selected reports and named
   domain projections, verified with 200 tests; checkpoint B acceptance is pending.

- [Current architecture](../architecture.md): implemented ownership, normalised CR6 tables, staging/master behaviour, provenance limits and verification evidence.
- [Strategic processing architecture](../04.planning/superpowers/specs/2026-10-11-strategic-architecture-design.md): approved design implemented for four-bank CR6, with a completed migration record; additional domains remain design examples.

- [Simpler CR6 research workflow](../04.planning/superpowers/specs/2026-10-10-simple-cr6-research-design.md): historical intermediate design, superseded in physical storage and ownership by the strategic architecture.

- [Original platform design](../04.planning/superpowers/specs/2026-10-10-rwa-analysis-design.md): research direction and historical proposals; use the current architecture for implemented workflows.
- [Initial data model](../04.planning/superpowers/specs/2026-10-10-initial-data-model.md): consolidated source capture, semantic catalogue and conformance contracts.
- [Layered schemas and E–R diagrams](../04.planning/superpowers/specs/2026-10-10-layered-data-model.md): explicit Bronze/catalogue/Silver relationships and conformed field contracts.
- [Worked model examples](../04.planning/superpowers/specs/2026-10-10-data-model-worked-examples.md): source-backed CR6, CR1/CR2 and LIQ2 design exercises.
- [CBA/Westpac discovery](../00.ideation/2025-disclosure-spike.md) and [NAB/ANZ discovery](../00.ideation/2025-nab-anz-metadata-spike.md): source evidence and examples.
- [Raw index](../../raw/index.md): saved disclosure catalogue.

Start with the architecture category when making structural decisions, then consult the relevant semantic and extraction principles. These principles apply to implementation planning as well as operational corrections.
