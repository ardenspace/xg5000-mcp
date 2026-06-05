# Field Commissioning Guide (현장 시운전 가이드)

This document is for the on-site step that could **not** be done offline. An agent should read this and walk the on-site user through it. All values here are the **confirmed Taesung cabinet values** (not placeholders).

> Context: Offline prep is done — Modbus server config, network plan, inverter D-word mapping, and input-sensor P-address map are all confirmed. See `docs/HANDOFF.md` and `docs/taesung-project-review.md`. What remains requires the **live PLC on site**.

## Confirmed values (use these directly)

| Item | Value |
| --- | --- |
| PLC / XBL-EMTA IP | `192.168.240.9` |
| Test PC IP | `192.168.240.100` |
| Subnet / Gateway | `255.255.255.0` / `192.168.240.1` |
| JAKA cabinet IP | `192.168.240.10` |
| Modbus TCP port | `502` |
| Unit / 국번 (slave id) | `1` |
| Server mode | 모드버스 서버 (Modbus server) |

## STEP A — Field PC setup (do once, before anything else)

The committed repo already includes the real `config/points.yaml` (96 points), so a fresh clone is ready to use — no copy-from-example needed.

```powershell
git clone <repo-url> xg5000-mcp
cd xg5000-mcp
python -m pip install -e ".[dev]"     # needs Python 3.11+
```

Caveats:
- **Offline field PC:** `pip install` pulls `mcp`, `pymodbus`, `pydantic`, `pyyaml` from the internet. If the field network is closed/air-gapped, prepare a `.venv` (or download the wheels) **before** going on site — installing there will otherwise fail.
- **Python 3.11+** must be installed.
- **The MCP server is not a standalone app.** `xg5000-mcp` is a stdio MCP server, normally launched by an MCP client (Claude Desktop / Claude Code / etc.). To actually call tools (`read_point`, …) you need an MCP client on the field PC — see the client config JSON in `README.md`. Use the confirmed env values (`PLC_HOST=192.168.240.9`, `PLC_PORT=502`, `PLC_UNIT_ID=1`, `POINTS_FILE=config\points.yaml`).

## STEP 0 — Download the modified comm parameter to the live PLC (REQUIRED FIRST)

Offline, the `워드 읽기 영역 시작 주소` was changed `P0000 → D00000` so inverter D-words become readable over Modbus. **This only takes effect after downloading parameters to the real PLC.**

1. Open `D:\Taesung\TaesungProject2\TaesungProject2.xgwx` in XG5000.
2. Connect to the PLC online, write/download **parameters** (I/O 파라미터 / Ethernet 파라미터).
3. The Ethernet module may need a **reset/restart** for comm-parameter changes to apply.
4. Re-confirm in the FEnet `Modbus 설정` dialog that `워드 읽기 = D00000` and `워드 쓰기 = P0000` (write area must stay `P` — do NOT point it at `D`, or a Modbus client could command the inverter and bypass ladder safety).

## STEP 1 — PC network setup

Set the test PC to `192.168.240.100 / 255.255.255.0 / gateway 192.168.240.1`. Make sure the IP does not collide with PLC (`.9`) or JAKA cabinet (`.10`).

## STEP 2 — Connectivity test

```powershell
ping 192.168.240.9
Test-NetConnection 192.168.240.9 -Port 502
```

Expected: ping replies (if ICMP allowed) and `TcpTestSucceeded: True`. If port 502 fails: confirm STEP 0 download/reset happened, check the module IP, and check any host-access/firewall restriction.

## STEP 3 — Run the MCP server

```powershell
cd D:\xg5000-mcp
$env:PLC_HOST="192.168.240.9"
$env:PLC_PORT="502"
$env:PLC_UNIT_ID="1"
$env:POINTS_FILE="config\points.yaml"
xg5000-mcp
```

## STEP 4 — Verify reads (the critical on-site checks)

### 4a. Confirm the 0-based offset assumption (off-by-one risk)

The config assumes Modbus offset `0` = `P0000.0` and register `0` = `D0000`, i.e. **0-based**. LS firmware has historically shifted between 0-based and 1-based Modbus addressing, so verify before trusting any value:

- Pick a sensor whose physical state you can change (e.g. box detect `box_1_detect`, offset `2`).
- Toggle it physically and watch `read_point`. If the value tracks the real sensor → 0-based is correct.
- If everything reads off by one position, the PLC is 1-based — add `+1` to all offsets (or adjust a base) and document it.

### 4b. Verify input sensors (discrete inputs, P area)

The full point map is in `config/points.yaml` (96 points: 64 discrete inputs + 32 inverter registers). Use `read_point` / `read_points`. Physically trigger a sensor and confirm the read value flips. Spot-check at least: one box-detect, one injection photosensor, one cylinder closed/open pair.

Note: physical **output solenoids** (`P20~P28`, offsets 32~40) are also read via `read_discrete_inputs` — they live in the bit-read window, so reading them returns the live output state. Do NOT use `read_coils` for them (the bit-write area `P01000` is empty scratch). `1` = solenoid energized.

### 4c. Verify inverter D-words (input registers, D area)

- `read_input_registers(address=100)` → should read `D00100` = start/stop command (`1`=stop, `2`=run).
- `read_input_registers(address=600)` → should read `D00600` = output frequency command (`0~60`).
- Cross-check against HMI: when HMI button (`M00502`) is ON, `D00100` should read `2`; OFF → `1`.

## STEP 5 — Re-confirm provisional / pending addresses

These were flagged as not-yet-final in the I/O map — verify on site and update `config/points.yaml`:

1. **박스 만재감지 센서** — currently `P06/P07/P08` (offsets 6/7/8) are **temporary** due to a missing label printer. Per the I/O map they will move to `P85/P86/P87` (offsets 133/134/135), with wire labels `DI64→12, 65→15, 66→16`. Confirm which addresses are actually live on the PLC right now.
2. **사출물 감지 photosensor labels** — wire labeling was changed pending relabeling; confirm the physical sensor↔P-address still matches the map.

## Acceptance checklist (Phase 1 complete)

- [ ] STEP 0 parameter download done; `워드 읽기 = D00000` confirmed on the live PLC
- [ ] `Test-NetConnection 192.168.240.9 -Port 502` → `True`
- [ ] 0-based vs 1-based confirmed by a physical toggle test
- [ ] ≥5 input sensors verified: physical change → MCP read change
- [ ] `D00100` and `D00600` read sensible inverter values, cross-checked vs HMI
- [ ] Provisional addresses (박스만재) reconciled with reality
- [ ] No write/control tool exposed (Phase 1 is read-only)

## Safety reminder

Phase 1 is **read-only**. Do not add write/control tools until reads are verified. When control is added later, write only to PLC-side command/request addresses — never directly to physical output coils or inverter registers — and let PLC ladder own all interlocks, e-stop, and mode logic.
