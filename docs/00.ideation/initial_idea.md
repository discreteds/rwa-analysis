# Project Brief: Bank Regulatory Capital & Risk Weight Analytics

**Working project name:** `bank-capital-analytics`  
**Language:** Python  
**Initial scope:** Australian banks, residential mortgages, 2016–2026  
**Long-term scope:** International banks, multiple credit portfolios, regulatory frameworks and reporting periods.

## 1. Project overview

Develop an open-source Python platform for collecting, standardising, storing and analysing historical and ongoing bank regulatory capital disclosures.

The platform will initially focus on Australian banks' APS 330 / Basel Pillar 3 disclosures, particularly residential mortgage portfolios subject to the Internal Ratings-Based (IRB) approach.

The core objective is to investigate **why banks operating in similar markets, with apparently similar credit risk, report materially different risk-weighted assets and regulatory capital requirements**.

The project will examine differences attributable to:

- Portfolio-average Probability of Default (PD).
- The distribution and dispersion of PD estimates across exposures.
- Differences in credit risk model calibration and discrimination.
- Regulatory methodology, including capital floors and scaling factors.
- Differences in portfolio composition.
- Changes in risk weights and capital adequacy through economic cycles.
- Potential financial incentives to optimise regulatory capital through internal modelling choices.

A central analytical contribution will be a **PD Differentiation Benefit** metric derived from the concavity of the Basel IRB capital function.

The system must distinguish between published observations, reconstructed estimates, standardised calculations and statistical inferences.

### Research hypothesis

The primary hypothesis is that variation in reported mortgage risk weights may partly reflect differences in banks' internal credit risk modelling philosophies.

Some institutions may adopt more conservative approaches to differentiating credit risk, while others may pursue more granular or aggressive differentiation because of the commercial benefits associated with lower regulatory capital consumption.

The purpose is to test this hypothesis empirically, **not to assume that lower risk weights indicate inappropriate modelling**.

---

# 2. Functional requirements

## 2.1. Regulatory disclosure database

Design a flexible, extensible relational schema capable of storing regulatory disclosures from different banks, jurisdictions, reporting periods and regulatory frameworks.

The schema must accommodate multiple levels of aggregation and different approaches to segmenting credit portfolios.

### Core dimensions

| Dimension | Examples |
|---|---|
| Institution | CBA, Westpac, NAB, ANZ, Macquarie, ING |
| Reporting entity | Banking group, subsidiary, regulated ADI |
| Jurisdiction | Australia, UK, EU, US, New Zealand |
| Regulator | APRA, PRA, ECB, Federal Reserve |
| Regulatory framework | Basel II, Basel III, jurisdiction-specific implementations |
| Reporting period | Quarter, half-year, financial year |
| Portfolio | Residential mortgages, credit cards, corporate, SME |
| Regulatory approach | IRB, Foundation IRB, Advanced IRB, Standardised |
| Portfolio segment | Owner-occupied, investment, interest-only |
| Risk segmentation | PD band, risk-weight band, LVR band, internal rating |
| Reporting scope | Consolidated group, domestic portfolio, subsidiary |

The architecture must support hierarchical portfolio structures and overlapping classification dimensions.

For example:

```text
Bank
 └── Reporting Entity
      └── Credit Risk
           └── Retail
                └── Residential Mortgages
                     ├── Owner Occupied
                     │    ├── Principal & Interest
                     │    └── Interest Only
                     └── Investment
                          ├── Principal & Interest
                          └── Interest Only
```

Each segment might be further subdivided by PD bands, LVR bands, delinquency status or other attributes.

**Important:** Banks may report overlapping segmentations rather than a single strict hierarchy. The schema must not assume that every disclosed segment can be summed to produce a portfolio total.

### Core financial and risk metrics

Support, at minimum:

| Metric | Description |
|---|---|
| Exposure | Original balance-sheet or contractual exposure |
| EAD | Exposure at Default |
| RWA | Risk-Weighted Assets |
| Risk Weight | RWA / EAD |
| PD | Probability of Default |
| LGD | Loss Given Default |
| ECL / EL | Expected Credit Loss / regulatory Expected Loss, separately defined |
| Default count | Number of defaulted exposures |
| Default rate | Observed default frequency |
| CET1 capital | Common Equity Tier 1 |
| Tier 1 capital | Regulatory Tier 1 |
| Total regulatory capital | Regulatory capital |
| Capital adequacy ratio | Capital / RWA |
| Capital intensity | Capital / exposure |
| Leverage ratio | Tier 1 capital / regulatory leverage exposure |

