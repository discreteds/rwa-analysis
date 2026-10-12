"""Strict schema-directed JSON codec; Decimal strings never pass through float.

The cr6-v1 wire keeps flat metadata and records despite Python composition;
disclosure-v2 keeps explicit domain discriminators and composed metadata.
Generic ReportedValue's parameter determines its numeric JSON representation.
"""

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from types import UnionType
from typing import Literal, Union, get_args, get_origin, get_type_hints

from .cr6 import Cr6Dataset
from .cr9 import Cr9Dataset
from .datasets import Dataset, DatasetMetadata, ExtractionBundle
from .models import ReportedValue
from .source_tables import ReportedText, SourceCell, SourceTable


def _convert(value, annotation, path, *, decode, parameters=None, version="cr6-v1"):
    parameters = parameters or {}
    annotation = parameters.get(annotation, annotation)
    # cr6-v1 contains only CR6 datasets; shared bundles impose no record shape.
    if annotation is Dataset:
        if version == "cr6-v1":
            annotation = Cr6Dataset
        elif decode:
            domains = {"cr6": Cr6Dataset, "cr9": Cr9Dataset}
            if version == SOURCE_TABLE_SCHEMA_VERSION:
                domains["source_table"] = SourceTable
            annotation = domains[value["domain"]]
            value = {k: v for k, v in value.items() if k != "domain"}
        else:
            annotation = type(value)
            result = _convert(
                value,
                annotation,
                path,
                decode=False,
                parameters=parameters,
                version=version,
            )
            return {
                "domain": {
                    Cr6Dataset: "cr6",
                    Cr9Dataset: "cr9",
                    SourceTable: "source_table",
                }[annotation],
                **result,
            }
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, UnionType):
        for option in args:
            try:
                return _convert(
                    value,
                    option,
                    path,
                    decode=decode,
                    parameters=parameters,
                    version=version,
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
                item,
                args[0],
                f"{path}[{i}]",
                decode=decode,
                parameters=parameters,
                version=version,
            )
            for i, item in enumerate(value)
        ]
        return tuple(converted) if decode else converted
    cls = origin or annotation
    if is_dataclass(cls):
        hints = get_type_hints(cls)
        if cls is SourceCell:
            kind = value["value_kind"] if decode else value.value_kind
            hints["value"] = {
                "decimal": ReportedValue[Decimal],
                "integer": ReportedValue[int],
                "text": ReportedText,
            }[kind]
        members = tuple(
            f
            for f in fields(cls)
            if not (
                cls is DatasetMetadata
                and version == "cr6-v1"
                and f.name not in LEGACY_METADATA_FIELDS
            )
        )
        names = {f.name for f in members}
        if cls is Cr6Dataset and decode and version == "cr6-v1":
            metadata_names = LEGACY_METADATA_FIELDS
            _object_keys(value, {"id", "records"} | metadata_names, path)
            value = {
                "id": value["id"],
                "metadata": {name: value[name] for name in metadata_names},
                "exposure_rows": value["records"],
            }
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
                version=version,
            )
            for f in members
        }
        if cls is Cr6Dataset and not decode and version == "cr6-v1":
            return {
                "id": result["id"],
                **result["metadata"],
                "records": result["exposure_rows"],
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
    payload = _convert(
        bundle, ExtractionBundle, "bundle", decode=False, version=bundle.schema_version
    )
    # Revalidate the complete boundary, including reference closure and invariants.
    if bundle.schema_version != SOURCE_TABLE_SCHEMA_VERSION:
        decode_payload(payload)
    return payload


def decode_payload(payload: dict) -> ExtractionBundle:
    version = payload["schema_version"]
    if version not in (
        SCHEMA_VERSION,
        DISCLOSURE_SCHEMA_VERSION,
        SOURCE_TABLE_SCHEMA_VERSION,
    ):
        raise ValueError(f"Unsupported schema version: {version}")
    bundle = _convert(payload, ExtractionBundle, "bundle", decode=True, version=version)
    return bundle


SCHEMA_VERSION = "cr6-v1"
DISCLOSURE_SCHEMA_VERSION = "disclosure-v2"
SOURCE_TABLE_SCHEMA_VERSION = "disclosure-v3"
LEGACY_METADATA_FIELDS = {
    "context",
    "axes",
    "published_fields",
    "bindings",
    "segmentations",
    "qualifications",
    "relationships",
}
EXTRACTION_WORKFLOW_VERSION = "cr6-extraction-v1"


def _object_keys(value, names, path):
    if type(value) is not dict:
        raise ValueError(f"{path}: expected object")
    if set(value) != names:
        raise ValueError(
            f"{path}: missing {names - value.keys()}, unknown {value.keys() - names}"
        )


def _nonempty_string(value, path):
    if type(value) is not str or not value.strip():
        raise ValueError(f"{path}: expected nonempty string")


def encode_envelope(
    bundle: ExtractionBundle,
    *,
    output_version: str,
    implementation_revision: str,
    dependency_versions: dict[str, str],
    executed_at: str,
) -> dict:
    """Keep execution provenance outside the exact source payload."""
    envelope = {
        "schema_version": bundle.schema_version,
        "reference": {
            "bundle_key": bundle.bundle_key,
            "output_version": output_version,
        },
        "implementation_revision": implementation_revision,
        "dependency_versions": dependency_versions,
        "extraction_workflow_version": EXTRACTION_WORKFLOW_VERSION,
        "executed_at": executed_at,
        "payload": encode_payload(bundle),
    }
    if bundle.schema_version != SOURCE_TABLE_SCHEMA_VERSION:
        decode_envelope(envelope)
    return envelope


def decode_envelope(
    envelope: dict, *, expected_reference: dict[str, str] | None = None
) -> ExtractionBundle:
    """Reject unsupported versions, dropped metadata and mistyped JSON values."""
    _object_keys(
        envelope,
        {
            "schema_version",
            "reference",
            "implementation_revision",
            "dependency_versions",
            "extraction_workflow_version",
            "executed_at",
            "payload",
        },
        "envelope",
    )
    for field, supported in (
        (
            "schema_version",
            (SCHEMA_VERSION, DISCLOSURE_SCHEMA_VERSION, SOURCE_TABLE_SCHEMA_VERSION),
        ),
        ("extraction_workflow_version", (EXTRACTION_WORKFLOW_VERSION,)),
    ):
        if type(envelope[field]) is not str or envelope[field] not in supported:
            raise ValueError(f"{field}: unsupported version {envelope[field]!r}")
    reference = envelope["reference"]
    _object_keys(reference, {"bundle_key", "output_version"}, "reference")
    for field, value in reference.items():
        _nonempty_string(value, f"reference.{field}")
    if expected_reference is not None and reference != expected_reference:
        raise ValueError("reference: envelope does not match selected Bronze version")
    _nonempty_string(envelope["implementation_revision"], "implementation_revision")
    dependencies = envelope["dependency_versions"]
    if type(dependencies) is not dict or not dependencies:
        raise ValueError("dependency_versions: expected nonempty object")
    for name, version in dependencies.items():
        _nonempty_string(name, "dependency_versions key")
        _nonempty_string(version, f"dependency_versions.{name}")
    _nonempty_string(envelope["executed_at"], "executed_at")
    try:
        timestamp = datetime.fromisoformat(envelope["executed_at"])
        if timestamp.utcoffset() is None:
            raise ValueError("timezone missing")
    except ValueError as error:
        raise ValueError(
            "executed_at: expected timezone-aware ISO timestamp"
        ) from error
    try:
        if envelope["payload"]["schema_version"] != envelope["schema_version"]:
            raise ValueError("schema_version: envelope and payload differ")
        bundle = decode_payload(envelope["payload"])
    except TypeError as error:
        raise ValueError(str(error)) from error
    if bundle.bundle_key != reference["bundle_key"]:
        raise ValueError("reference.bundle_key: does not match payload bundle_key")
    return bundle
