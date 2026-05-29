from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Any

import yaml

SUPPORTED_AREAS = {"coil", "discrete_input", "holding_register", "input_register"}
SUPPORTED_DATA_TYPES = {"bool", "uint16", "int16", "uint32", "int32", "float32"}
SUPPORTED_ORDERS = {"big", "little"}


class PointConfigError(ValueError):
    """Raised when a point configuration file is invalid."""


class PointDecodeError(ValueError):
    """Raised when raw Modbus values cannot be decoded for a point."""


@dataclass(frozen=True)
class PointDefinition:
    name: str
    area: str
    address: int
    count: int
    data_type: str
    scale: float | None = None
    unit: str | None = None
    description: str | None = None
    word_order: str = "big"
    byte_order: str = "big"


class PointMap:
    def __init__(self, points: dict[str, PointDefinition]) -> None:
        self._points = dict(points)

    def names(self) -> list[str]:
        return list(self._points)

    def get(self, name: str) -> PointDefinition:
        try:
            return self._points[name]
        except KeyError as exc:
            raise PointConfigError(f"Unknown point: {name}") from exc


def load_point_map(path: str | Path) -> PointMap:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    raw_points = raw.get("points")
    if not isinstance(raw_points, dict):
        raise PointConfigError("points must be a mapping")

    points = {
        name: _parse_point(name, value)
        for name, value in raw_points.items()
    }
    return PointMap(points)


def _parse_point(name: str, value: Any) -> PointDefinition:
    if not isinstance(value, dict):
        raise PointConfigError(f"{name}: point definition must be a mapping")

    area = _require_str(name, value, "area")
    if area not in SUPPORTED_AREAS:
        raise PointConfigError(f"{name}: area must be one of {sorted(SUPPORTED_AREAS)}")

    data_type = _require_str(name, value, "data_type")
    if data_type not in SUPPORTED_DATA_TYPES:
        raise PointConfigError(
            f"{name}: data_type must be one of {sorted(SUPPORTED_DATA_TYPES)}"
        )

    address = _require_int(name, value, "address")
    if address < 0:
        raise PointConfigError(f"{name}: address must be greater than or equal to 0")

    count = _require_int(name, value, "count")
    if count < 1:
        raise PointConfigError(f"{name}: count must be greater than or equal to 1")

    scale = value.get("scale")
    if scale is not None and (isinstance(scale, bool) or not isinstance(scale, int | float)):
        raise PointConfigError(f"{name}: scale must be a number")

    unit = value.get("unit")
    if unit is not None and not isinstance(unit, str):
        raise PointConfigError(f"{name}: unit must be a string")

    description = value.get("description")
    if description is not None and not isinstance(description, str):
        raise PointConfigError(f"{name}: description must be a string")

    word_order = _optional_order(name, value, "word_order")
    byte_order = _optional_order(name, value, "byte_order")

    return PointDefinition(
        name=name,
        area=area,
        address=address,
        count=count,
        data_type=data_type,
        scale=float(scale) if scale is not None else None,
        unit=unit,
        description=description,
        word_order=word_order,
        byte_order=byte_order,
    )


def _require_str(name: str, value: dict[str, Any], field: str) -> str:
    field_value = value.get(field)
    if not isinstance(field_value, str):
        raise PointConfigError(f"{name}: {field} must be a string")
    return field_value


def _require_int(name: str, value: dict[str, Any], field: str) -> int:
    field_value = value.get(field)
    if isinstance(field_value, bool) or not isinstance(field_value, int):
        raise PointConfigError(f"{name}: {field} must be an integer")
    return field_value


def _optional_order(name: str, value: dict[str, Any], field: str) -> str:
    field_value = value.get(field, "big")
    if not isinstance(field_value, str):
        raise PointConfigError(f"{name}: {field} must be a string")
    if field_value not in SUPPORTED_ORDERS:
        raise PointConfigError(f"{name}: {field} must be one of {sorted(SUPPORTED_ORDERS)}")
    return field_value


def decode_point_value(point: PointDefinition, raw: list[int] | list[bool]) -> object:
    if len(raw) != point.count:
        raise PointDecodeError(
            f"{point.name}: expected {point.count} raw values, got {len(raw)}"
        )

    match point.data_type:
        case "bool":
            value = _decode_bool(point, raw)
        case "uint16":
            value = _decode_uint16(point, raw)
        case "int16":
            value = _decode_int16(point, raw)
        case "uint32":
            value = _decode_uint32(point, raw)
        case "int32":
            value = _decode_int32(point, raw)
        case "float32":
            value = _decode_float32(point, raw)
        case _:
            raise PointDecodeError(f"{point.name}: unsupported data type {point.data_type}")

    if point.scale is not None and isinstance(value, int | float) and not isinstance(value, bool):
        return value * point.scale
    return value


def _decode_bool(point: PointDefinition, raw: list[int] | list[bool]) -> bool:
    _require_decode_count(point, 1)
    return bool(raw[0])


def _decode_uint16(point: PointDefinition, raw: list[int] | list[bool]) -> int:
    _require_decode_count(point, 1)
    return int(raw[0]) & 0xFFFF


def _decode_int16(point: PointDefinition, raw: list[int] | list[bool]) -> int:
    value = _decode_uint16(point, raw)
    return value - 0x10000 if value & 0x8000 else value


def _decode_uint32(point: PointDefinition, raw: list[int] | list[bool]) -> int:
    _require_decode_count(point, 2)
    return int.from_bytes(_register_bytes(point, raw), "big")


def _decode_int32(point: PointDefinition, raw: list[int] | list[bool]) -> int:
    value = _decode_uint32(point, raw)
    return value - 0x100000000 if value & 0x80000000 else value


def _decode_float32(point: PointDefinition, raw: list[int] | list[bool]) -> float:
    _require_decode_count(point, 2)
    return struct.unpack(">f", _register_bytes(point, raw))[0]


def _require_decode_count(point: PointDefinition, expected: int) -> None:
    if point.count != expected:
        raise PointDecodeError(
            f"{point.name}: {point.data_type} requires count {expected}, got {point.count}"
        )


def _register_bytes(point: PointDefinition, raw: list[int] | list[bool]) -> bytes:
    registers = [int(value) & 0xFFFF for value in raw]
    if point.word_order == "little":
        registers = list(reversed(registers))

    byte_order = ">" if point.byte_order == "big" else "<"
    return b"".join(struct.pack(f"{byte_order}H", register) for register in registers)
