# Composed processing and organisation staging

> **Status:** AGREED
> **Scope:** core, Bronze, Silver, configuration, orchestration

## Principle

Separate domain dataset containers share a fundamental Python protocol and compose
shared source metadata. Domain pipelines connect Bronze input dataclasses and Silver
output dataclasses using Mountainash conformance, contracts, rules and relation
operations. Derive common schema declarations from the models and augment them where
necessary rather than maintaining parallel field inventories.

Configuration supplies execution settings; domain declarations own models, contracts,
rules and table identities; operations perform extraction, transformation and storage;
an organisation-scoped session owns workflow sequencing. A small construction function
assembles the concrete operations using resolved settings and declarations.

Each session stage is independently callable for targeted reruns; `run()` is the thin
workflow entrypoint invoking those same stages in sequence. This agreed name supersedes
the provisional `all()`. Project defaults and organisation overrides use Mountainash
Settings' native layering.

Each organisation has an independently rebuildable staging Silver database. All
staging databases implement the same Silver schema and feed a full master Silver
rebuild, validated and published atomically.

## Rationale and implications

- CR6, CR1 and CR2 share evidence structures but differ in record grain, related
  collections and temporal meaning. A shared protocol does not require identical
  domain containers or one universal record shape.
- Dataclass collections can enter Mountainash relations and return as dataclasses
  or dataframes. Reuse those facilities rather than implement a local dataframe ORM.
- Contracts belong at input/output transitions. Check parameters up front; trust
  framework arithmetic and avoid scattered checks or duplicate numeric ETL.
- Domain constraints are explicit alongside their models, rather than inferred by
  a shared helper from field names. Named domain results preserve related collections;
  their declared storage associations supply a shared write/read table inventory.
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

- [Strategic architecture design](../../04.planning/superpowers/specs/2026-10-11-strategic-architecture-design.md).
- [Rebuildable analytical layers](rebuildable-analytical-layers.md).
- [Multi-domain source bundles](multi-domain-source-bundles.md).
- [Capture and tag for research](capture-and-tag-for-research.md).
