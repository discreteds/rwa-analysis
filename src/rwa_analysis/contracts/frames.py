"""Validate already-typed frames without changing their physical types."""

import mountainash as ma
import polars as pl


def conform_frame(frame: pl.DataFrame, spec: ma.TypeSpec) -> pl.DataFrame:
    """Preserve explicit physical types; fail on contract errors."""
    if spec.missing_values != []:
        raise ValueError("Typed frames require explicit missingValues: []")
    if any(field.missing_values for field in spec.fields):
        raise ValueError("Typed frames reject nonempty field missingValues")
    result = ma.relation(frame).conform(spec, apply_value_transforms=False).collect()
    contract = ma.datacontract(spec)
    contract.Config = type("Config", (), {"coerce": False})
    report = contract.validate_datacontract(result)
    if not report.passes:
        raise ValueError(str(report.check_summaries))
    if result.schema != frame.schema:
        raise ValueError("Unexpected physical dtype change")
    return result
