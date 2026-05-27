import asyncio

import pytest

from ls_modbus_mcp.points import PointConfigError, PointDefinition, PointMap
from ls_modbus_mcp.server import (
    list_points_tool,
    read_coils_tool,
    read_holding_registers_tool,
    read_point_tool,
    read_points_tool,
)


class FakeReader:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def read_area(self, area, address, count):
        self.calls.append((area, address, count))
        return self.responses[(area, address, count)]


def run(coro):
    return asyncio.run(coro)


def point_map():
    return PointMap(
        {
            "mesh_1_running": PointDefinition(
                name="mesh_1_running",
                area="coil",
                address=0,
                count=1,
                data_type="bool",
                description="Mesh conveyor 1 running state",
            ),
            "mesh_1_speed": PointDefinition(
                name="mesh_1_speed",
                area="holding_register",
                address=100,
                count=1,
                data_type="uint16",
                scale=0.1,
                unit="hz",
                description="Mesh conveyor 1 speed feedback",
            ),
        }
    )


def test_list_points_returns_public_point_metadata():
    assert list_points_tool(point_map()) == [
        {
            "name": "mesh_1_running",
            "area": "coil",
            "address": 0,
            "count": 1,
            "data_type": "bool",
            "scale": None,
            "unit": None,
            "description": "Mesh conveyor 1 running state",
        },
        {
            "name": "mesh_1_speed",
            "area": "holding_register",
            "address": 100,
            "count": 1,
            "data_type": "uint16",
            "scale": 0.1,
            "unit": "hz",
            "description": "Mesh conveyor 1 speed feedback",
        },
    ]


def test_read_point_reads_raw_values_and_decodes_named_point():
    reader = FakeReader({("holding_register", 100, 1): [123]})

    result = run(read_point_tool(point_map(), reader, "mesh_1_speed"))

    assert result == {
        "name": "mesh_1_speed",
        "value": 12.3,
        "raw": [123],
        "area": "holding_register",
        "address": 100,
        "count": 1,
        "data_type": "uint16",
        "scale": 0.1,
        "unit": "hz",
        "description": "Mesh conveyor 1 speed feedback",
    }
    assert reader.calls == [("holding_register", 100, 1)]


def test_read_points_reads_multiple_named_points():
    reader = FakeReader(
        {
            ("coil", 0, 1): [True],
            ("holding_register", 100, 1): [123],
        }
    )

    result = run(read_points_tool(point_map(), reader, ["mesh_1_running", "mesh_1_speed"]))

    assert [item["name"] for item in result] == ["mesh_1_running", "mesh_1_speed"]
    assert [item["value"] for item in result] == [True, 12.3]
    assert reader.calls == [("coil", 0, 1), ("holding_register", 100, 1)]


def test_read_point_rejects_unknown_point():
    reader = FakeReader({})

    with pytest.raises(PointConfigError, match="Unknown point"):
        run(read_point_tool(point_map(), reader, "unknown"))


def test_read_coils_tool_returns_raw_area_values():
    reader = FakeReader({("coil", 10, 2): [True, False]})

    assert run(read_coils_tool(reader, address=10, count=2)) == {
        "area": "coil",
        "address": 10,
        "count": 2,
        "values": [True, False],
    }


def test_read_holding_registers_tool_rejects_invalid_count():
    reader = FakeReader({})

    with pytest.raises(ValueError, match="count"):
        run(read_holding_registers_tool(reader, address=0, count=0))
