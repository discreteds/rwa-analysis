# Documentation guide

## Current guidance

- [Project README](../README.md): supported workflow, executable examples and commands.
- [Current architecture](architecture.md): implementation ownership, data flow,
  normalised storage, publication semantics and known limits.
- [Principles](01.principles/README.md): durable decisions and their status/maintenance rules.
- [Contextual source occurrences](01.principles/a.architecture/contextual-source-occurrences.md)
  and [metadata-driven extraction and conformance](01.principles/a.architecture/metadata-driven-extraction-and-conformance.md):
  AGREED on 2026-10-13; authoritative ownership and occurrence-model decisions with
  enacted clause supersessions. The [metadata-driven extraction design](04.planning/superpowers/specs/2026-10-13-metadata-driven-extraction-design.md)
  and disposable spike shape are approved. The [implementation plan](04.planning/superpowers/plans/2026-10-13-metadata-driven-extraction.md)
  was approved on 2026-10-13; Tasks 1–3 are implemented and verified on
  `feature/metadata-driven-extraction` for checkpoint A. ANZ 2023 is the first v4
   source. Checkpoint A was accepted on 2026-10-14; Tasks 4–6 now cover all twelve
   selected reports, with 200 tests passing and checkpoint B awaiting acceptance.
  Principle acceptance does not imply an implemented replacement
  pipeline; existing capture remains supported.
- [Mountainash-first coding](01.principles/d.coding-practices/mountainash-first.md):
  library ownership, data boundaries and handling capability gaps.
- [Agent guidance](../AGENTS.md): starting points and repository working instructions.
- [Backlog](04.planning/a.backlog/INDEX.md): outstanding work and temporary adaptations.

## Evidence and design history

- [Historical source-table design](04.planning/superpowers/specs/2026-10-12-historical-source-tables-design.md):
  researcher-approved capture/composition contracts and structural research queries;
  the four-bank 2024 delivery merged through PRs #13/#14. The
  [implementation plan](04.planning/superpowers/plans/2026-10-12-historical-source-tables.md)
  records the accepted checkpoint, four-bank persisted capture and passing full
  example after consuming Mountainash PR #377; final reviews are complete and
  checkpoint B was accepted. The [implementation lessons](00.ideation/2026-10-13-historical-implementation-lessons.md)
  record the source-format, metadata and native-ingress findings.
  The [2024 source inventory](00.ideation/2026-10-12-historical-source-inventory.md)
  records selected mortgage panels, measures, qualifications and unresolved meanings.

- [2023 capture continuation](00.ideation/2026-10-13-historical-2023-capture.md):
  approved four-bank extension, source-vintage distinctions and assessment of shared
  versus bespoke responsibilities; execution evidence records its delivery status.

- [CR9 implementation lessons](00.ideation/2026-10-12-cr9-implementation-lessons.md):
  observed fixes, reusable design evidence and concrete follow-up candidates.

- [CR9 domain and temporal metadata design](04.planning/superpowers/specs/2026-10-12-cr9-domain-design.md):
  refined production specification and disposable spike shape approved.
   Four-bank CR9 capture, conformance and persistence are implemented and merged through PR #9.
  The [implementation plan](04.planning/superpowers/plans/2026-10-12-cr9-implementation.md)
   records the approved Westpac checkpoint and final four-bank execution evidence.

- [Raw inventory](../raw/index.md) and [`extractions/`](../extractions/): official
  sources, per-document review and saved extraction code.
- [`00.ideation/`](00.ideation/): research briefs, discoveries and labelled spikes.
- [Strategic architecture specification](04.planning/superpowers/specs/2026-10-11-strategic-architecture-design.md)
  and [completed migration](04.planning/superpowers/plans/2026-10-11-strategic-architecture-migration.md):
  approved design and dated delivery evidence.
- [Initial logical model](04.planning/superpowers/specs/2026-10-10-initial-data-model.md),
  [E–R diagrams](04.planning/superpowers/specs/2026-10-10-layered-data-model.md) and
  [worked examples](04.planning/superpowers/specs/2026-10-10-data-model-worked-examples.md):
  semantic rationale and extension exercises, not a current physical-schema inventory.

Principles own decisions; code/declarations and verified examples establish current
implementation. Specs explain design; plans record execution history. An older
instruction does not regain authority because it remains in a historical plan.
Surface conflicts rather than treating code as permission to change an agreed principle.
