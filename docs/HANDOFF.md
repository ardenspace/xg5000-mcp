# XG5000 MCP Handoff

## Current Status

The repository contains Phase 1 of the XG5000 MCP project on branch `ls-modbus-mcp`.

Phase 1 is read-only:

- Connects to LS PLC through Modbus TCP.
- Reads coils, discrete inputs, holding registers, and input registers.
- Exposes named points through MCP tools.
- Does not write to PLC memory.
- Does not control conveyors, cylinders, inverters, or outputs yet.

Implemented tools:

- `list_points`
- `read_point`
- `read_points`
- `read_coils`
- `read_discrete_inputs`
- `read_holding_registers`
- `read_input_registers`

Verification already run:

```powershell
python -m pytest -v
python -m ruff check .
```

Latest result:

- `27 passed`
- `All checks passed`

## Target Equipment

Known cabinet/equipment information:

- PLC controller: `XBC-DR64H`
- Ethernet module: `XBL-EMTA`
- Input module: `XBE-DC32A`
- Output module: `XBE-TN16A`
- Field protocol for MCP: Modbus TCP over Ethernet
- Main controlled equipment:
  - Mesh conveyors
  - Top-chain conveyors
  - Box conveyors
  - Solenoid cylinders
  - Cooling fans
  - Inverters

## Offline Status

The latest available project is:

```text
D:\Taesung\TaesungProject2
```

This is enough for offline review, but the raw `.xgwx` file does not provide a reliable plain-text Modbus address map. The next practical work is blocked until someone opens the project in XG5000 and exports or records the communication settings, symbols/device comments, I/O list, and Modbus mapping.

A physical PLC or field machine is not required for that export step. A live PLC is only required later for the Modbus TCP smoke test.
## What To Collect From Site

Ask the company/site for these files and values before PLC testing:

1. Latest XG5000 project backup
   - Prefer an upload from the running PLC, not an old engineering copy.
   - Keep an untouched backup copy.

2. PLC network information
   - PLC/XBL-EMTA IP address
   - Subnet mask
   - Gateway, if used
   - PC IP address used for testing
   - Whether the PC can ping the PLC

3. XBL-EMTA communication settings
   - Modbus TCP service enabled or not
   - TCP port, usually `502`
   - Unit/slave ID, often `1`
   - Host enable table or communication protection settings
   - Whether the test PC IP must be allowed

4. PLC address map
   - Input addresses for sensors
   - Output addresses for solenoids/contactors
   - Internal relay addresses used for status
   - Data register addresses used for inverter status/speed/faults
   - Any existing Modbus mapping table

5. I/O and device documents
   - Electrical drawings
   - I/O list
   - Device comment list
   - Symbol/variable export from XG5000, if available
   - Inverter RS485 address/status map, if PLC stores those values in registers

## What To Check In XG5000

Open the latest XG5000 project and confirm:

1. PLC and module configuration
   - CPU is `XBC-DR64H`.
   - Ethernet module is `XBL-EMTA`.
   - I/O expansion order matches the real cabinet.

2. XBL-EMTA settings
   - IP address.
   - Modbus TCP service.
   - Port.
   - Host access restrictions.

3. Device comments and symbols
   - Find names for photo sensors, cylinder sensors, inverter status, conveyor status.
   - Export comments/symbols if XG5000 supports it.

4. Ladder logic status points
   - Identify stable status bits/registers that are safe to read.
   - Prefer internal monitoring addresses over raw physical outputs.

5. Existing Modbus mapping
   - Confirm how LS/XG5000 devices map to Modbus areas.
   - Confirm whether the address shown as `40001` should be entered as offset `0` in the MCP config.

## First Points To Map

Start with read-only status points. Do not start with control/output points.

Recommended first targets:

- PLC heartbeat or always-changing scan/status register
- Emergency stop status, if already exposed as a safe status bit
- Auto/manual mode status
- Inverter running status
- Inverter fault status
- Conveyor running feedback
- Photo sensor detection bits
- Cylinder open/close sensor bits
- Box presence sensor bits

Avoid in the first test:

- Physical output coils
- Solenoid output commands
- Contactor outputs
- Inverter run commands
- Speed command registers
- Any writeable control address

## MCP Config File

Create a real config from the example:

```powershell
cd D:\xg5000-mcp
Copy-Item config\points.example.yaml config\points.yaml
notepad config\points.yaml
```

