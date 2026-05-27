from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from ls_modbus_mcp.points import SUPPORTED_AREAS


class ModbusConnectionError(ConnectionError):
    """Raised when the Modbus TCP client cannot connect."""


class ModbusReadError(RuntimeError):
    """Raised when a Modbus read fails."""


@dataclass(frozen=True)
class ModbusSettings:
    host: str
    port: int = 502
    unit_id: int = 1
    timeout: float = 3.0


class AsyncModbusReader:
    def __init__(self, settings: ModbusSettings, client: Any | None = None) -> None:
        self.settings = settings
        self._client = client
        self._connected = False

    async def connect(self) -> None:
        if self._connected:
            return

        if self._client is None:
            self._client = self._create_pymodbus_client()

        connected = await self._client.connect()
        if not connected:
            raise ModbusConnectionError(
                f"Failed to connect to Modbus TCP server "
                f"{self.settings.host}:{self.settings.port}"
            )
        self._connected = True

    async def close(self) -> None:
        if self._client is None:
            return

        result = self._client.close()
        if inspect.isawaitable(result):
            await result
        self._connected = False

    async def read_area(self, area: str, address: int, count: int) -> list[bool] | list[int]:
        if area not in SUPPORTED_AREAS:
            raise ValueError(f"unsupported Modbus area: {area}")
        if address < 0:
            raise ValueError("address must be greater than or equal to 0")
        if count < 1:
            raise ValueError("count must be greater than or equal to 1")

        await self.connect()

        method_name = {
            "coil": "read_coils",
            "discrete_input": "read_discrete_inputs",
            "holding_register": "read_holding_registers",
            "input_register": "read_input_registers",
        }[area]
        method = getattr(self._client, method_name)
        response = await method(
            address=address,
            count=count,
            slave=self.settings.unit_id,
        )

        if response.isError():
            raise ModbusReadError(
                f"Modbus read failed: area={area}, address={address}, count={count}"
            )

        if area in {"coil", "discrete_input"}:
            return list(response.bits[:count])
        return list(response.registers[:count])

    async def read_coils(self, address: int, count: int) -> list[bool]:
        values = await self.read_area("coil", address, count)
        return [bool(value) for value in values]

    async def read_discrete_inputs(self, address: int, count: int) -> list[bool]:
        values = await self.read_area("discrete_input", address, count)
        return [bool(value) for value in values]

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        values = await self.read_area("holding_register", address, count)
        return [int(value) for value in values]

    async def read_input_registers(self, address: int, count: int) -> list[int]:
        values = await self.read_area("input_register", address, count)
        return [int(value) for value in values]

    def _create_pymodbus_client(self) -> Any:
        from pymodbus.client import AsyncModbusTcpClient

        return AsyncModbusTcpClient(
            self.settings.host,
            port=self.settings.port,
            timeout=self.settings.timeout,
        )
