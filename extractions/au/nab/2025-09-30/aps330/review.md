# NAB September 2025 mortgage CR6 source review

Reviewed 2026-10-10 directly from the saved [PDF](../../../../../raw/nab-2025-09-30-aps330.pdf), before writing the extractor. Rendered PDF pages 48 and 49 (printed 46 and 47) and page 4 (printed 2); also inspected the cover, summary PDF 13 / printed 11 and CMS2 PDF 18 / printed 16. The source-specific golden was independently transcribed from these pages, not from extractor output or another bank's fixture.

## Selected structure

- One dataset, `cr6-residential-mortgages`, in `au/nab/2025-09-30/aps330`.
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
