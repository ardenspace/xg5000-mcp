# LS Modbus MCP Design

## Goal

Build an MCP server for an LS XG5000-based control cabinet that reads PLC data over Modbus TCP first, then can be extended to controlled writes after the PLC-side safety logic is ready.

## Target Hardware

- PLC controller: LS XBC-DR64H
- Ethernet module: XBL-EMTA
- Expansion inputs: XBE-DC32A
- Expansion outputs: XBE-TN16A
- Controlled equipment: mesh conveyors, top-chain conveyors, box conveyors, solenoid cylinders, cooling fans, and inverters
- Field protocol for this project: Modbus TCP over Ethernet

## Design Principles

The first version is read-only. It should prove that the PC can connect to the PLC, read Modbus addresses, and expose those values as named MCP tools.

Future control support must not write arbitrary physical output addresses directly. The MCP server should write only to PLC-defined command/request registers or coils, and the PLC ladder program must decide whether the command is allowed. Emergency stop, interlocks, inverter faults, cylinder position checks, robot clearance, and manual/auto mode must stay inside PLC logic.

## Phase 1 Scope

Phase 1 provides a Python MCP server with Modbus TCP read tools:

- `list_points`
- `read_point`
- `read_points`
- `read_coils`
- `read_discrete_inputs`
- `read_holding_registers`
- `read_input_registers`

The server loads named points from `config/points.yaml`. A point maps a human-readable equipment name to a Modbus area, address, count, data type, and optional scale.

Example points:

```yaml
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
    description: Mesh conveyor 1 inverter speed feedback
```

## Future Control Scope

Control is a later phase. The codebase should reserve a separate command mapping file, such as `config/commands.yaml`, but Phase 1 should not expose write tools.

Future write tools should be gated by:

- `ENABLE_WRITES=true`
- command allowlist
- value range checks
- command-specific descriptions
- dry-run mode
- append-only audit log

Future command examples:

- `start_conveyor`
- `stop_conveyor`
- `set_conveyor_speed`
- `open_cylinder`
- `close_cylinder`

These commands should write to PLC command/request addresses, not directly to output coils.

## Architecture

The project uses Python so Modbus TCP can be handled with `pymodbus` and MCP can be exposed through the Python MCP SDK.

Modules:

- `ls_modbus_mcp.config`: environment and YAML configuration loading
- `ls_modbus_mcp.points`: point schema validation and decoding
- `ls_modbus_mcp.modbus_client`: Modbus TCP read operations
- `ls_modbus_mcp.server`: MCP tool registration

The server should keep protocol details out of MCP tool handlers. Tool handlers should call point/config services, and those services should call the Modbus client.

## Error Handling

The server should return clear errors for:

- unknown point names
- invalid Modbus area names
- connection failures
- read timeouts
- invalid address/count values
- unsupported data types

Errors must include enough context to diagnose PLC IP, area, address, count, and point name without exposing secrets.

## Testing

Tests should not require a physical PLC. Unit tests cover:

- point YAML loading and validation
- point value decoding
- Modbus client behavior with a fake client
- MCP tool handlers for list/read flows
- failure cases for unknown points and invalid config

Manual PLC testing is a separate step once the real PLC IP, unit id, and Modbus address map are known.
