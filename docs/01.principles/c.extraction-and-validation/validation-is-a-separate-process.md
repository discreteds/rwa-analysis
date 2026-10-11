# Validation is a separate process

> **Status:** AGREED
> **Scope:** core, extraction, Bronze, Silver, Gold, orchestration
> **Decision:** Researcher clarification, 2026-10-11.

## Principle

Validation is a separate process. It is not embedded in extraction, conformance,
transformation, storage, publication, reconstruction or the organisation workflow.
The project's validation requirements and behaviour have not yet been defined.
Do not invent validation rules, calls or processing gates while implementing those
operations, including by automatically invoking Mountainash validators.

## Implications

- Models and schemas describe data. Conformance applies the declared conversions
  and mappings. Neither implies running a validation process.
- Validation's scope, rules, invocation, outputs and consequences require a separate
  researcher decision. This principle does not design that process or authorize its
  implementation, including an optional validation stage or mode.
- A schema declaration, preservation requirement or backend working type is not
  permission to add precision checks, consistency passes or publication gates.
- Ordinary failures of parsing, arithmetic, casts and I/O propagate from their
  owning operations. They do not justify a second layer of defensive checks.
- Independent goldens and development tests remain evidence for implementation
  correctness. They are not an implicit runtime validation stage or a source of
  additional runtime policy.

## Supersession

This decision supersedes earlier instructions to validate at processing boundaries,
validate candidates before publication, or embed source-backed validation rules in
conformance. Those instructions must not be restored from older specs, plans, tests
or implementations. The separation is agreed; validation itself remains undefined.

## References

- [Source-led extraction and golden sets](source-led-extraction-and-golden-sets.md).
- [Composed processing and organisation staging](../a.architecture/composed-processing-and-organisation-staging.md).
- [Rebuildable analytical layers](../a.architecture/rebuildable-analytical-layers.md).
