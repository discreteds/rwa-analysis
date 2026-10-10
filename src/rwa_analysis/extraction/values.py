"""Numeric token conventions observed in the CBA and Westpac disclosures.

Parsing does not decide the meaning of a blank or dash; each source owns that.
"""

from decimal import Decimal


def parse_decimal_token(token: str) -> Decimal | None:
    text = token.strip()
    if text in {"", "-", "–"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    numeric = text[1:-1] if negative else text
    value = Decimal(numeric.replace(",", "").removesuffix("%"))
    if not value.is_finite():
        raise ValueError(f"Nonfinite source token: {token!r}")
    return -value if negative else value


def parse_count_token(token: str) -> int | None:
    value = parse_decimal_token(token)
    if value is None:
        return None
    if value != value.to_integral_value():
        raise ValueError(f"Count must be integral: {token!r}")
    return int(value)
