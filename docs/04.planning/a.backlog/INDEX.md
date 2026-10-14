# Project backlog

Items own their scope and status. Subtypes group work by purpose.

## Research

Evidence acquisition and research questions with a defined analytical use live under
`research/`. Items distinguish located sources, reviewed evidence and implemented use.

| Item | Status | Objective |
|---|---|---|
| [Mortgage distribution evidence and calculation inputs](research/mortgage-distribution-evidence.md) | OPEN | Gather composition, market-share and actual default-outcome evidence; join scoped observations and explicit assumptions into distribution-constraining calculations. |
| [Cross-bank disclosure table catalogue](research/cross-bank-disclosure-table-catalogue.md) | IN PROGRESS | Initial all-domain location matrix and CR6–CR9/CR8 comparisons available; deepen per-panel semantics and prioritise extraction. |

## Techdebt

Temporary implementation choices with an explicit removal objective live under
`techdebt/`. Recording debt does not make it a permanent architecture requirement.

| Item | Status | Removal objective |
|---|---|---|
| [Metadata ingress and nested dataclass schemas](techdebt/metadata-ingress-and-nested-dataclasses.md) | CLOSED | Removed the temporary recursive `asdict()` ingress adaptation; checkpoint B accepted 2026-10-14. |
| [Constructor validation separation](techdebt/constructor-validation-separation.md) | DEFERRED | Revisit retained constructor/transport checking responsibilities under the separate-validation principle; outside CR9 interface design. |
| [Interactive research examples](techdebt/interactive-research-examples.md) | OPEN | Restore convenient interactive execution and exposed research objects without introducing a runner framework. |

## Implementation learning

[CR9 implementation lessons](../../00.ideation/2026-10-12-cr9-implementation-lessons.md)
retain observed fixes, design evidence and investigation candidates. Candidates are
not new requirements or confirmed upstream defects.
