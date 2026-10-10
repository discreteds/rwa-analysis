# Rebuildable analytical layers

> **Status:** AGREED
> **Scope:** Bronze, Silver, Gold, storage

## Principle

Full Silver regeneration from empty target tables is a normal, primary workflow. Silver is disposable; retained evidence, interpretation rules and the inputs needed to reproduce it are durable. Incremental processing produces the same logical result as a full rebuild.

## Rationale

Definitions, assumptions and classifications will be corrected repeatedly throughout the repository's lifetime. Existing Silver rows cannot be the only record of those corrections or a prerequisite for reconstructing the database.

## Implications

- Rebuild inputs explicitly select saved Bronze output versions, canonical definitions, mappings, curated corrections, conformance code/contracts and configuration.
- Preserve those inputs outside the disposable Silver layer. Golden sets verify extraction; they do not replace Bronze as the conformance input.
- Record selected input and implementation versions in a durable run manifest. Avoid relying on an unspecified mutable “latest”.
- Use Mountainash for tabular conformance, validation, analytics and storage integration, with local persistent DuckDB through `mountainash-data`. The independent capital-calculation library uses NumPy/SciPy.
- Validate a fresh candidate revision before publishing through an atomic transactional or staging mechanism supported by the backend. Failure leaves the previous published revision available.
- Gold outputs identify their Silver revision and become stale when a replacement revision is published.
- Historical Silver snapshots are optional conveniences; reproducibility depends on retained inputs and the corresponding implementation/configuration.
- Design full regeneration before optimising incremental upserts. Idempotency and equivalent logical results govern both paths.

## Example

If a glossary establishes that a previously assumed borrower count measures agreements, revise the durable mapping and rebuild Silver. A direct patch to a Silver row alone would be lost on the next rebuild and is therefore not a complete correction.

## References

- [Initial data model — Silver lifecycle](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md#11-silver-conformance-and-rebuild-lifecycle).
- [Platform design](../../04.planning/superpowers/specs/2026-10-10-rwa-analysis-design.md).
- [Correction-safe identity](../b.data-semantics/correction-safe-identity.md).
