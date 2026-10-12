# NAB September 2025 mortgage CR6/CR9 source review

Reviewed 2026-10-10 directly from the saved [PDF](../../../../../raw/nab-2025-09-30-aps330.pdf), before writing the extractor. Rendered PDF pages 48 and 49 (printed 46 and 47) and page 4 (printed 2); also inspected the cover, summary PDF 13 / printed 11 and CMS2 PDF 18 / printed 16. The source-specific golden was independently transcribed from these pages, not from extractor output or another bank's fixture.

## Selected structure

- Original CR6 dataset, `cr6-residential-mortgages`, in `au/nab/2025-09-30/aps330`; the CR9 extension below shares this logical bundle.
- PDF 49's **Residential mortgage** block: seven explicit PD intervals, `100.00 (Default)`, and `Sub-total`. The Retail SME block above it is separate.
- All twelve columns **a–l**, including blank positions, are selected: 9 rows, 108 positions, 91 numeric values and 17 blanks. There are no dashes in this selected block. Default CCF is **85%**, not a missing token.
- The A-IRB heading and CR6 title are on PDF 48; the date on PDF 49 is `As at 30 Sep 25`. The reporting date is 2025-09-30. Printed page numbers are two less than PDF positions; the cover has no printed page label.
- The seven intervals are lower-inclusive and upper-exclusive as printed; default is a separate category. The subtotal relationship is local to this mortgage block. This population partition does not establish that counts represent distinct people or that percentage fields are additive.

## Definitions and applicability

PDF 48's column (f) definition distinguishes **agreements** for residential mortgage, qualifying revolving retail and other retail from **counterparties** for corporate (including SME), retail SME, sovereign and financial institution portfolios. The complete passage is retained, scoped to the selected mortgage count field. Its interpreted counted entity is `agreement`; distinctness remains unresolved. The corporate counting rule does not become a mortgage rule.

The same page expressly states: “RWA in column (i) and RWA density in column (j) exclude RWA overlay adjustments.” Both fields retain that qualification and an excluded-overlay attribute. The CR6 subtotal is **112,014 $m**, whereas the summary and CMS2 modelled-approach mortgage RWA are **112,064 $m**. The summary's footnote (2) says credit RWA includes an off-balance-sheet measurement overlay, and CR6 explicitly excludes overlays. This is source-qualified measure-basis evidence, not a failed extraction or authority to replace CR6 RWA. The 50 $m difference is not an independently disclosed mortgage overlay allocation; no adjustment or band allocation is made.

Columns (a) and (b) retain **On-balance / sheet EaD / pre-CRM** and **Off-balance / sheet EaD / pre-CCF and / pre-CRM**. Column (d) is **EaD / post-CCF / and / post-CRM**. These labels do not establish equivalence with another bank's gross exposure definition. Column (e) explicitly says **Weighted average PD**; the captured NAB CR6 passages do not identify the weight basis. Weighting remains unresolved rather than inheriting a CR9 or corporate convention.

## Shading, template definitions and missingness

Direct rendering shows a dark shaded maturity column (h), including the subtotal, and shaded provision column (l) cells only for the eight PD rows. The subtotal provision **1,126 $m** is visible. There is no stand-alone colour legend on these NAB pages. The controlling NAB CR6 definitions explain the template omissions:

- (h) “only disclosed for asset classes where it is used for the RWA calculation, consistent with the disclosure template prescribed by APS 330.” Together with the selected mortgage column's omission, this supports `not_applicable` for its nine maturity positions, specifically in the CR6 RWA-calculation/disclosure context.
- (l) “disclosed for each asset class and not by PD band”, also explicitly referring to the APS 330 template. The eight band provision positions are `not_disclosed_at_this_grain`, not zero and not a claim that provisions do not apply to mortgages.

