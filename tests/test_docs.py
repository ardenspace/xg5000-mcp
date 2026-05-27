from pathlib import Path

from ls_modbus_mcp.points import load_point_map


def test_example_points_config_loads_at_least_one_point():
    point_map = load_point_map(Path("config") / "points.example.yaml")

    assert point_map.names()


def test_readme_documents_runtime_configuration_and_read_only_scope():
    readme = Path("README.md").read_text(encoding="utf-8")

    for required_text in [
        "PLC_HOST",
        "PLC_PORT",
        "PLC_UNIT_ID",
        "POINTS_FILE",
        "read-only",
        "command/request",
    ]:
        assert required_text in readme