Example:

```yaml
points:
  mesh_1_running:
    area: coil
    address: 0
    count: 1
    data_type: bool
    description: Mesh conveyor 1 running status

  mesh_1_speed_feedback:
    area: holding_register
    address: 100
    count: 1
    data_type: uint16
    scale: 0.1
    unit: hz
    description: Mesh conveyor 1 inverter speed feedback

  inverter_1_frequency_raw:
    area: holding_register
    address: 120
    count: 2
    data_type: float32
    word_order: big
    byte_order: big
    unit: hz
    description: Example 32-bit value; confirm word and byte order on site
```

Supported areas:

- `coil`
- `discrete_input`
- `holding_register`
- `input_register`

Supported data types:

- `bool`
- `uint16`
- `int16`
- `uint32`
- `int32`
- `float32`

Optional 32-bit decode order fields:

- `word_order`: `big` or `little`, default `big`
- `byte_order`: `big` or `little`, default `big`

Address note:

- Modbus documentation often shows addresses like `00001`, `10001`, `30001`, `40001`.
- The MCP config uses zero-based offsets.
- Example: `40001` usually becomes `address: 0`; `40002` becomes `address: 1`.
- Confirm this with the actual LS/XBL-EMTA mapping before trusting values.

## Local Setup

Run once:

```powershell
cd D:\xg5000-mcp
git switch ls-modbus-mcp
python -m pip install -e ".[dev]"
```

Run verification:

```powershell
python -m pytest -v
python -m ruff check .
```

## PLC Connectivity Test

Set environment variables:

```powershell
$env:PLC_HOST="192.168.0.10"
$env:PLC_PORT="502"
$env:PLC_UNIT_ID="1"
$env:POINTS_FILE="config\points.yaml"
```

Replace `192.168.0.10` with the real PLC/XBL-EMTA IP.

Network checks:

```powershell
ping $env:PLC_HOST
Test-NetConnection $env:PLC_HOST -Port 502
```

Expected:

- `ping` succeeds, if ICMP is allowed.
- `Test-NetConnection` shows `TcpTestSucceeded: True`.

If port `502` is blocked:

- Check XBL-EMTA Modbus TCP service.
- Check the module IP.
- Check host enable/access control settings.
- Check firewall or network segmentation.

## Running The MCP Server

Start:

```powershell
xg5000-mcp
```

The server runs over MCP stdio, so it is usually launched by an MCP client rather than used as a normal web server.

MCP client example:

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

First MCP tool calls:

1. `list_points`
2. `read_point` for one known-safe point
3. `read_points` for a small group
4. Raw read only if needed:
   - `read_coils`
   - `read_discrete_inputs`
   - `read_holding_registers`
   - `read_input_registers`

## Acceptance Checklist For Phase 1

Phase 1 is usable when:

- PC can reach PLC IP.
- TCP port `502` is open.
- `config\points.yaml` contains at least 5 verified real status points.
- `list_points` returns the configured points.
- `read_point` returns the expected value for a known sensor/status.
- Toggling a safe sensor changes the MCP read value.
- No write/control tool is exposed.
- The address mapping is documented with source references from XG5000 or electrical drawings.

## Safety Rules

Do not add write/control tools until Phase 1 reads are verified.

When control is added later:

- Do not write directly to physical output coils.
- Do not let MCP/AI bypass PLC ladder logic.
- Create PLC-side command/request bits or registers.
- PLC must check all interlocks before acting.
- PLC must remain responsible for:
  - Emergency stop
  - Manual/auto mode
  - Sensor conditions
  - Inverter faults
  - Cylinder position checks
  - Robot/conveyor clearance
  - Final output decisions
- Add `ENABLE_WRITES=true` gating.
- Add command allowlist.
- Add dry-run mode.
- Add value range checks.
- Add append-only command audit logs.

## Likely Phase 2

After Phase 1 works against the real PLC:

1. Create `config/commands.example.yaml`.
2. Add dry-run command tools only.
3. Add tests proving commands do not write unless explicitly enabled.
4. Add PLC-side command/request bits.
5. Test with a non-dangerous simulated or maintenance-only command.

Possible future command names:

- `start_conveyor`
- `stop_conveyor`
- `set_conveyor_speed`
- `open_cylinder`
- `close_cylinder`

These should map to PLC command/request addresses, not raw output addresses.
