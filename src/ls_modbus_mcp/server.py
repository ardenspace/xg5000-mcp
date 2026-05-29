from __future__ import annotations

import os
from typing import Any

from ls_modbus_mcp.modbus_client import AsyncModbusReader, ModbusSettings
from ls_modbus_mcp.points import PointDefinition, PointMap, decode_point_value, load_point_map


def list_points_tool(point_map: PointMap) -> list[dict[str, Any]]:
    return [
        _point_metadata(point_map.get(name))
        for name in point_map.names()
    ]


async def read_point_tool(
    point_map: PointMap,
    reader: AsyncModbusReader,
    name: str,
) -> dict[str, Any]:
    point = point_map.get(name)
    raw = await reader.read_area(point.area, point.address, point.count)
    return _point_read_result(point, raw)


async def read_points_tool(
    point_map: PointMap,
    reader: AsyncModbusReader,
    names: list[str],
) -> list[dict[str, Any]]:
    return [
        await read_point_tool(point_map, reader, name)
        for name in names
    ]


async def read_coils_tool(
    reader: AsyncModbusReader,
    *,
    address: int,
    count: int,
) -> dict[str, Any]:
    return await _read_raw_area_tool(reader, "coil", address, count)


async def read_discrete_inputs_tool(
    reader: AsyncModbusReader,
    *,
    address: int,
    count: int,
) -> dict[str, Any]:
    return await _read_raw_area_tool(reader, "discrete_input", address, count)


async def read_holding_registers_tool(
    reader: AsyncModbusReader,
    *,
    address: int,
    count: int,
) -> dict[str, Any]:
    return await _read_raw_area_tool(reader, "holding_register", address, count)


async def read_input_registers_tool(
    reader: AsyncModbusReader,
    *,
    address: int,
    count: int,
) -> dict[str, Any]:
    return await _read_raw_area_tool(reader, "input_register", address, count)


def create_app(point_map: PointMap, reader: AsyncModbusReader):
    from mcp.server.fastmcp import FastMCP

    app = FastMCP("xg5000-mcp")

    @app.tool()
    def list_points() -> list[dict[str, Any]]:
        return list_points_tool(point_map)

    @app.tool()
    async def read_point(name: str) -> dict[str, Any]:
        return await read_point_tool(point_map, reader, name)

    @app.tool()
    async def read_points(names: list[str]) -> list[dict[str, Any]]:
        return await read_points_tool(point_map, reader, names)

    @app.tool()
    async def read_coils(address: int, count: int) -> dict[str, Any]:
        return await read_coils_tool(reader, address=address, count=count)

    @app.tool()
    async def read_discrete_inputs(address: int, count: int) -> dict[str, Any]:
        return await read_discrete_inputs_tool(reader, address=address, count=count)

    @app.tool()
    async def read_holding_registers(address: int, count: int) -> dict[str, Any]:
        return await read_holding_registers_tool(reader, address=address, count=count)

    @app.tool()
    async def read_input_registers(address: int, count: int) -> dict[str, Any]:
        return await read_input_registers_tool(reader, address=address, count=count)

    return app


def main() -> None:
    point_map = load_point_map(os.environ.get("POINTS_FILE", "config/points.yaml"))
    reader = AsyncModbusReader(load_modbus_settings_from_env())
    create_app(point_map, reader).run()


def load_modbus_settings_from_env() -> ModbusSettings:
    host = os.environ.get("PLC_HOST")
    if not host:
        raise ValueError("PLC_HOST environment variable is required")

    return ModbusSettings(
        host=host,
        port=int(os.environ.get("PLC_PORT", "502")),
        unit_id=int(os.environ.get("PLC_UNIT_ID", "1")),
        timeout=float(os.environ.get("PLC_TIMEOUT", "3.0")),
    )


async def _read_raw_area_tool(
    reader: AsyncModbusReader,
    area: str,
    address: int,
    count: int,
) -> dict[str, Any]:
    if address < 0:
        raise ValueError("address must be greater than or equal to 0")
    if count < 1:
        raise ValueError("count must be greater than or equal to 1")

    values = await reader.read_area(area, address, count)
    return {
        "area": area,
        "address": address,
        "count": count,
        "values": values,
    }


def _point_metadata(point: PointDefinition) -> dict[str, Any]:
    return {
        "name": point.name,
        "area": point.area,
        "address": point.address,
        "count": point.count,
        "data_type": point.data_type,
        "scale": point.scale,
        "unit": point.unit,
        "description": point.description,
        "word_order": point.word_order,
        "byte_order": point.byte_order,
    }


def _point_read_result(
    point: PointDefinition,
    raw: list[int] | list[bool],
) -> dict[str, Any]:
    return {
        **_point_metadata(point),
        "value": decode_point_value(point, raw),
        "raw": raw,
    }