Store metric definitions and denominator conventions explicitly.

For example, average PD might be weighted by borrower count or EAD. These are different measures and must not be silently combined.

Similarly, distinguish loan balances, gross exposures, post-credit-conversion-factor EAD and leverage exposures.

### Recommended database architecture

Use a **hybrid dimensional and relational model**, rather than a single wide table with fixed columns for every possible disclosure.

Suggested entities:

```text
Institution
ReportingEntity
Jurisdiction
RegulatoryFramework
RegulatoryFrameworkVersion
ReportingPeriod
DisclosureDocument
DisclosureTable
Portfolio
PortfolioSegment
SegmentationDimension
BandDefinition
DisclosureObservation
MetricDefinition
MetricValue
SourceReference
ExtractionRun
NormalizationRule
CalculationRun
DerivedMetric
```

`DisclosureObservation` should identify a reported row and its dimensional context.

`MetricValue` should hold the associated numerical observations using canonical metric identifiers and units.

`BandDefinition` must support configurable ranges for PD, LVR, risk weights and other numerical or categorical segmentation variables.

Band boundaries need explicit inclusivity, units and handling of open-ended ranges.

The schema must also distinguish:

- Source-specific portfolio classifications from canonical classifications.
- Raw disclosures from normalised disclosures.
- Original observations from estimates.
- Detailed rows from subtotals and totals.
- Reporting dates from publication dates.
- Original documents from subsequent corrections or restatements.

Use structured, typed fields for important financial quantities. JSON metadata may support uncommon dimensions, but should not replace relational structure for core metrics.

---

# 3. Disclosure acquisition and PDF extraction

## 3.1. Source discovery

Create a configurable mechanism for locating and downloading regulatory disclosures.

Initial target institutions:

- Commonwealth Bank of Australia
- Westpac
- National Australia Bank
- ANZ
- Macquarie
- ING Australia, where relevant

Support historical backfilling and ongoing retrieval of newly published disclosures.

Initial document types:

- APS 330 disclosures.
- Basel Pillar 3 reports.
- Annual and interim financial reports where relevant.
- Supplementary regulatory disclosure spreadsheets.

The source-discovery system should be extensible to international institutions.

Every downloaded document must be retained in its original form, with source URL, retrieval date, SHA-256 checksum and publication metadata.

## 3.2. Extraction pipeline

Implement a modular extraction pipeline:

```text
Source Discovery
       ↓
Document Download
       ↓
Document Classification
       ↓
Table Detection
       ↓
Table Extraction
       ↓
Semantic Interpretation
       ↓
Schema Mapping
       ↓
Validation
       ↓
Database Persistence
```

### Extraction requirements

The extraction system must handle:

- Native PDF tables.
- Tables spanning multiple pages.
- Multi-level column headings.
- Different bank-specific reporting formats.
- Footnotes and explanatory text.
- Historical changes in disclosure layouts.
- Different currencies, units and percentage formats.
- Missing values and ambiguous cells.

Use deterministic PDF extraction where possible, with structured LLM-assisted extraction as an optional fallback for complex layouts. OCR should be reserved for scanned documents.

A bank-specific adapter architecture should allow extraction rules to vary without changing the underlying database schema.

### Source provenance

Every extracted metric must be traceable to its original source.

At minimum, retain:

```text
document_id
document_version
page_number
table_identifier
row_identifier
column_identifier
original_value
original_unit
normalised_value
normalised_unit
extraction_method
extraction_confidence
validation_status
```

Where feasible, also retain PDF cell coordinates and footnote references.

The system should support manual correction without overwriting the original extracted value.

**All published values must be auditable back to their source documents.**

---

# 4. Data normalisation and comparability

This is a central technical challenge.

Different banks, regulatory jurisdictions and reporting periods may disclose similar information using different classifications, aggregation levels or definitions.

The system must support like-for-like comparisons without concealing these differences.

## 4.1. Canonical classifications

Create a mapping layer between original disclosures and standardised portfolio definitions.

For example:

```text
Bank A: Australian Housing Loans
Bank B: Residential Mortgages — Australia
Bank C: Retail Secured Property

             ↓

Canonical Portfolio:
AU_RESIDENTIAL_MORTGAGE
```

