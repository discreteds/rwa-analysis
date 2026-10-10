# Correction-safe identity

> **Status:** AGREED
> **Scope:** lineage, Silver, Gold

## Principle

Observation identity and lineage survive corrections and full rebuilds. Mutable canonical interpretations are not the sole identity/upsert key, and database-generated surrogate IDs are not durable cross-rebuild references.

## Rationale

Correcting a classification must not leave both the old and new interpretation active. Some corrections split, merge or remove records, so individual row upserts are insufficient for every change.

## Implications

- Preserve stable source identities and deterministic logical observation identities. Detailed key design is established with working datasets rather than assumed from a column label.
- Extraction errors produce corrected source-backed expectations and a new Bronze output version.
- Metadata errors produce new interpretation revisions and reconformance of retained Bronze.
- Bank restatements introduce new published evidence with explicit supersession relationships.
- Source-effective dates and interpretation revision history are distinct. Correcting an old mapping today does not imply that the bank changed its definition today.
- Repeated comparative disclosures can support the same observation. Selection of authoritative evidence is explicit so repeated publication does not double-count exposure.
- When record grain changes, replace the affected dataset scope, remove superseded active results and preserve source lineage.
- Publish dataset revisions atomically and retain the durable inputs needed to reproduce earlier interpretations. Downstream results identify their consumed revision.

## Example

Changing an observation's canonical portfolio classification must update or replace its interpretation rather than insert a second active exposure simply because a classification-based key changed. If new evidence splits one aggregate into two supported records, the previous aggregate cannot remain active in the same additive population.

## References

- [Initial data model](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md), sections 11.2–11.3.
- [Rebuildable analytical layers](../a.architecture/rebuildable-analytical-layers.md).
