# Target fields across disclosure generations — CBA mortgage deep dive

Date: 2026-11-20. Status: **research evidence and recommendation; no design or
migration approved.** Umbrella:
[semantic-layer structure backlog](../04.planning/a.backlog/research/semantic-layer-schema-and-library-options.md).
Governing requirement:
[format-independent target fields](../01.principles/b.data-semantics/format-independent-target-fields.md).

## Question and cases

Can CBA residential-mortgage EAD, average PD and the related RWA measures reach the
same target fields across three disclosure generations and two formats, and what
structure does that require?

| Generation | Source | Layout |
|---|---|---|
| 2013 APS 330, Basel III with 1.06 scaling | [June 2014 PDF](../../raw/cba-2014-06-30-aps330.pdf), Table 9d(ii) PDF pp.43–45 | Measures down rows, PD bands across columns |
| Same template, post-2023 framework | [June 2024 PDF](../../raw/cba-2024-06-30-aps330.pdf), Table 9d(ii) PDF pp.49–51 (captured, golden exists) | As 2014 |
| BCBS CR6 under revised APS 330 | [June 2025 PDF](../../raw/cba-2025-06-30-aps330.pdf) p.55 (captured, golden exists) and [APS 330 workbook](../../raw/cba-2025-06-30-aps330-quantitative.xlsx), sheet `CR6` | Bands down rows, measures across columns |

