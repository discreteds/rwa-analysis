# Metadata ingress and nested dataclass schemas

**Type:** techdebt

**Status:** OPEN

**Scheduling:** Deferred during CR9 interface design by researcher decision,
2026-10-12. The removal objective remains; CR9 is not an ingress-refactoring project.

**Owner:** rwa-analysis metadata schemas / CR6 domain projection

**Decision:** Researcher explicitly authorised the temporary adaptation while
requiring its removal after revisiting metadata's need for nested dataclasses.

## Temporary implementation

The normalised Silver tables use scalar row models. Existing source metadata and
catalogue assertions still contain nested dataclasses. At the metadata ingress
boundary, standard-library `dataclasses.asdict()` exposes those objects as records;
Mountainash expressions select, unnest, explode, rename and join those records into
normalised relations. This is not a permanent metadata interchange format.

The boundary uses full-record Polars schema inference rather than the installed
Mountainash Python ingress default of 100 rows. On the pinned dependency, a column
with 100 initial nulls followed by `AUD` fails before conformance, including with an
explicit TypeSpec. The temporary bridge does no tabular transformation or validation.
Keep this adaptation local to `src/rwa_analysis/domains/cr6/metadata.py`.

## Removal work

1. Revisit which metadata schemas actually need nested dataclasses. Distinguish
   convenient source containers from record collections used for tabular processing.
2. Prefer directly ingestible typed records/related collections where they represent
   the domain naturally. Preserve existing source evidence and catalogue semantics.
3. Remove recursive `asdict()` adaptation and the full-inference bridge once those
   records can enter the supported native Mountainash path reliably.
4. Demonstrate the four-bank metadata and saved-Bronze/DuckDB reconstruction paths,
   including nullable fields and ordered evidence/alternative collections.

Closure requires removal of the temporary boundary from production, not merely an
upstream upgrade or moving it into a general-purpose serializer. Do not turn this
item into a validation project or require a new storage framework.

## Related records

- [Approved normalised design](../../superpowers/specs/2026-10-11-strategic-architecture-design.md).
- [Migration plan](../../superpowers/plans/2026-10-11-strategic-architecture-migration.md).
- Mountainash capability investigation 291 remains separately owned at
  `/home/ubuntu/git/mountainash-io/mountainash-central/04.planning/mountainash/a.backlog/active/nested-dataclass-ingress-support.md`.