Also inspected the [BCBS CR6 template and Definitions legend](https://www.bis.org/committees/bcbs/basel-framework/standard/dis/40/inforce/2023-01-01/published/2020-03-27#bf-header-86883) (DIS40 Table 12, effective 2023-01-01): average maturity “needs to be filled in only when it is used for the RWA calculation.” This corroborates the local note; it is not a universal meaning of grey shading. The external template's gross-exposure and obligor definitions are not substituted for NAB's explicit EaD/agreement wording. The executable bundle captures the NAB PDF evidence and needs no network access.

The wire payload retains blank original text and explicit missing reasons; presentation attributes retain shading separately. These reasons are based on the column definitions and reviewed positions, not colour alone or another bank's blank-cell conventions. Unexpected empty numeric windows elsewhere remain unresolved.

## Units, precision and context

PDF 4 identifies NAB and its controlled entities, defines Level 2 exclusions and applies this report to the Level 2 Group headed by NAB unless stated otherwise. It explicitly states AUD and rounding to the nearest million unless otherwise indicated. Monetary columns retain `$m` and scale 1,000,000; rates retain `%` and their displayed precision; counts are integers. RWA density has **one decimal** in every row, including **6.0%** and **26.1%**. PD has two decimals. No quotient replaces a reported density.

The selected context is A-IRB, Level 2, AUD. Portfolio geography is left unresolved: the Australian reporting folder and AUD currency alone do not prove exposure geography. The cover supplies the reporting entity/title; publication date 2025-11-06 and official URL come from the acquisition index.

## Golden and verification ownership

The [complete golden](../../../../../tests/bronze/au/nab/2025-09-30/aps330/golden.json) owns all values, blanks, labels, field bindings, column IDs, qualifications and page offsets. Its [authoring notes](../../../../../tests/bronze/au/nab/2025-09-30/aps330/golden-notes.md) document independence and the TDD boundary. No shared metadata extension is needed: existing source axes, attributes and scoped qualifications express the observed requirements.

## CR9 extension — source review 2026-10-12

Reviewed retained PDF60–61 (printed58–59), referenced external-rating table PDF46
(printed44), and CR6 count definition PDF48 (printed46). Rendered PDF61 and PDF46
to inspect the table geometry and shading. The independent `golden-cr9.json` was
transcribed before extractor changes; its source contract first failed because
the existing bundle was still CR6-only.

The selected **Residential mortgage** block is PDF61's first block: eight rows,
seven measure positions each, no subtotal. The separately labelled **BNZ
residential mortgage** block is outside this selection. The source says BNZ is
disclosed separately; this does not prove every selected exposure's geography.
Geography remains unresolved rather than inferred from the Australian folder.

Column (c) is split into **As at 30 Sep 25** then **As at 30 Sep 24**. First-band
counts are respectively **198,124** and **215,531**, and keep those measurement
dates despite being reversed relative to the typed previous/current field order.
The other columns are weighted PD (a), arithmetic PD (b), defaults in the year
(d), new-default subset (e), and historical annual default rate (f). Every rate
retains its percent token and two displayed decimal places. There are 51 numeric
positions, two dashes in the new-default column, and three shaded blank default-row
cells (d/e/f). Dashes and blanks remain unresolved missing values, not zero.
Shading is retained as presentation; there is no local legend establishing a
stronger missingness reason.

CR9's introduction explicitly directs external-rating equivalents to printed44.
Its two agency columns are **S&P Global Ratings / Fitch Ratings** and **Moody's
Investor Services**. All eight band-associated labels, including **D / C** for
default, are retained as lexical axes with PDF46 evidence. These are band
equivalents, not per-agreement observed ratings or a rating-assignment date.

PDF60 defines weighted PD as EaD-weighted at the reporting date: measurement and
weight measurement are 2025-09-30. Arithmetic PD is the sum of PDs divided by the
number of borrowers; its measurement date is not expressly established and stays
unresolved. CR9 refers counting back to CR6, which explicitly counts mortgage
**agreements**. The existing agreed arrangement-count interpretation therefore
applies, with distinctness unresolved. This interpretation is separate from the
quoted source and follows the agreed data-semantics principle. The existing
`agreed.nab-mortgage-agreements@v1` decision is historical context only: its
CR6-specific effective-date restriction cannot be imported as an unrestricted
CR9 dependency. `count.arrangements@v1` itself depends on that dated decision.
The executable mappings therefore use the unrestricted generic
`count.reported-borrowers@v1` concept with an established `counted_entity=agreement`
attribute, citing CR9's own count-reference and definition evidence. They preserve
the agreement semantics without bypassing the existing concept's restriction.

Default counts include a new borrower or a performing borrower at financial-year
opening who is non-performing at **any month-end**, including subsequent cures
and exits. The annual descriptor normalises this full-year September2025 report's
financial year to 2024-10-01–2025-09-30; these ISO dates are contextual
interpretation, not an invented source quotation. Seven row-scoped relationships
retain (e) as a subset of (d). The default-stock row's missing event measures do
not create an eighth disclosed subset observation. No forward opening-cohort
canonical outcome equivalence or inferred annual rate is asserted.

The historical column uses a **10-year observation period**, with the cohort not
in default at the beginning of each financial year averaged. Exact history bounds,
denominator details and whether column(d)'s event rules also govern the historical
column remain unresolved. Preserve the note about best-endeavours retrospective
application of revised asset-class definitions effective 1 January2023. Neither
that policy date nor publication date supplies a history boundary.

The new bundle uses `disclosure-v2` and includes both datasets. The unchanged CR6
golden is checked through its original wire projection. Catalogue members are in
`catalogue/{measures,mappings}/nab-cr9-2025-09-30-v1.json`; the parent task owns
release selection and persisted conformance/bank acceptance.