Reference model: EBA DPM 4.1 annotated table layout, `K_26.00.a` (EU CR6), from the
[framework 4.1 page](https://www.eba.europa.eu/risk-and-data-analysis/reporting-frameworks/reporting-framework-41).

## Findings

### 1. Same data, different format: converges exactly

Every one of the 108 golden positions for the 2025 PDF mortgage block (9 rows × 12
fields) matches the workbook's `CR6` rows 31–39 as a decimal value. Blank positions
are empty strings in the workbook; a different block uses a `–` string, so blank
versus dash survives. The workbook's number formats reproduce the golden displayed
precision for all populated positions (for example `#,##0.00` for average PD, so the
stored float `4` displays as `4.00`).

The workbook omits footnote markers, notes and definitions: overlay inclusion,
EAD-weighting of average PD and density rounding exist only in the PDF. Workbook
capture alone could therefore yield correct numbers with incomplete meaning.
A golden cross-format test is practical: both sources' mappings resolve to the same
target observations. Comparison performed with a throwaway script; not retained.

### 2. Same template name, different meaning across regimes

2014 and 2024 both publish "Table 9d(ii) – Retail exposures by portfolio type and PD
band" with identical band labels, but:

| Measure | June 2014 | June 2024 |
|---|---|---|
| Risk-weight row label | Exposure-weighted average risk weight (%) | Same label, footnote 3 |
| Scaling | Mortgage total 14.3% = 65,986 / 460,788 portfolio RWA (Table 6b–6f), which lists the 1.06 scaling factor as a separate line. **Inference:** excludes scaling | "Includes 1.10 scaling factor" |
| Overlay | No overlay note | LGD footnote: excludes the $7.4bn RWA overlay |
| Default-band risk weight | `-` | 200.6 |
| Average-EAD row label | "Exposure-weighted average EAD ($M)" | "Exposure - average EAD ($M)"; already mapped as unresolved |

Template identity and labels do not establish semantic continuity. The risk weights
need distinct target fields (or variants) for "excluding scaling" and "including
1.10 scaling, excluding overlay", related explicitly. The 2025 CR6 RWA density
"includes RWA overlays"; its scaling treatment is not stated in the captured
qualifications and remains unresolved.

### 3. Perimeter changes inside one table

2014 Table 6b–6f footnote 2: from June 2014 SME retail exposures secured by
residential mortgage move out of residential mortgage. In 9d(ii), the December 2013
panel's mortgage total 454,626 equals Table 7i's 446,695 plus SME retail mortgages
7,931; the June 2014 panel's 460,788 equals Table 7i alone. Adjacent panels with
the same row label therefore have different populations. Portfolio is a dimension
with a dated membership definition, not a label.

### 4. PD segmentations do not align across generations

| 9d(ii), 2014 and 2024 | 0 < 0.1% | 0.1% < 0.3% | 0.3% < 0.5% | 0.5% < 3% | 3% < 10% | 10% < 100% | Default |
|---|---|---|---|---|---|---|---|
| CR6, 2025 | 0.00–<0.15 | 0.15–<0.25 | 0.25–<0.50 | 0.50–<0.75 | 0.75–<2.50 | 2.50–<10.00 | 10.00–<100.00, 100 (Default) |

Only the default band and the portfolio total share population definitions. The
band is a segmentation dimension whose members carry explicit bounds. Band-level
values from different segmentations map to different dimension members; there is no
fabricated common band.

### 5. Field coverage differs legitimately

| Target | 2014 9d(ii) | 2024 9d(ii) | 2025 CR6 |
|---|---|---|---|
| EAD post-CCF post-CRM | "Total credit risk exposures": on-balance + undrawn "credit exposure value"; EAD equivalence **provisional** | Same label | Established |
| Average PD (EAD-weighted) | Absent | Absent | Established |
| Average LGD | Exposure-weighted | Exposure-weighted | Average LGD |
| Risk weight / RWA density | Excluding scaling (inference) | Including 1.10, excluding overlay | Including overlays |
| Number of borrowers | Absent | Absent | Present |

Average PD exists only in the CR6 generation for CBA. Earlier periods are partial
coverage, not mapping failures.

### 6. The current catalogue does not yet satisfy the principle

- **Bank- and template-specific measure identities.** `catalogue/measures/cr6-v1.json`
  defines `measure.cba.cr6.ead` and `measure.nab.cr6.ead` as separate measures with
  one-date effective ranges. Both reference concept `exposure.at-default@v1`, but the
  attribute values are spelled differently: `ead_post_crm_post_ccf` (CBA) and
  `ead_post_ccf_post_crm` (NAB). Equivalent data reaches different measures.
- **Historical EAD is unmapped semantically.** `catalogue/mappings/cba-historical-2024-v1.json`
  supplies unit conversions for Table 9d(ii). `historical-semantics-v1.json` maps LGD
  and the overlay only, and marks average EAD unresolved. "Total credit risk
  exposures" has no concept or measure mapping.
- **Free-text qualifiers.** `exposure_basis` is an open string attribute, so
  synonyms drift without detection.

The occurrence → mapping → definition shape already exists. What is missing is a
shared, bank-neutral target-field layer and controlled qualifier vocabularies.

### 7. What the EBA DPM contributes

The DPM defines each EU CR6 cell as a datapoint: a **main property** plus
**qualifier dimensions** with coded members. Examples from `K_26.00.a`:

- Column d: property `Exposure value` + `Type of adjustment` = "value after CRM
  substitution effects and conversion factors" + accounting item + calculation
  approach.
- Column e: property `Probability of default` + calculation method "EAD-weighted
  average of PDs".
- Rows: `PD Range` members with explicit intervals (for example `x403` ">=0.15% and
  <0.25%") and `Impairment status` (defaulted / non-defaulted). Exposure class is the
  sheet key.

This is the decomposition the principle asks for, and it puts post-CCF/post-CRM in a
coded member instead of a free string. Limits for us: the DPM has no member for
2014's "0.1% < 0.3%" band; it has no knowledge status, evidence or researcher
interpretation; and it covers EU templates from 2025 only. It is a reference
vocabulary, not a target model to adopt wholesale.

## Recommendation

Adopt the DPM's **property + coded qualifier dimensions** pattern for target fields
in our own catalogue, and keep our occurrence/evidence/interpretation model around it:

```text
target field  = measure property (exposure value, PD, LGD, RWA, risk weight, count)
              + controlled qualifiers (adjustment basis, weighting/calculation method,
                scaling/overlay treatment, accounting item)
observation   = target field + dimension members (entity/level, portfolio membership
                definition, approach, segmentation member with bounds, date/temporal role)
mapping       = source occurrence (PDF cell, workbook cell, legacy table position)
                → target field + members, with evidence and knowledge status
relationship  = explicit link between non-equivalent fields across regimes
                (for example risk weight excluding scaling → including 1.10 scaling)
```

Consequences, as concrete changes for a later design:

1. Replace per-bank `measure.<bank>.cr6.*` identities with shared target fields.
   Bank-specific evidence stays on the mapping. Example: CBA and NAB CR6 EAD both map
   to one "exposure value, post-CCF post-CRM" field.
2. Make qualifiers controlled vocabularies (SKOS-style concept schemes are a fit),
   which removes the `ead_post_crm_post_ccf` / `ead_post_ccf_post_crm` drift.
3. Model portfolio and PD segmentation as dated dimension definitions, so the
   December 2013 versus June 2014 perimeter and the 9d/CR6 band schemes stay distinct.
4. Add cross-format golden assertions where two sources cover the same period,
   starting with the CBA June 2025 PDF and workbook.
5. Record cross-regime field relationships with their evidence, starting with the
   9d(ii) risk weight (2014 versus 2024) and CBA scaling factors.

XBRL storage, Arelle and RDF tooling bring no current benefit: APRA does not publish
XBRL and there is no exchange consumer. LinkML could author the target-field and
vocabulary schema if the design is approved; that is a separate decision.

## Open questions for the researcher

1. Is 2014 "Total credit risk exposures" equivalent to EAD post-CCF/post-CRM, or a
   provisional/approximate correspondence? Footnote 1's "credit exposure value of
   undrawn commitments" suggests a post-conversion amount but does not establish it.
2. Should risk weight (9d) and RWA density (CR6) be one measure property with
   scaling/overlay qualifiers, or distinct properties?
3. Should the 2014 average-EAD row ("exposure-weighted") share the unresolved 2024
   average-EAD interpretation, given the label change?

## Limits

One bank, one portfolio. Workbooks for other banks and periods were not inspected.
EU CR9 (`K_29.00`) was located in the DPM table of contents but not reviewed. The
2014 scaling exclusion is an arithmetic inference from rounded totals.
