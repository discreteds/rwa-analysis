# Composed processing and organisation staging

> **Status:** AGREED
> **Scope:** core, Bronze, Silver, configuration, orchestration

> **Clause supersession, accepted 2026-10-13:** The [metadata-driven journey](metadata-driven-extraction-and-conformance.md#clause-supersessions-and-retained-decisions)
> replaces domain-container/pipeline ownership as the governing capture boundary and
> makes technical declarations consumers of authoritative definitions. Staging,
> storage separation and independently callable stages remain AGREED.

## Principle

Metadata-defined capture and contextual conformance govern the Bronze-to-Silver
pathway, using Mountainash schema declarations, conformance and relation operations.
Compose reusable definitions with independently identified source occurrences under
[contextual source occurrences](contextual-source-occurrences.md). Domain records
are useful projections; their fixed inventories do not limit capture. Technical
declarations consume authoritative definitions and bindings rather than maintaining
parallel semantic inventories. Existing typed containers and source-table capture
remain supported; this ownership decision does not implement their replacement.

Configuration supplies execution settings; declarations describe models, schemas
and technical storage associations using those definitions; operations perform
extraction, transformation and storage;
an organisation-scoped session owns workflow sequencing. A small construction function
assembles the concrete operations using resolved settings and declarations.

Each session stage is independently callable for targeted reruns; `run()` is the thin
workflow entrypoint invoking those same stages in sequence. This agreed name supersedes
the provisional `all()`. Project defaults and organisation overrides use Mountainash
Settings' native layering.

Each organisation has an independently rebuildable staging Silver database. All
staging databases implement the same Silver schema and feed a full master Silver
rebuild, published atomically. [Validation is a separate process](../c.extraction-and-validation/validation-is-a-separate-process.md)
whose requirements and behaviour have not yet been defined.

## Rationale and implications

- CR6, CR1 and CR2 share evidence structures but differ in record grain, related
  collections and temporal meaning. A shared protocol does not require identical
  domain containers or one universal record shape.
- Dataclass collections can enter Mountainash relations and return as dataclasses
  or dataframes. Reuse those facilities rather than implement a local dataframe ORM.
- Composed source objects do not dictate nested database columns. Persist flat domain
  rows, store shared context once, and use related rows for repeated metadata. Flatten
  small owned objects where appropriate; table count follows the actual relationships.
- Input/output declarations describe the data and its conformance. Do not attach
  validation calls to these transitions. Trust framework arithmetic and casts.
- Technical declarations are explicit alongside their models and consume the same
  authoritative definitions and bindings, rather than inferring financial meaning
  from field names. Named domain results preserve related collections; their declared
  storage associations supply a shared write/read table inventory.
- The session delegates to operations. Storage owns serialization, paths, manifests,
  connections and transactions; domain conformance/reconstruction consumes explicit
  inputs without opening files or database connections. Keep construction separate
  from execution using ordinary functions and concrete components.
- Organisation ownership scopes source processing and staging, not exposure geography,
  legal reporting entity or observation date.
- Independent staging allows local teardown/rebuild without affecting other organisations.
  Master consolidation combines published outputs under the common schema.
- Full replacement handles removed inputs; incremental master updates are deferred.
- Settings configure execution. The semantic catalogue continues to own financial
  definitions, mappings, decisions and evidence.
- Plain Python use remains the interface. Git is not required to execute the workflow.

## References

- [Current implementation](../../architecture.md): four-bank CR6 uses these boundaries,
  a named 12-relation output and staging/master replacement. Broader domain dispatch
  remains an extension design, not an implemented plugin facility.
- [Mountainash-first coding](../d.coding-practices/mountainash-first.md).
- [Strategic architecture design](../../04.planning/superpowers/specs/2026-10-11-strategic-architecture-design.md).
- [Rebuildable analytical layers](rebuildable-analytical-layers.md).
- [Multi-domain source bundles](multi-domain-source-bundles.md).
- [Capture and tag for research](capture-and-tag-for-research.md).
