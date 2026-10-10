# Layered model feasibility spike

Date: 2026-10-10

Status: Completed throwaway experiment. No production extractor, Bronze output, approved golden fixture or Silver implementation is established by this exercise.

Design exercised: [Bronze/catalogue/Silver contracts and E–R diagrams](../04.planning/superpowers/specs/2026-10-10-layered-data-model.md). Source review: [CBA/Westpac discovery](2025-disclosure-spike.md).

## Outcome

The proposed layer split supports both complete mortgage CR6 samples through Mountainash relations, contract validation and local DuckDB persistence. Decimal values, partial interpretations, missingness, aggregate membership and field lineage survive a closed/reopened database and a fresh rebuild. Multi-table replacement through `mountainash-data` rolls back after an injected publication failure.

**Recommendation:** proceed to implementation planning for the first CR6 slice, with an explicit Decimal-preserving conformance policy. Default Mountainash numeric conformance is not suitable for this path as currently configured; the working explicit configuration is described below.

## Inputs and physical projection

Reused the earlier manually transcribed, source-reviewed samples: CBA June 2025 PDF p. 55 and Westpac September 2025 PDF p. 48, with applicable captured notes. They remain exploratory data, not independently approved golden expectations. Their reporting dates differ.

Saved inputs in the temporary spike directory:

- Source-form JSON with all twelve fields per row, original strings, precision, missingness, source references, bands, source definitions and qualifications.
- A separate partial mapping selection with target field, exact unit factor, interpretation tags, qualification references and mapping revision references.
- A manifest per build selecting the saved source bundle, mapping selection, implementation filename, package versions and any synthetic scope selection.

The sample was augmented with explicit links from each reported portfolio aggregate to its eight displayed bands, supported by the captured aggregate scope and source reference. These are source aggregate-membership relationships, not canonical concept relationships. The probe does not establish a generic parser for `of which` relationships or exercise column/footnote subsets in other domains. Exhaustiveness and mutual exclusivity are left unset on these links.

The DuckDB projection has seven tables:

| Table | Rows | Role |
|---|---:|---|
| `contexts` | 2 | Separate bank/date/source scope |
| `segments` | 16 | Fourteen numerical intervals and two default categories |
| `observations` | 18 | Wide typed CR6 records, including two aggregates |
| `interpretations` | 216 | Per-field availability, unit and interpretation tags |
| `applied_mappings` | 216 | Applied mapping revision references |
| `lineage` | 216 | Selected source occurrences, captured cell evidence and conversions |
| `relationships` | 16 | Portfolio-aggregate-to-band links |

Each table carries its Silver revision. Aggregates have no individual segment reference; defaults have no invented interval bounds. Monetary/rate/duration columns use `DECIMAL(38,8)` for this sample; counts use 64-bit integers. This scale is a probe choice, not a universal production precision policy. Historical result: the researcher subsequently selected `Decimal(22,8)` for production CR6, with 10-trillion-scale exact roundtrip tests; the original probe and its precision sentinel below remain recorded as executed.

Mappings intentionally retain null complete-measure references. They establish useful partial tags without pretending to implement the full semantic catalogue. Currency codes and counted-entity conventions remain unresolved; CBA PD has the captured period-end EAD-weighting qualification, while LGD weighting remains unresolved. Source definitions and qualification text remain saved outside Silver.

## Checks and results

All checks below passed against the actual local packages and persistent databases:

1. **Exact transport:** all seven table contents round-tripped through Arrow → `IbisBackend.create_table` → DuckDB → Arrow, after connection close/reopen, with matching physical schemas. Financial fields remained Decimal.
2. **Source-backed anchors:** CBA first-band EAD became `281508000000`, PD `0.0008`, and count `742470`; CBA aggregate RWA became `149143000000`; Westpac aggregate EAD became `569920000000`.
3. **Availability and semantics:** all 35 missing cells remained represented (34 blanks and the Westpac default-row CCF dash); missingness explanations and original strings remained in metadata/lineage. Westpac's disclosed 101% CCF became `1.01`. Unknown weighting/currency did not remove numeric observations.
4. **Structure:** revision-qualified context, segment and observation references resolved; every represented field had interpretation, mapping and lineage records. Mountainash rejected a deliberately duplicated observation key with `IdentityInvalidError`.
5. **Fresh rebuild:** a second database built from the saved source bundle and mapping selection matched the first logically, excluding the new Silver revision label.
6. **Mapping revision:** a clearly synthetic review annotation changed CBA LGD interpretation metadata and its mapping reference while preserving observation identities and financial values. This was not a new source interpretation.
7. **Failed publication:** injected an exception after replacing six of the seven tables inside `IbisBackend.transaction()`. Reopening the database recovered every original table and original revision label; no mixture of candidate and prior tables survived.
8. **Successful publication:** the same candidate then published completely.
9. **Scope removal:** a synthetic selection omitting one Westpac band replaced a prior full database with 17 observations, 204 field-lineage records and 15 relationships. The omitted observation and its links were absent. This only exercises removal mechanics; it does not claim a revised disclosed total or exhaustive remaining breakdown.

