import pytest

from ls_modbus_mcp.points import PointConfigError, load_point_map


def write_points(tmp_path, text):
    path = tmp_path / "points.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_point_map_lists_named_points(tmp_path):
    path = write_points(
        tmp_path,
        """
points:
  mesh_1_running:
    area: coil
    address: 0
    count: 1
    data_type: bool
    description: Mesh conveyor 1 running state
  mesh_1_speed:
    area: holding_register
    address: 100
    count: 1
    data_type: uint16
    scale: 0.1
    unit: hz
""",
    )

    point_map = load_point_map(path)

    assert point_map.names() == ["mesh_1_running", "mesh_1_speed"]
    assert point_map.get("mesh_1_speed").area == "holding_register"
    assert point_map.get("mesh_1_speed").address == 100
    assert point_map.get("mesh_1_speed").scale == 0.1


def test_load_point_map_rejects_invalid_area(tmp_path):
    path = write_points(
        tmp_path,
        """
points:
  bad_point:
    area: output
    address: 0
    count: 1
    data_type: bool
""",
    )

    with pytest.raises(PointConfigError, match="bad_point.*area"):
        load_point_map(path)


def test_load_point_map_rejects_invalid_count(tmp_path):
    path = write_points(
        tmp_path,
        """
points:
  bad_point:
    area: holding_register
    address: 0
    count: 0
    data_type: uint16
""",
    )

    with pytest.raises(PointConfigError, match="bad_point.*count"):
        load_point_map(path)
