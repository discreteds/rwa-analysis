"""Physical readers selected by this source's reviewed bindings."""

from rwa_analysis.extraction.physical import (
    anchored_prefix_rows,
    cropped_text_region,
    line_band_matches,
    line_match_groups,
    paragraph,
)

OPERATIONS = {
    "paragraph": paragraph,
    "region": cropped_text_region,
    "line": line_match_groups,
    "rows": anchored_prefix_rows,
    "bands": line_band_matches,
}
