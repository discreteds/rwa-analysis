"""Strict schema-directed JSON codec; Decimal strings never pass through float.

The declared dataclass fields are the complete wire schema, including nulls.
Generic ReportedValue's parameter determines its numeric JSON representation.
"""

from dataclasses import fields, is_dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from types import UnionType
from typing import Literal, Union, get_args, get_origin, get_type_hints

from .cr6 import ExtractionBundle


def _convert(value, annotation, path, *, decode, parameters=None):
    parameters = parameters or {}
    annotation = parameters.get(annotation, annotation)
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, UnionType):
        for option in args:
            try:
                return _convert(
                    value, option, path, decode=decode, parameters=parameters
                )
            except (TypeError, ValueError):
                pass
        raise ValueError(f"{path}: invalid value for {annotation}: {value!r}")
    if origin is Literal:
        if not any(type(value) is type(x) and value == x for x in args):
            raise ValueError(f"{path}: expected one of {args}")
        return value
    if origin is tuple:
        expected = list if decode else tuple
        if type(value) is not expected:
            raise TypeError(f"{path}: expected {expected.__name__}")
        converted = [
            _convert(
                item, args[0], f"{path}[{i}]", decode=decode, parameters=parameters
            )
            for i, item in enumerate(value)
        ]
        return tuple(converted) if decode else converted
    cls = origin or annotation
    if is_dataclass(cls):
        hints = get_type_hints(cls)
        names = {f.name for f in fields(cls)}
        if decode:
            if type(value) is not dict:
                raise TypeError(f"{path}: expected object")
            if set(value) != names:
                raise ValueError(
                    f"{path}: missing {names - value.keys()}, unknown {value.keys() - names}"
                )
        elif type(value) is not cls:
            raise TypeError(f"{path}: expected {cls.__name__}")
        substitutions = parameters | dict(zip(getattr(cls, "__parameters__", ()), args))
        result = {
            f.name: _convert(
                value[f.name] if decode else getattr(value, f.name),
                hints[f.name],
                f"{path}.{f.name}",
                decode=decode,
                parameters=substitutions,
            )
            for f in fields(cls)
        }
        return cls(**result) if decode else result
    if annotation is Decimal:
        if type(value) is not (str if decode else Decimal):
            raise TypeError(
                f"{path}: expected {'Decimal string' if decode else 'Decimal'}"
            )
        try:
            number = Decimal(value)
        except InvalidOperation as error:
            raise ValueError(f"{path}: invalid Decimal") from error
        if not number.is_finite():
            raise ValueError(f"{path}: nonfinite Decimal")
        return number if decode else str(number)
    if annotation is date:
        if type(value) is not (str if decode else date):
            raise TypeError(f"{path}: expected date")
        return date.fromisoformat(value) if decode else value.isoformat()
    if annotation not in (str, int, bool, type(None)) or type(value) is not annotation:
        raise TypeError(f"{path}: expected {annotation}, got {type(value).__name__}")
    return value


def encode_payload(bundle: ExtractionBundle) -> dict:
    payload = _convert(bundle, ExtractionBundle, "bundle", decode=False)
    # Revalidate the complete boundary, including reference closure and invariants.
    decode_payload(payload)
    return payload


def decode_payload(payload: dict) -> ExtractionBundle:
    return _convert(payload, ExtractionBundle, "bundle", decode=True)
