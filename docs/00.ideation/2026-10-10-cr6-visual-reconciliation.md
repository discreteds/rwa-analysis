# CR6 visual reconciliation — 10 October 2026

Reviewer: **OpenAI GPT-6 Astra, LLM agent**. This is not human sign-off.

## Review in progress

The initial direct review used a scratch rendering of the actual published
`cr6-2025-v1` warehouse. Its manifest and four Bronze `v1` bundles record producer
`198ea6ada83e1b9cae2c59e752487644584c9e18`; a newer renderer must not claim to be
that producer. The draft returned zero exact-value or metadata findings.

The agent opened the actual source-page images rendered with
`pdfplumber.Page.to_image` and browser screenshots of all four Bronze and Silver
reconstructions. Each selected block contains eight bands and one aggregate,
with all twelve source field positions. Numeric bodies, original precision,
blank/dash distinctions, headers and row order matched the source pages.

- **CBA PDF/printed 55:** empty maturity and band provisions, subtotal, PD/RWA/
  density footnote markers 1–3. The reported 22% density remains reported;
  it was not replaced by a quotient of rounded numbers.
- **Westpac PDF/printed 48:** early mortgage rows above the vertically centred
  portfolio label are included; default CCF is a dash, maturity is blank.
  Direct review of p. 49 confirms density footnote a; corporate-only footnote b
  is not applied to mortgages.
- **NAB PDF 49 / printed 47:** columns a–l, one-decimal density (including 6.0%),
  shaded maturity and band provisions, unshaded aggregate provision. Direct
  review of PDF 48 / printed 46 confirms agreement counts, disclosure at asset
  class rather than band level, and exclusion of overlays from RWA/density.
- **ANZ PDF/printed 57:** source rows 10–18, AIRB scope, dashes for maturity,
  blank band provisions, subtotal and footnotes 1–3. Direct images of pp. 6–7,
  23, 54 and 116 confirm entity/Level 2 scope, AUD millions, the separate CMS2 overlay
  evidence, Suncorp's exclusion from IRB-specific tables and the retail maturity
  template modification.

No source-backed extraction or conformance correction was identified in this
draft review. Native source colours and shading not captured as source metadata
are not invented in the reconstruction; the original image remains available.

Final artifact paths, clean renderer revision, final persisted Silver browser review,
verification and backup recovery results will be recorded after generation.

## Retained semantic limitations

CBA currency and several geographies, most weighting conventions and borrower
distinctness remain unresolved. NAB counts agreements (mapped to arrangements),
not an asserted count of distinct people. ANZ CR6 overlay treatment remains
unresolved: the CMS2 statement is cross-table evidence, not automatic CR6
inheritance. These are legitimate research limitations, visible in the source
notes and field interpretations, not extraction errors or reasons to drop values.

See [extraction and review commands](../workflows/cr6-extraction.md) and
[retention/recovery](../workflows/silver-rebuild.md).
