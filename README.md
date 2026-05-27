# XG5000 MCP

Read-only MCP server for LS XG5000 PLC data over Modbus TCP.

## Phase 1 Scope

This project starts with read-only access to PLC values exposed through Modbus TCP. It is intended for status monitoring, diagnostics, and named point lookup from MCP clients.

Write/control tools are intentionally excluded from the first phase. Future control support should write only to PLC-side command/request registers or coils, and the PLC ladder program must enforce equipment interlocks and safety conditions.

## Target Setup

- PLC: LS XBC-DR64H
- Ethernet module: XBL-EMTA
- Protocol: Modbus TCP
- Default port: `502`

## Development

```powershell
python -m pytest -v
```

