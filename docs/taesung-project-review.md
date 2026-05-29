# Taesung Project Review

## Source Files

Company project folder:

```text
D:\Taesung\TaesungProject2
```

Files observed:

```text
TaesungProject2.state
TaesungProject2.xgwx
TaesungProject2.xgwx_bkx0
TaesungProject2.xgwx_bkx1
TaesungProject2.xgwx_bkx2
```

## What Was Confirmed

`TaesungProject2.xgwx` is an XG5000 workspace/project binary, not a plain XML or ZIP file. It contains proprietary binary sections, so it should be opened in XG5000 for reliable project inspection.

`TaesungProject2.state` is BZip2-compressed state data. It can be partially decoded into XG5000 project state XML. This appears to describe editor/workspace state, not the full ladder project or a complete Modbus address map.

The state file includes these nodes:

```text
{PROJECT}\LSPLC
{PROJECT}\LSPLC\{DIRECT_VAR}
{PROJECT}\LSPLC\{PARAMETER}\{IO_PARAMETER}
{PROJECT}\LSPLC\{SCAN_TASK}\485통신
{PROJECT}\LSPLC\{SCAN_TASK}\MOTOR수동
{PROJECT}\LSPLC\{SCAN_TASK}\ProductAligning
```

Useful scan task names:

- `485통신`
- `MOTOR수동`
- `ProductAligning`

These names are consistent with the expected system:

- Inverter communication over RS485.
- Manual motor operation.
- Product alignment logic.

## What Was Not Confirmed Yet

The raw files did not provide a reliable plain-text Modbus map.

The following are still unknown:

- PLC/XBL-EMTA IP address.
- Whether Modbus TCP service is enabled.
- Unit/slave ID.
- Host allowlist/access protection settings.
- Exact Modbus mapping for X/M/D/R/etc. devices.
- Which internal bits/registers represent conveyor status.
- Which internal bits/registers represent cylinder open/close sensors.
- Which registers store inverter speed/fault/running status.

## Current Blocker

The latest project files are available at:

```text
D:\Taesung\TaesungProject2
```

That is enough to continue offline preparation, but not enough to create a reliable final `config\points.yaml` from raw file parsing alone.

The next implementation step is blocked until the XG5000 project is opened in XG5000 and the following data is exported or manually recorded:

- XBL-EMTA communication settings.
- Device comments / symbol list.
- I/O list.
- Modbus address mapping between LS devices and Modbus areas/offsets.
- A small first batch of confirmed safe read-only status points.

No physical field equipment is required for this export step. A live PLC is only required later for smoke testing real values.
## Required XG5000 Export/Inspection

Open `TaesungProject2.xgwx` in XG5000 and collect:

1. PLC/module configuration
   - Confirm CPU model.
   - Confirm XBL-EMTA module.
   - Confirm I/O module order.

2. XBL-EMTA communication parameters
   - IP address.
   - Modbus TCP service setting.
   - TCP port, usually `502`.
   - Unit/slave ID.
   - Host enable/access table.

3. Device comments / symbols
   - Export symbol table if possible.
   - Export device comments if possible.
   - Prioritize X, M, D, and inverter-related registers.

4. Ladder sections to inspect first
   - `485통신`
   - `MOTOR수동`
   - `ProductAligning`

5. First read-only MCP points to define
   - Auto/manual mode.
   - Emergency stop status, if exposed as a status bit.
   - Conveyor running feedback.
   - Inverter running/fault/speed feedback.
   - Product photo sensor states.
   - Cylinder open/close sensor states.
   - Box presence sensor states.

## MCP Mapping Notes

Create `config\points.yaml` only after confirming the XG5000/Modbus address mapping.

Example shape:

```yaml
points:
  mesh_1_running:
    area: coil
    address: 0
    count: 1
    data_type: bool
    description: Mesh conveyor 1 running feedback

  inverter_1_frequency:
    area: holding_register
    address: 120
    count: 2
    data_type: float32
    word_order: big
    byte_order: big
    unit: hz
    description: Inverter 1 frequency feedback
```

For 32-bit register values, confirm both:

- `word_order`
- `byte_order`

The MCP server now supports both fields with `big` as the default.

## Next Practical Step

Use XG5000 to export or manually record a small first batch of verified read-only points:

```text
5 sensor/status bits
2 inverter status bits
1 inverter speed/frequency register
1 mode/status register or bit
```

After those are known, update:

```text
config\points.yaml
```

Then run a live Modbus TCP smoke test against the PLC.
