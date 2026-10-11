# Project backlog

Items own their scope and status. Subtypes group work by purpose.

## Research

Evidence acquisition and research questions with a defined analytical use live under
`research/`. Items distinguish located sources, reviewed evidence and implemented use.

| Item | Status | Objective |
|---|---|---|
| [Mortgage distribution evidence and calculation inputs](research/mortgage-distribution-evidence.md) | OPEN | Gather composition, market-share and actual default-outcome evidence; join scoped observations and explicit assumptions into distribution-constraining calculations. |

## Techdebt

Temporary implementation choices with an explicit removal objective live under
`techdebt/`. Recording debt does not make it a permanent architecture requirement.

| Item | Status | Removal objective |
|---|---|---|
| [Metadata ingress and nested dataclass schemas](techdebt/metadata-ingress-and-nested-dataclasses.md) | OPEN | Revisit the metadata schemas and remove the temporary recursive `asdict()` ingress adaptation. |
