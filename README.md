# XG5000 MCP

Read-only MCP server for LS XG5000 PLC data over Modbus TCP.

This project is for an LS XG5000-based control cabinet using an XBC-DR64H PLC and XBL-EMTA Ethernet module. Phase 1 exposes PLC values to MCP clients for monitoring and diagnostics.

## Phase 1 Scope

This project starts with read-only access to PLC values exposed through Modbus TCP. It is intended for status monitoring, diagnostics, and named point lookup from MCP clients.

Write/control tools are intentionally excluded from the first phase. Future control support should write only to PLC-side command/request registers or coils, and the PLC ladder program must enforce equipment interlocks and safety conditions.

## Target Setup

- PLC: LS XBC-DR64H
- Ethernet module: XBL-EMTA
- Protocol: Modbus TCP
- Default port: `502`

## Install

```powershell
python -m pip install -e ".[dev]"
```

## Configuration

Runtime configuration is provided through environment variables:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `PLC_HOST` | yes | none | PLC or XBL-EMTA IP address |
| `PLC_PORT` | no | `502` | Modbus TCP port |
| `PLC_UNIT_ID` | no | `1` | Modbus unit/slave id |
| `PLC_TIMEOUT` | no | `3.0` | Connection timeout in seconds |
| `POINTS_FILE` | no | `config/points.yaml` | Named point mapping file |

Copy `config/points.example.yaml` to `config/points.yaml`, then replace addresses with the actual PLC Modbus map.

```powershell
Copy-Item config\points.example.yaml config\points.yaml
$env:PLC_HOST = "192.168.0.10"
$env:PLC_PORT = "502"
$env:PLC_UNIT_ID = "1"
$env:POINTS_FILE = "config\points.yaml"
xg5000-mcp
```

## MCP Client Example

```json
{
  "mcpServers": {
    "xg5000-mcp": {
      "command": "xg5000-mcp",
      "env": {
        "PLC_HOST": "192.168.0.10",
        "PLC_PORT": "502",
        "PLC_UNIT_ID": "1",
        "POINTS_FILE": "D:\\xg5000-mcp\\config\\points.yaml"
      }
    }
  }
}
```

## Tools

- `list_points`
- `read_point`
- `read_points`
- `read_coils`
- `read_discrete_inputs`
- `read_holding_registers`
- `read_input_registers`

## Control Roadmap

Conveyor and cylinder control should be added later as a separate guarded command layer. The MCP server should write only to PLC-side command/request addresses, never directly to physical output coils. PLC ladder logic must keep responsibility for emergency stop handling, sensor checks, inverter faults, cylinder interlocks, manual/auto mode, and final output decisions.

## Development

```powershell
python -m pytest -v
python -m ruff check .
```

