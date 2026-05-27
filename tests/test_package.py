from ls_modbus_mcp import __version__


def test_package_exposes_version():
    assert isinstance(__version__, str)
    assert __version__
