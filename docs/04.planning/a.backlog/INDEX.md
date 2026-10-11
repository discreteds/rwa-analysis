# Project backlog

Items own their scope and status. Subtypes group work by purpose.

## Techdebt

Temporary implementation choices with an explicit removal objective live under
`techdebt/`. Recording debt does not make it a permanent architecture requirement.

| Item | Status | Removal objective |
|---|---|---|
| [Metadata ingress and nested dataclass schemas](techdebt/metadata-ingress-and-nested-dataclasses.md) | OPEN | Revisit the metadata schemas and remove the temporary recursive `asdict()` ingress adaptation. |