Mappings must be versioned and capable of representing partial or conditional equivalence.

Importantly, a common name does not guarantee equivalent reporting scope.

## 4.2. PD and risk-weight band normalisation

Banks may disclose PD distributions using different bands.

For example:

```text
Bank A:
0.00–0.10%
0.10–0.50%
0.50–1.00%
1.00–5.00%
>5.00%

Bank B:
0.00–0.15%
0.15–0.25%
0.25–0.75%
0.75–2.50%
2.50–10.00%
>10.00%
```

Implement a configurable mechanism to map these observations onto common analytical distributions.

The system should support:

1. Direct comparison where band definitions are equivalent.
2. Aggregation into broader common bands.
3. Distribution reconstruction from disclosed band totals and means.
4. Interpolation or estimation where required.
5. Explicit uncertainty and sensitivity analysis.

**Do not assume that observations are uniformly distributed within reported bands.**

Where average PD is disclosed for each band, preserve it as an observed first moment.

Where only band boundaries and EAD are available, treat the underlying PD distribution as unidentified.

Any reconstruction must preserve known constraints, such as band exposure totals and disclosed average PDs.

Potential reconstruction methods include constrained maximum-entropy estimation, parametric distributions and sensitivity bounds.

All such results must be labelled as estimates rather than observed data.

## 4.3. Regulatory standardisation

Historical regulatory changes must not be confused with changes in underlying portfolio risk.

The analysis must support two distinct views:

**As-reported view**

Uses the original regulatory definitions and disclosed metrics applicable at the reporting date.

**Standardised analytical view**

Recalculates relevant metrics using a consistent, explicitly selected regulatory capital function and common assumptions.

This will permit meaningful comparisons across major changes to Australia's prudential framework, including the 2016 and 2023 mortgage capital reforms.

