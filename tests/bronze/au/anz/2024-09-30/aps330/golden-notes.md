# ANZ September 2024 independent source expectations

Authored before the extractor, from the tracked official PDF's rendered pages
53–55 and 57 (printed 52–54, 56); all 125 selected body positions transcribed.
Rendered inspection: `/tmp/opencode/anz2024-{53,54,55,57}.png`.
Definitions reviewed on PDF pp.4,25,27–28,46–49,100–101, not imported from another vintage.

The selected rows are **Residential Mortgage**, five measures across eight columns
on each exposure panel, plus five backtesting measures. No New Zealand aggregate,
other portfolio, table-wide total row or percent-of-total row is selected. The
rightmost **mortgage** Total column is selected. Preserve original two-line bands;
lower-bound inclusivity is unspecified, upper bounds explicitly use `<`.
Undrawn is included in EAD, not additive to it. Total relationships do not assert
that averages are sums or that children are disjoint/exhaustive.

Money is AUD millions (p.4); average EAD's counted entity is not established by
the definition of EAD as facility exposure. Backtesting EAD is a dimensionless
ratio; the adjacent PD/LGD `%` markers do not apply to it. Retail PD/EAD history
2019–2023 differs from LGD history 2018–2022. September 2023 is retained separately
as the actual-PD and LGD default cutoff, without inventing a precise day or a
single common window. The historical LGD review sentence lies under Wholesale
Portfolios, above Retail Portfolios: retain its evidence with unresolved mortgage
applicability, rather than claiming retail restatement.

Test-audit gate: the real `run_extractor` boundary must return complete source
numbers, axis paths, units, relationships, qualifications and field-specific time.
Wrong repeated-row selection, percent scaling in Bronze, dropped two-line headers,
borrowed wholesale timing and invented portfolio totals are credible regressions.
No existing test owns ANZ 2024 source correctness. No test-only production seam.
