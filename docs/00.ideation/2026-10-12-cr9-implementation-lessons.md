# CR9 implementation lessons

Date: 2026-10-12

Status: **Living implementation observations, not additional approved requirements.**
The researcher approved the Westpac checkpoint and requested that lessons be retained
for later backlog, techdebt and architecture decisions. Extend this record with evidence
from the remaining banks rather than treating one-bank success as universal proof.

Evidence: [implementation plan and checkpoint](../04.planning/superpowers/plans/2026-10-12-cr9-implementation.md),
[approved design](../04.planning/superpowers/specs/2026-10-12-cr9-domain-design.md),
[checkpoint PR #9](https://github.com/discreteds/rwa-analysis/pull/9).

| Lesson | Concrete evidence | Disposition / revisit trigger |
|---|---|---|
| Time belongs to a field occurrence, not one table date | Westpac weighted PD/EAD uses June 2024; default events use July 2024–June 2025; history reports ten years without established endpoints | Implemented temporal descriptors/bindings. Carry forward under the existing field-level semantics principle; check the shape against other banks before expanding roles. |
| Partial meaning remains useful | Historical rate 0.06% is retained and conformed while history boundaries and aspects of its denominator remain unresolved | Established capture-and-tag decision. No additional eligibility flag or inference stage. Promote a new definition only after source review/researcher agreement. |
| Relationships must address fields within rows | Seven new-default counts are subsets of the corresponding total event counts; first band is 7 of 385. The default-stock row has blank event cells | Implemented field-addressable endpoints and source scope. Revisit only when an actual source relationship cannot be represented; do not add an aggregation engine. |
| Numerical equality does not establish metadata fidelity | Review found Bronze's row-level `default-definition` qualification missing from Silver field qualifications for default-stock counts | Fixed with a failing-then-passing regression. Future reviews should trace applicable row/column/temporal evidence through readback, not just compare numbers. No runtime validation process follows from this lesson. |
| Reconstruction has presentation semantics too | Initial CR9 output used typed field keys and put historical rates before counts | Fixed: retain published header labels and column order from source bindings. Keep typed names in domain relations and source labels at the reconstruction boundary. |
| The current shared seams are sufficient for two domains | Concrete pipelines, shared field-meaning composition and a declared table inventory support real mixed-domain publication/readback | Keep these boundaries; no new pipeline protocol or plugin registry justified. Removed an unused copy of temporal bindings from semantic `FieldOccurrence`. Revisit abstractions only for a demonstrated consumer. |
| Flat metadata can use native ingress without expanding the nested adapter | CR9's flat declarations entered Mountainash and persisted through DuckDB | Positive evidence for this path only. Existing nested-ingress techdebt remains open; do not claim that its upstream limitation has been solved. |
| Decimal working scales matter before arithmetic | Spike's initial small-rate multiplication rounded values; explicit casts on both operands restored exact source-unit readback | Reuse the existing CR6 conversion pattern; declare final measure scales separately. A consumer arithmetic issue, not evidence for new precision guards. |
| Legacy compatibility needs inputs independent of live extractors | Old-wire tests previously obtained CBA objects from an extractor that will emit the new format | Legacy fixture ownership corrected before migration. Keep wire compatibility assertions distinct from current extraction goldens; do not compare a serializer only with its own output. |
| Interactive examples are part of the usable research interface | `uv run python -i examples/westpac_cr9.py` exited for missing arguments; local variables inside `main()` were unavailable for inspection | Concrete [interactive-example debt](../04.planning/a.backlog/techdebt/interactive-research-examples.md). Existing command with explicit flags works, but is not the expected interactive experience. |
| Schema-inference log messages obscure the useful result | Pinned schema extraction logs unsupported Decimal/Literal hints before explicit augmentation supplies the actual types | Investigation candidate, not a confirmed upstream defect. Inspect pinned native schema APIs and existing upstream findings before proposing a change. Do not hide all logs or invent a second schema system. |

## Boundaries for follow-up

- A resolved defect stays recorded as evidence; it does not need an open backlog item.
- An implementation compromise with a concrete removal objective belongs in techdebt.
- A suspected library gap first needs reproduction and ownership analysis, then the
  existing Mountainash Central process. No GitHub issue is authorised by this record.
- A recurring source-backed requirement can refine a principle/spec after researcher
  agreement. A single difficult case is not permission to introduce a framework.
- Remaining-bank findings should name the source, affected interface and observed
  outcome. Historical reconstruction and authoritative-vintage selection remain
  bespoke analysis, regardless of how much history the capture accumulates.