The 2025 APS 330 disclosure regime provides a useful modern reference. Its Basel-aligned CR6 template includes EAD, average PD, average LGD, RWA and RWA density by PD range, making it particularly relevant for this project. [APRA](https://www.apra.gov.au/standards/aps-330?utm_source=chatgpt.com)

---

# 5. Analytical framework

## 5.1. Basel regulatory capital functions

Implement a library of regulatory capital functions.

The initial implementation should support the Basel IRB residential mortgage capital function.

Subsequent implementations may cover other retail, corporate and specialised lending portfolios.

Functions should support:

- PD.
- LGD.
- Asset correlation.
- Regulatory maturity adjustments where applicable.
- Scaling factors.
- Input floors.
- Risk-weight floors.
- Jurisdiction-specific modifications.

The function implementations must be versioned and independently testable.

Critically, distinguish the unfloored mathematical capital function from the actual regulatory calculation including floors and overlays.

## 5.2. PD Differentiation Benefit

This is the project's primary original analytical metric.

For a portfolio with exposure-weighted average PD:

\[
\overline{PD}=\sum_i w_iPD_i
\]

Let \(f(PD)\) be a standardised mortgage risk-weight function, with LGD and other parameters held constant.

Define the undifferentiated portfolio risk weight:

\[
RW_0=f(\overline{PD})
\]

And the differentiated portfolio risk weight:

\[
RW_D=\sum_i w_i f(PD_i)
\]

The **PD Differentiation Benefit (PDB)** is:

\[
\boxed{
PDB=1-\frac{RW_D}{RW_0}
}
\]

This is a normalised Jensen gap.

### Interpretation

| PDB | Interpretation |
|---|---|
| 0% | No capital benefit from PD differentiation |
| 10% | Modelled RWA is 10% below the uniform-PD benchmark |
| 25% | Modelled RWA is 25% below the benchmark |
| 40% | Modelled RWA is 40% below the benchmark |

For a concave capital function, greater PD dispersion can reduce average modelled risk weights without changing average PD.

The PDB allows comparison between banks with different average PDs by measuring the capital effect of differentiation relative to each bank's undifferentiated benchmark.

### Implementation requirements

Calculate PDB at several granularities:

- Portfolio.
- Bank.
- Reporting period.
- Portfolio segment.
- Regulatory framework.
- Standardised comparison group.

Support both absolute and relative differentiation benefits:

\[
\Delta RW=RW_0-RW_D
\]

\[
PDB=\frac{\Delta RW}{RW_0}
\]

Also expose the normalised capital ratio:

\[
NCR=\frac{RW_D}{RW_0}=1-PDB
\]

The zero-differentiation benchmark therefore has \(NCR=1\).

### Important analytical constraints

- PDB measures the capital effect of assigned PD dispersion, **not predictive discrimination or model quality**.
- Grouped-data estimates omit within-band differentiation. Under a concave capital function and accurately reported band means, the grouped PDB is a lower bound on the underlying loan-level PDB.
- Concavity must not be assumed for every regulatory function or across every PD range.
- Floors, overlays and heterogeneous regulatory multipliers may materially alter the result.
- Defaulted exposures should initially be analysed separately.

The software must calculate and report these limitations explicitly.

---

# 6. Additional analytical capabilities

## 6.1. Capital adequacy and capital intensity

Correctly distinguish:

\[
\text{Risk Weight}=\frac{RWA}{EAD}
\]

\[
\text{Capital Adequacy Ratio}=\frac{Capital}{RWA}
\]

\[
\text{Capital Intensity}=\frac{Capital}{Exposure}
\]

For a consistent exposure definition:

\[
\text{Capital Intensity}
=
\text{Risk Weight}\times\text{Capital Adequacy Ratio}
\]

The system must prevent misleading comparisons between ratios with different denominators.

It should distinguish actual institution-level capital holdings from **model-implied portfolio capital allocations**, calculated using an assumed or target capital ratio.

An important objective is to quantify the potential capital savings associated with PD differentiation:

\[
\text{Illustrative Capital Saving}
=
\Delta RW \times EAD \times c
\]

where \(c\) is an explicitly selected regulatory or target capital ratio.

These savings must be presented as potential rather than realised where other binding capital constraints apply.

## 6.2. RWA decomposition

Implement a counterfactual decomposition framework to explain differences in modelled risk weights between portfolios.

For banks A and B:

\[
\frac{RW_A}{RW_B}
=
\frac{f(\overline{PD}_A)}{f(\overline{PD}_B)}
\times
\frac{1-PDB_A}{1-PDB_B}
\]

This decomposes differences under a common capital function into:

1. An average-PD effect.
2. A PD-distribution effect.

Additional analyses should progressively incorporate:

- LGD differences.
- Portfolio mix.
- Regulatory multipliers.
- Capital floors.
- Other disclosed adjustments.

Where several effects interact, support order-independent attribution using Shapley decomposition.

Do not claim that residual differences necessarily represent model conservatism.

## 6.3. Longitudinal analysis

Track changes in risk-weight characteristics through time.

Primary metrics:

- Average PD.
- Average LGD.
- Reported risk weight.
- Standardised modelled risk weight.
- PD Differentiation Benefit.
- Exposure distribution across PD bands.
- Capital intensity.
- CET1 and leverage ratios.

Investigate:

- Trends in PDB within each institution.
- Differences in PDB between institutions.
- Changes around regulatory reforms.
- Changes during economic cycles.
- Changes coinciding with disclosed model redevelopment or recalibration.
- Associations with capital pressure, profitability and return on equity.

Distinguish movements caused by portfolio composition from changes in risk estimates.

## 6.4. Calibration, discrimination and stability

Provide a framework for subsequently integrating model performance information.

Potential analyses include:

- Observed versus expected defaults.
- Calibration by PD grade.
- Rank-based discrimination measures.
- Stability of PD distributions.
- Population Stability Index.
- Rating migration matrices.
- Changes in capital requirements under common macroeconomic scenarios.
- Procyclicality measures.

These capabilities may require supplementary data beyond public disclosures.

The software must identify unavailable data rather than fabricate model-performance results.

---

# 7. Visualisation and reporting

Provide a Python-based analytical and visualisation layer.

Initial outputs should include:

### A. Cross-bank comparisons

Scatter plot of standardised portfolio risk weight versus average PD.

Overlay the theoretical no-differentiation capital curve.

Use the distance below the curve to illustrate the PD Differentiation Benefit.

### B. Longitudinal PDB

Plot PDB over time for each bank.

Highlight material regulatory changes and relevant economic periods.

### C. PD distributions

Compare exposure-weighted PD distributions between banks.

Support raw bands, common aggregated bands and reconstructed distributions.

### D. RWA decomposition

Show the contribution of average PD, PD differentiation and other modelled factors to differences in capital requirements.

### E. Capital adequacy versus capital intensity

Compare risk-weighted capital ratios with measures of capital relative to actual exposures.

Explicitly distinguish changing capital numerators from changing RWA denominators.

### F. Research exports

Support reproducible exports to:

- CSV.
- Parquet.
- Markdown.
- HTML charts and analytical reports.

Every chart should reference its source data, calculation version and assumptions.

---

# 8. Proposed technical architecture

The application should be modular, testable and suitable for extension.

Suggested package structure:

```text
bank_capital_analytics/
│
├── config/
│   ├── institutions/
│   ├── jurisdictions/
│   ├── regulatory_frameworks/
│   └── mappings/
│
├── data/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   └── migrations/
│
├── acquisition/
│   ├── discovery/
│   ├── downloaders/
│   └── source_registry/
│
├── extraction/
│   ├── pdf/
│   ├── tables/
│   ├── adapters/
│   └── validation/
│
├── normalization/
│   ├── portfolios/
│   ├── metrics/
│   ├── banding/
│   └── reconstruction/
│
├── regulatory/
│   ├── basel/
│   ├── apra/
│   └── capital_functions/
│
├── analytics/
│   ├── differentiation/
│   ├── capital/
│   ├── decomposition/
│   ├── longitudinal/
│   └── statistics/
│
├── reporting/
│   ├── charts/
│   ├── tables/
│   └── exports/
│
├── cli/
│
└── tests/
```

### Suggested technology choices

| Component | Recommendation |
|---|---|
| Language | Python 3.12+ |
| Configuration | Pydantic v2 / pydantic-settings |
| Database models | SQLAlchemy 2.x |
| Database migrations | Alembic |
| Durable relational database | PostgreSQL |
| Local analytical processing | DuckDB |
| DataFrames | Polars |
| Columnar interchange | PyArrow / Parquet |
| Data validation | Pandera / Pydantic |
| PDF extraction | PyMuPDF, pdfplumber |
| Table extraction | PyMuPDF tables, Camelot where appropriate |
| Numerical analysis | NumPy, SciPy |
| Statistical modelling | SciPy, statsmodels |
| Visualisation | Plotly |
| Testing | pytest |
| CLI | Typer |
| Dependency management | uv |

Prefer explicit interfaces between modules, with minimal coupling between data acquisition, regulatory calculations and statistical analysis.

For local development, PostgreSQL could initially be run through Docker. DuckDB can operate directly against analytical extracts without becoming the authoritative source of regulatory observations.

Use precise decimal or fixed-point representations for stored financial quantities. Floating-point conversion is acceptable within numerical calculations where appropriate.

---

# 9. Data quality and reproducibility

This project depends on reliable handling of imperfect public disclosures.

Implement validation at every stage.

### Required validation controls

**Extraction validation**
- Table totals reconcile with reported subtotals.
- Percentages and monetary units are interpreted correctly.
- PD band boundaries are valid.
- Missing values remain distinguishable from zeros.

**Financial validation**
- RWA density reconciles with RWA / EAD.
- Average PD reconciles with disclosed band values where possible.
- Capital adequacy ratios use correct denominators.
- Aggregated observations avoid double counting.

**Analytical validation**
- Standardised Basel calculations reproduce known reference results.
- PDB equals zero for uniform PD portfolios.
- PDB behaves consistently with Jensen's inequality where concavity applies.
- Capital calculations are consistent across equivalent grouped and ungrouped data, within their stated approximation limits.

**Reproducibility**
- Every analytical result identifies the source observations used.
- Every calculation records its methodology version.
- Regulatory parameters and assumptions are versioned.
- Re-running a calculation with the same inputs produces identical results.
- Corrections to extracted data do not erase earlier calculation history.

### Data quality classifications

Assign explicit quality statuses, such as:

```text
OBSERVED_VERIFIED
OBSERVED_UNVERIFIED
DERIVED_EXACT
ESTIMATED
INTERPOLATED
UNAVAILABLE
REJECTED
```

Maintain a separate confidence or uncertainty measure where appropriate.

Do not confuse extraction confidence with statistical estimation uncertainty.

---

# 10. Implementation roadmap

The project should be developed incrementally, with a complete working analytical pipeline established before attempting broad historical coverage.

## Phase 1 — Core analytical engine

**Objective:** Validate the mathematical and analytical framework independently of PDF extraction.

Deliverables:

- Basel mortgage capital function.
- PDB calculations.
- Capital-intensity calculations.
- Standardised RWA decomposition.
- Synthetic test portfolios.
- Unit tests for mathematical properties.

**Acceptance criterion:** Given two synthetic portfolios with identical EAD-weighted average PD and different PD distributions, the system correctly computes their modelled RWA and differentiation benefit.

## Phase 2 — Database and canonical schema

**Objective:** Persist regulatory disclosures at multiple granularities.

Deliverables:

- Relational database models.
- Migrations.
- Metric dictionary.
- Portfolio hierarchy and segmentation system.
- PD band definitions.
- Data provenance structures.
- Repository interfaces.

**Acceptance criterion:** Store two banks' disclosures with different PD band structures without altering the schema.

## Phase 3 — PDF ingestion proof of concept

**Objective:** Build an end-to-end ingestion pipeline.

Start with two modern disclosures from CBA and Westpac containing mortgage PD-band data.

Modern Basel-aligned CR6 disclosures are preferable initially because the tables have a more consistent structure.

Deliverables:

- Document downloader.
- PDF table extractor.
- Bank-specific extraction adapters.
- Structured data validation.
- Database persistence.
- Source traceability.

**Acceptance criterion:** Extract all required mortgage PD-band metrics from each report and reconcile their totals against the original disclosures.

## Phase 4 — Normalisation and historical expansion

**Objective:** Build a comparable longitudinal dataset.

Expand across the available disclosures for approximately 2016–2026.

Deliverables:

- Historical source registry.
- Additional bank adapters.
- Portfolio mapping rules.
- PD band harmonisation.
- Distribution reconstruction.
- Regulatory framework versioning.
- Data-quality and coverage reports.

**Acceptance criterion:** Produce comparable bank-period observations with explicit classification of directly observed, derived and estimated values.

## Phase 5 — Longitudinal analytical study

**Objective:** Investigate the research hypotheses.

Deliverables:

- Ten-year PDB dataset.
- Bank comparison charts.
- PD versus RWA analysis.
- Regulatory reform comparisons.
- Capital intensity estimates.
- Counterfactual decomposition.
- Statistical investigation of persistent bank-level differences.

**Acceptance criterion:** Produce a reproducible analytical report comparing mortgage risk-weight outcomes across available banks and reporting periods.

## Phase 6 — Ongoing monitoring and broader coverage

**Objective:** Transition from a research pipeline to a reusable analytical platform.

Possible extensions:

- Automated retrieval of new disclosures.
- Additional international jurisdictions.
- Corporate and other retail portfolios.
- Interactive dashboard.
- Model performance and calibration datasets.
- Macro stress-testing scenarios.
- Public analytical data releases.

---

# 11. Initial research questions

The project should be designed to answer the following questions.

| ID | Research question |
|---|---|
| RQ01 | How much do mortgage risk weights vary between Australian IRB banks? |
| RQ02 | How much variation can be explained by differences in average PD? |
| RQ03 | How much can be explained by the distribution of PD around its average? |
| RQ04 | Do banks exhibit persistent differences in PD Differentiation Benefit? |
| RQ05 | How has PDB changed over the last ten years? |
| RQ06 | Are differences in PDB associated with changes in regulation or modelling practices? |
| RQ07 | How much of the reported risk-weight difference translates into differences in capital intensity? |
| RQ08 | Are changes in PDB associated with capital adequacy, profitability or ROE? |
| RQ09 | Are observed differences consistent with legitimate credit risk differentiation, more conservative modelling or capital optimisation? |
| RQ10 | How sensitive are the conclusions to missing data, PD band granularity and distribution reconstruction assumptions? |

RQ09 is an interpretive research question. Public disclosures alone cannot establish deliberate regulatory arbitrage or inappropriate model development.

The software should quantify evidence and uncertainty, leaving questions of intent to carefully supported interpretation.

---

# 12. Initial reference materials

The implementation should begin by studying these sources.

**Regulatory specifications**

- [APRA — APS 330 Public Disclosure](https://www.apra.gov.au/standards/aps-330)
- [APRA — APS 113 Internal Ratings-Based Approach to Credit Risk](https://www.apra.gov.au/standards/aps-113)
- [Basel Committee — Pillar 3 Disclosure Requirements](https://www.bis.org/committees/bcbs/basel-framework/standard/dis.htm)

**Analytical context**

- [APRA — Demystifying Credit Risk Capital Requirements for Housing Loans](https://www.apra.gov.au/news-and-publications/demystifying-credit-risk-capital-requirements-housing-loans)
- [RBA — Regulatory Capital Framework for Residential Mortgages](https://www.rba.gov.au/publications/fsr/2015/oct/box-c.html)
- [From the Outside — The Case for Low Mortgage Risk Weights](https://from-the-outside.com/2020/03/09/the-case-for-low-mortgage-risk-weights/)
- [From the Outside — Mortgage Risk Weights Revisited](https://from-the-outside.com/2019/12/05/mortgage-risk-weights-revisited/)

The project should also establish a registry of the relevant bank disclosure archives.

---

# 13. Engineering principles

The coding agent should follow these principles throughout implementation.

**1. Source data is immutable.**  
Original downloaded disclosures and extracted values must be preserved. Corrections, mappings and estimates are separately versioned.

**2. Regulation is configuration, not hard-coded business logic.**  
Regulatory functions may require Python implementations, but jurisdiction-specific parameters, effective dates, floors, multipliers and mappings must be explicit and versioned.

**3. Comparability must be demonstrated, not assumed.**  
A metric with the same name in two disclosures is not necessarily comparable.

**4. Reported and modelled results must remain separate.**  
A theoretical calculation using standardised assumptions must never be misrepresented as a bank's actual regulatory capital requirement.

**5. Missing information is not invented.**  
Interpolation, imputation and distribution reconstruction require explicit methods and uncertainty reporting.

**6. Every analytical result must be reproducible.**  
The underlying source data, transformation steps and modelling assumptions must be identifiable.

**7. Prefer modular, testable components.**  
Regulatory functions, extraction adapters, database models and statistical analyses should be independently reusable.

**8. Build vertically before scaling horizontally.**  
Demonstrate the complete workflow for a small number of disclosures before expanding to ten years of historical data.

---

# 14. Instructions to the coding agent

The first task should be to turn this brief into a technical design and phased implementation plan.

Specifically:

1. Review the requirements and relevant regulatory disclosure specifications.
2. Propose the canonical database schema, including relationships, metric definitions, flexible segmentation and provenance.
3. Identify the minimum data needed to calculate the PD Differentiation Benefit.
4. Develop the Basel mortgage risk-weight calculation and associated mathematical tests.
5. Identify two suitable bank disclosures for the first ingestion proof of concept.
6. Define the extraction adapter interface and validation strategy.
7. Produce a repository structure, development milestones and acceptance tests.

**Do not begin by scraping ten years of reports.** Establish the analytical engine, data contracts and a validated end-to-end ingestion example first.

The initial proof of concept should demonstrate:

```text
CBA Pillar 3 PDF      Westpac Pillar 3 PDF
         │                    │
         ▼                    ▼
    PDF Extraction       PDF Extraction
         │                    │
         └─────────┬──────────┘
                   │
                   ▼
          Canonical Database
                   │
                   ▼
       Normalised PD Distributions
                   │
                   ▼
       Standardised Basel Function
                   │
                   ▼
          PD Differentiation
             Benefit (PDB)
                   │
                   ▼
        Comparative Analysis
                   │
                   ▼
          Reproducible Charts
```

### Definition of success

The initial project is successful when it can ingest two banks' published mortgage disclosures, reconstruct their disclosed PD distributions, calculate a consistent theoretical capital benchmark, quantify their PD Differentiation Benefits, and explain the resulting differences with full source traceability.

The longer-term success criterion is a reliable, extensible dataset and analytical framework capable of investigating a decade of bank regulatory capital disclosures.

---

## A final architectural recommendation

I would treat this as **two related but independent systems**:

**1. A regulatory disclosure data platform**, which acquires, interprets, normalises and stores bank disclosures without presupposing a particular analytical purpose.

**2. A regulatory capital analytics library**, which implements capital functions, PD differentiation metrics, counterfactuals and longitudinal statistical methods.

That separation is important.

The disclosure platform could eventually become a reusable public data resource, supporting research beyond this particular hypothesis.

The analytics library could operate against either the public disclosure database or more granular private loan-level data, allowing the same methods to be applied to actual portfolio modelling and validation.

And I would ensure that **the PD Differentiation Benefit is treated as a general mathematical measure of the capital effect of a risk distribution**, rather than a metric intrinsically tied to Australian mortgages.

That makes the initial research project a practical demonstration of a more broadly useful analytical framework.
