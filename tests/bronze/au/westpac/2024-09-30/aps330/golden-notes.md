# Independent Westpac 2024 PDF expectations

Authored before the production extractor from the tracked September 2024 PDF,
using rendered pages 45, 56–58 and independently extracted source text. PDF and
printed page numbers coincide. All 27 × 8 exposure positions (p.45), three × six
mortgage backtesting positions (pp.57–58), and the two p.45 note figures are covered.
Values are manually transcribed; no production extractor output generates fixtures.

The full-source test owns omission, wrong-panel, transposition, token/precision,
axis-path, qualifier-scope, relationship and temporal regressions. Existing CBA
tests cannot exercise Westpac's layout or semantics. It invokes the ordinary
extractor entrypoint without production test hooks.

Header superscripts are represented as ᵃ/ᵇ. Whitespace in prose is normalised.
The two dashes are retained as unresolved missing values; `(1%)` means minus one
percent, not a ratio or a positive percentage. No lexical ratings occur in this
selected historical scope. The exposure bands do not disclose boundary inclusion.
Subtotal covers the six non-default bands; Total covers Subtotal and Default.
Neither relationship implies exclusive/exhaustive coverage beyond source evidence.

Page 42 establishes average-PD presentation and facility-level expected-loss rules.
Glossary pp.113–114 supplies EAD, PD, downturn LGD, RWA and default/NPE definitions.
The explicit default definition begins January 2023; it is not retrospectively
assigned to the backtesting history. Pages 2, 7 and 14 establish report context.

The p.45 note's IRB $131,989m and standardised-equivalent $214,081m are September
2024 supplementary observations, not the body RWA $116,228m and not comparatives.
No reconciliation or implied adjustment is supplied.

Backtesting rates retain portfolio grain and the NZ historical-inclusion footnote.
Page 56 says accreditation started in 2008 for *most* portfolios: no exact mortgage
start/end dates are inferred. The one-year default outcome duration and two-year
mortgage workout are retained; neither implies exact history endpoints. EAD's
"up to one year prior" is not an exact one-year anchor. No panel-date fallback
supplies dates for historical averages. Regulatory expected loss alone uses the
panel snapshot date. Annual predictions, cohort anchors and outcome windows have
distinct temporal roles. Weighting conventions and exact NZ contribution remain
unresolved.

The metadata migration extends this same primary boundary to actual captured v4
headers and shared-comment targets. Captured superscripts use the PDF text layer's
plain `a`/`b`; declared display labels retain `ᵃ`/`ᵇ`. The single p.57 NZ passage
serves both 2024 panels, while its p.58 repetition is separately captured. Field
and panel header checks cover all selected panels, including the continuation.
The independent JSON values and note transcriptions are unchanged.