This establishes the exercised local transaction path. Concurrent-reader behavior, process termination during publication, split/merge identity, comparative-source deduplication, incremental upserts and the `not_conformed` value state remain unexercised. Referential checks in the probe are Python checks over the generated tables, not database foreign-key constraints. The full catalogue/release graph and a publication registry were not implemented.

## Mountainash integration findings

### Default missing-value transformation fails on Decimal

On the installed versions, default `ma.relation(frame).conform(ma.typespec({'amount': 'number'}))` applies the default empty-string sentinel to a Decimal column. Polars raises:

```text
InvalidOperationError: 'is_in' cannot check for Decimal(38, 8) values in List(String) data
```

The same default conformance behavior is reached through contract validation. Disabling coercion alone does not remove that sentinel rule.

### Generic number coercion changes representation

With the sentinel rule removed, automatic `number` conformance yields `Float64`. A separate synthetic precision sentinel (`12345678901234567890.12345678`) demonstrably loses precision. This sentinel is not a source observation.

The working path for already-typed source data is:

```python
spec = ma.TypeSpec.from_frictionless({
    'fields': [{'name': 'amount', 'type': 'number'}],
    'missingValues': [],
})
result = ma.relation(frame).conform(
    spec, apply_value_transforms=False,
).collect()
Contract = ma.datacontract(spec)
Contract.Config = type('Config', (), {'coerce': False})
validation = Contract.validate_datacontract(result)
assert validation.passes
```

Unit conversion is performed separately using Mountainash relation expressions with Decimal factors (`0.01` or `1000000`), before structural conformance and validation. Explicit Polars schemas establish the numeric representation, including all-null maturity columns. The probe verifies physical dtypes in addition to the universal `number` contract.

`ma.typespec({...}, missing_values=[])` did **not** apply the supplied missing-value metadata: the convenience factory retained `['']`. Constructing the TypeSpec through `from_frictionless` honored `missingValues: []`. Also, the actual contract method is `validate_datacontract`, returning a result whose `passes` must be checked; the inspected website example's `.validate()` method was unavailable.

These findings should inform the integration plan and any upstream follow-up. No dependency files were modified.

## Reproduction and artifacts

Throwaway directory: `/tmp/opencode/rwa-layered-spike/`.

```bash
/tmp/opencode/rwa-layered-spike/.venv/bin/python /tmp/opencode/rwa-layered-spike/spike.py
/tmp/opencode/rwa-layered-spike/.venv/bin/python /tmp/opencode/rwa-layered-spike/integration_probe.py
```

`results.json` records the lifecycle results and populated examples. `integration-results.json` records the conformance reproductions. `silver.duckdb` ends at the successful mapping revision (`r3`); `fresh.duckdb` contains the independent rebuild (`r2`); `removal.duckdb` contains the reduced scope (`r4`). Source JSON, catalogue selections and manifests are outside those databases. Temporary artifacts are machine-local and may be removed; this repository note is the durable finding, not a claim of long-term reproducibility of the scratch directory.

Environment: Python 3.12; Mountainash `0.1.0`, mountainash-data `0.1.0`, Polars `2.0.0`, DuckDB `1.5.6`, Ibis `12.0.0`. Packages were installed from local Mountainash repositories into an isolated virtual environment. Repository HEADs observed during the run: Mountainash `9f43cf818223c02793a6e5f516edaf2924f5339f`; mountainash-data `36f4f4a68bc17de51bfc22bbfbd9dd9191db2701`. HEAD identifiers alone do not certify working-tree contents.

## Implications for the first implementation plan

- Keep distinct source-oriented and conformed records, wide typed numeric tables, and field-level interpretation/lineage.
- Make Decimal precision, missing-value handling and coercion explicit at Mountainash boundaries; retain a precision-sensitive integration check.
- Begin with independently authored full CR6 golden sets and bespoke extractors. The sample adapter does not replace that work.
- Establish exact catalogue storage, manifest/version selection and publication semantics using the successful transaction path as evidence.
- Exercise richer subset endpoints, unsupported conversions and correction-induced changes in grain when those selected scopes become concrete.
