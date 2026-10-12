# Documentation guide

## Current guidance

- [Project README](../README.md): supported workflow, executable examples and commands.
- [Current architecture](architecture.md): implementation ownership, data flow,
  normalised storage, publication semantics and known limits.
- [Principles](01.principles/README.md): durable decisions and their status/maintenance rules.
- [Mountainash-first coding](01.principles/d.coding-practices/mountainash-first.md):
  library ownership, data boundaries and handling capability gaps.
- [Agent guidance](../AGENTS.md): starting points and repository working instructions.
- [Backlog](04.planning/a.backlog/INDEX.md): outstanding work and temporary adaptations.

## Evidence and design history

- [CR9 domain and temporal metadata design](04.planning/superpowers/specs/2026-10-12-cr9-domain-design.md):
  refined production specification and disposable spike shape approved.
  CR9 remains unimplemented in production.
  The [implementation plan](04.planning/superpowers/plans/2026-10-12-cr9-implementation.md)
  is approved and records the real Westpac mixed-domain checkpoint awaiting review.

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
