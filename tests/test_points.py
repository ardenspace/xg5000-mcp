from pathlib import Path

import pytest

from ls_modbus_mcp.points import (
    PointConfigError,
    PointDecodeError,
    PointDefinition,
    decode_point_value,
    load_point_map,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_point_map_lists_named_points():
    point_map = load_point_map(FIXTURES / "points_valid.yaml")

    assert point_map.names() == ["mesh_1_running", "mesh_1_speed"]
    assert point_map.get("mesh_1_speed").area == "holding_register"
    assert point_map.get("mesh_1_speed").address == 100
    assert point_map.get("mesh_1_speed").scale == 0.1


def test_load_point_map_rejects_invalid_area():
    with pytest.raises(PointConfigError, match="bad_point.*area"):
        load_point_map(FIXTURES / "points_invalid_area.yaml")


def test_load_point_map_rejects_invalid_count():
    with pytest.raises(PointConfigError, match="bad_point.*count"):
        load_point_map(FIXTURES / "points_invalid_count.yaml")


def test_load_point_map_rejects_bool_for_integer_fields():
    with pytest.raises(PointConfigError, match="bad_point.*address"):
        load_point_map(FIXTURES / "points_bool_integer.yaml")


def point(data_type, *, count=1, scale=None):
    return PointDefinition(
        name="test_point",
        area="holding_register",
        address=0,
        count=count,
        data_type=data_type,
        scale=scale,
    )


def test_decode_bool_from_coil_value():
    assert decode_point_value(point("bool"), [True]) is True


def test_decode_uint16_register():
    assert decode_point_value(point("uint16"), [123]) == 123


def test_decode_int16_register_twos_complement():
    assert decode_point_value(point("int16"), [0xFFFE]) == -2


def test_decode_scaled_register_value():
    assert decode_point_value(point("uint16", scale=0.1), [123]) == 12.3


def test_decode_uint32_register_pair():
    assert decode_point_value(point("uint32", count=2), [0x0001, 0x0002]) == 65538


def test_decode_int32_register_pair_twos_complement():
    assert decode_point_value(point("int32", count=2), [0xFFFF, 0xFFFE]) == -2


def test_decode_float32_register_pair():
    assert decode_point_value(point("float32", count=2), [0x4120, 0x0000]) == 10.0


def test_decode_float32_register_pair_with_little_word_order():
    little_word_point = PointDefinition(
        name="test_point",
        area="holding_register",
        address=0,
        count=2,
        data_type="float32",
        word_order="little",
    )

    assert decode_point_value(little_word_point, [0x0000, 0x4120]) == 10.0


def test_decode_float32_register_pair_with_little_byte_order():
    little_byte_point = PointDefinition(
        name="test_point",
        area="holding_register",
        address=0,
        count=2,
        data_type="float32",
        byte_order="little",
    )

    assert decode_point_value(little_byte_point, [0x2041, 0x0000]) == 10.0


def test_decode_rejects_wrong_raw_count():
    with pytest.raises(PointDecodeError, match="test_point.*expected 2.*got 1"):
        decode_point_value(point("uint32", count=2), [1])
