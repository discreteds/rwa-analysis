# Independent CBA June 2023 expectations

Transcribed from official PDF pages 51–53 (printed 49–51) and 57 (printed 55),
checked against rendered pages before implementation. All 125 body cells and four
numeric note cells are covered. PDF pages 4 and 45–46 provide entity/perimeter and
PD/LGD/EAD definitions. The golden is not produced by the extractor.

June 2023 has a Revised Framework heading, 1.10 scaling and a 7.4 billion overlay
attached to the LGD mortgage row. Neither comparative has an overlay occurrence;
each has 1.06 scaling. Do not backfill current framework semantics into 2022.
The source does not establish geographic coverage or currency solely through the
selected mortgage label or dollar symbol. Average EAD's counted entity stays unknown.

PD backtesting is long-run averaging from 2016, with no explicit end date. Retail
LGD covers defaults in financial years 2016–2022. EAD history endpoints are unknown.
The pre-reform framework statement applies to both backtesting tables. June 2023
restatement notes attach explicitly to the mortgage rows in both tables; LGD/EAD
note 3 is row-scoped, not silently limited to actual LGD. LGD floor note 2 applies
only to estimated downturn LGD. Do not import 2024's ambiguous NZ note attachments.

The test owns the complete source contract: omitting a comparative/metric, replacing
1.06 with 1.10, fabricating overlays, shifting cells or losing scoped historical
metadata must fail here. Existing 2024 coverage cannot exercise these differences.
No production test-only seam is required.
