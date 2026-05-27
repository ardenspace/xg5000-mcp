import asyncio

import pytest

from ls_modbus_mcp.modbus_client import (
    AsyncModbusReader,
    ModbusConnectionError,
    ModbusReadError,
    ModbusSettings,
)


class FakeResponse:
    def __init__(self, *, bits=None, registers=None, error=False):
        self.bits = bits or []
        self.registers = registers or []
        self._error = error

    def isError(self):
        return self._error


class FakeClient:
    def __init__(self, *, connect_result=True, response=None):
        self.connect_result = connect_result
        self.response = response or FakeResponse()
        self.calls = []
        self.closed = False

    async def connect(self):
        return self.connect_result

    def close(self):
        self.closed = True

    async def read_coils(self, *, address, count, slave):
        self.calls.append(("read_coils", address, count, slave))
        return self.response

    async def read_discrete_inputs(self, *, address, count, slave):
        self.calls.append(("read_discrete_inputs", address, count, slave))
        return self.response

    async def read_holding_registers(self, *, address, count, slave):
        self.calls.append(("read_holding_registers", address, count, slave))
        return self.response

    async def read_input_registers(self, *, address, count, slave):
        self.calls.append(("read_input_registers", address, count, slave))
        return self.response


def run(coro):
    return asyncio.run(coro)


def test_read_coils_returns_bits():
    client = FakeClient(response=FakeResponse(bits=[True, False]))
    reader = AsyncModbusReader(ModbusSettings(host="192.168.0.10", unit_id=7), client=client)

    assert run(reader.read_area("coil", address=10, count=2)) == [True, False]
    assert client.calls == [("read_coils", 10, 2, 7)]


def test_read_discrete_inputs_returns_bits():
    client = FakeClient(response=FakeResponse(bits=[False, True]))
    reader = AsyncModbusReader(ModbusSettings(host="192.168.0.10"), client=client)

    assert run(reader.read_area("discrete_input", address=20, count=2)) == [False, True]
    assert client.calls == [("read_discrete_inputs", 20, 2, 1)]


def test_read_holding_registers_returns_registers():
    client = FakeClient(response=FakeResponse(registers=[100, 200]))
    reader = AsyncModbusReader(ModbusSettings(host="192.168.0.10"), client=client)

    assert run(reader.read_area("holding_register", address=100, count=2)) == [100, 200]
    assert client.calls == [("read_holding_registers", 100, 2, 1)]


def test_read_input_registers_returns_registers():
    client = FakeClient(response=FakeResponse(registers=[300, 400]))
    reader = AsyncModbusReader(ModbusSettings(host="192.168.0.10"), client=client)

    assert run(reader.read_area("input_register", address=110, count=2)) == [300, 400]
    assert client.calls == [("read_input_registers", 110, 2, 1)]


def test_read_area_rejects_unknown_area():
    reader = AsyncModbusReader(ModbusSettings(host="192.168.0.10"), client=FakeClient())

    with pytest.raises(ValueError, match="unsupported Modbus area"):
        run(reader.read_area("output", address=0, count=1))


def test_read_area_raises_connection_error_when_connect_fails():
    reader = AsyncModbusReader(
        ModbusSettings(host="192.168.0.10"),
        client=FakeClient(connect_result=False),
    )

    with pytest.raises(ModbusConnectionError, match="192.168.0.10"):
        run(reader.read_area("coil", address=0, count=1))


def test_read_area_raises_read_error_for_modbus_exception_response():
    reader = AsyncModbusReader(
        ModbusSettings(host="192.168.0.10"),
        client=FakeClient(response=FakeResponse(error=True)),
    )

    with pytest.raises(ModbusReadError, match="coil.*0.*1"):
        run(reader.read_area("coil", address=0, count=1))
