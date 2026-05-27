from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_AREAS = {"coil", "discrete_input", "holding_register", "input_register"}
SUPPORTED_DATA_TYPES = {"bool", "uint16", "int16", "uint32", "int32", "float32"}


class PointConfigError(ValueError):
    """Raised when a point configuration file is invalid."""


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
    if scale is not None and not isinstance(scale, int | float):
        raise PointConfigError(f"{name}: scale must be a number")

    unit = value.get("unit")
    if unit is not None and not isinstance(unit, str):
        raise PointConfigError(f"{name}: unit must be a string")

    description = value.get("description")
    if description is not None and not isinstance(description, str):
        raise PointConfigError(f"{name}: description must be a string")

    return PointDefinition(
        name=name,
        area=area,
        address=address,
        count=count,
        data_type=data_type,
        scale=float(scale) if scale is not None else None,
        unit=unit,
        description=description,
    )


def _require_str(name: str, value: dict[str, Any], field: str) -> str:
    field_value = value.get(field)
    if not isinstance(field_value, str):
        raise PointConfigError(f"{name}: {field} must be a string")
    return field_value


def _require_int(name: str, value: dict[str, Any], field: str) -> int:
    field_value = value.get(field)
    if not isinstance(field_value, int):
        raise PointConfigError(f"{name}: {field} must be an integer")
    return field_value
