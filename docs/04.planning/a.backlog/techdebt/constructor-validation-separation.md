# Revisit constructor validation responsibilities

**Type:** techdebt

**Status:** DEFERRED — researcher explicitly kept this outside the CR9 interface-design work, 2026-10-12.

**Owner:** rwa-analysis source/catalogue models and retained transport

## Finding

The existing source and catalogue classes still perform checks during construction.
For example, `Cr6Dataset.__post_init__` traverses source objects and resolves bindings
and references; catalogue constructors enforce attribute/reference conventions.
The migration retained these behaviours alongside the strict Bronze codec.

The [separate-validation principle](../../../01.principles/c.extraction-and-validation/validation-is-a-separate-process.md)
remains authoritative. Retained checks are not permission to introduce validation
stages, boundary validators or new constructor checks in CR9.

## Removal/refactoring objective

Review the retained responsibilities with the researcher and remove embedded
validation responsibilities from data declarations as agreed. Distinguish ordinary
parsing/type conversion from reference, consistency and semantic checking. Define
any separate validation process only through its own explicit design decision;
do not simply move current checks into an automatically invoked helper.

Preserve source evidence, saved-format compatibility and the supported processing
path. This item authorises no immediate code change, new refusal or validation mode.

## Related work

- [Current architecture](../../../architecture.md#validation-boundary).
- [Metadata ingress debt](metadata-ingress-and-nested-dataclasses.md), separately
  deferred while CR9 supplies the second domain for interface design.
