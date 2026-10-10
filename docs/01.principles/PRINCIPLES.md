# Maintaining principles

## Purpose

This collection captures the durable decisions agreed during project discovery. It follows Mountainash's category/index pattern at a scale appropriate to this repository. Detailed specifications explain contracts and workflows; source reviews explain evidence; this collection owns the principles that guide both.

## Status and scope

Each principle carries a status and scope:

| Status | Meaning |
|---|---|
| AGREED | Accepted design constraint; implementation is not implied |
| IMPLEMENTED | Supported by implementation, with links to its verification |
| PROPOSED | Awaiting a design decision |
| SUPERSEDED | Retained for context, with a link to its replacement |

These definitions are local to this repository; Mountainash's status vocabulary is not copied unchanged. All initial principles are AGREED because production extraction and conformance are not yet implemented.

Scope identifies the affected layers or concerns, such as `core`, `Bronze`, `Silver`, `Gold`, or `extraction`. Category letters order navigation, not conflict precedence.

## Document form

Each principle states:

1. Status and scope.
2. The principle in a few declarative sentences.
3. Its rationale.
4. Concrete implications and source-backed examples.
5. Links to detailed specifications or evidence.

Keep principles focused on enduring constraints. Dataclass field lists, implementation plans and transient spike outputs belong in their respective working materials.

## Ownership and change

- A principle document owns its decision, status and scope. Its category `INDEX.md` lists its summary and matching status.
- The root README routes to categories and supporting material without maintaining a second principle inventory.
- Update the principle and its category index together. Update detailed specifications in the same change when the decision changes their requirements.
- An agreed principle guides implementation. If source evidence or implementation findings conflict with it, surface the conflict and obtain a revised decision rather than silently changing its meaning.
- Preserve the rationale and replacement link when superseding a principle. Distinguish refinements from changed decisions.
- Mark a principle IMPLEMENTED only when supporting code and verification can be cited. An exploratory prototype is insufficient.
- Keep relative links valid and avoid multiple competing copies of a principle. Specifications link here for governing intent and retain their own detailed contracts.

## Relationship to the existing design

The initial collection distils decisions already agreed in the platform and data-model discussions. Existing specifications and discovery notes remain available at their current paths. Principles do not imply that every detail of a draft specification has been approved or implemented.
