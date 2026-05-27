# LS Modbus MCP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a read-only MCP server that exposes LS XG5000 PLC data over Modbus TCP as named MCP tools.

**Architecture:** The server loads named point definitions from YAML, uses a Modbus TCP client to read raw PLC values, decodes them into typed values, and exposes both named-point and raw-read MCP tools. Write/control support is intentionally excluded from Phase 1, but the project layout keeps it separate for a later guarded command layer.

**Tech Stack:** Python 3.11+, `pymodbus`, `mcp`, `pydantic`, `pyyaml`, `pytest`, `ruff`.

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.gitignore`
- Create: `src/ls_modbus_mcp/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Write the failing test**

Create `tests/test_package.py`:

```python
from ls_modbus_mcp import __version__


def test_package_exposes_version():
    assert isinstance(__version__, str)
    assert __version__
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_package.py -v`

Expected: FAIL because the package does not exist.

**Step 3: Write minimal implementation**

Create `pyproject.toml` with package metadata, dependencies, pytest path config, and a console script:

```toml
[project]
name = "xg5000-mcp"
version = "0.1.0"
description = "Read-only MCP server for LS XG5000 PLC data over Modbus TCP"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "pymodbus>=3.8.0",
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.6.0",
]

[project.scripts]
xg5000-mcp = "ls_modbus_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ls_modbus_mcp"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

Create `src/ls_modbus_mcp/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.venv/
dist/
build/
*.egg-info/
.env
```

Create a README explaining Phase 1 read-only scope and Modbus TCP requirements.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_package.py -v`

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add .gitignore README.md pyproject.toml src tests docs
git commit -m "docs: add ls modbus mcp design and scaffold plan"
```

### Task 2: Point Configuration

**Files:**
- Create: `src/ls_modbus_mcp/points.py`
- Create: `config/points.example.yaml`
- Test: `tests/test_points.py`

**Step 1: Write the failing tests**

Create tests for loading YAML, listing points, rejecting invalid area names, and rejecting invalid counts.

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_points.py -v`

Expected: FAIL because `ls_modbus_mcp.points` does not exist.

**Step 3: Write minimal implementation**

Implement:

- `PointDefinition`
- `PointMap`
- `load_point_map(path: str | Path) -> PointMap`
- supported areas: `coil`, `discrete_input`, `holding_register`, `input_register`
- supported data types: `bool`, `uint16`, `int16`, `uint32`, `int32`, `float32`

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_points.py -v`

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add config/points.example.yaml src/ls_modbus_mcp/points.py tests/test_points.py
git commit -m "feat: load named modbus point configuration"
```

### Task 3: Value Decoding

**Files:**
- Modify: `src/ls_modbus_mcp/points.py`
- Test: `tests/test_points.py`

**Step 1: Write the failing tests**

Add tests for decoding:

- `bool` from coil list
- `uint16`
- `int16`
- scaled values
- multi-register data rejects unsupported counts cleanly for now if needed

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_points.py -v`

Expected: FAIL because decode behavior is missing.

**Step 3: Write minimal implementation**

Add `decode_point_value(point: PointDefinition, raw: list[int] | list[bool]) -> object`.

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_points.py -v`

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add src/ls_modbus_mcp/points.py tests/test_points.py
git commit -m "feat: decode modbus point values"
```

### Task 4: Modbus Client Adapter

**Files:**
- Create: `src/ls_modbus_mcp/modbus_client.py`
- Test: `tests/test_modbus_client.py`

**Step 1: Write the failing tests**

Create tests using a fake async Modbus client that records calls and returns fake responses. Cover raw reads for all four areas and connection error handling.

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_modbus_client.py -v`

Expected: FAIL because the adapter does not exist.

**Step 3: Write minimal implementation**

Implement:

- `ModbusSettings(host, port=502, unit_id=1, timeout=3.0)`
- `AsyncModbusReader`
- `read_area(area, address, count)`
- area-specific methods for coils, discrete inputs, holding registers, input registers

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_modbus_client.py -v`

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add src/ls_modbus_mcp/modbus_client.py tests/test_modbus_client.py
git commit -m "feat: add modbus tcp read adapter"
```

### Task 5: MCP Tool Layer

**Files:**
- Create: `src/ls_modbus_mcp/server.py`
- Test: `tests/test_server_tools.py`

**Step 1: Write the failing tests**

Create tests for pure tool functions:

- `list_points`
- `read_point`
- `read_points`
- raw read argument validation
- unknown point error

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_server_tools.py -v`

Expected: FAIL because tool functions do not exist.

**Step 3: Write minimal implementation**

Implement MCP-facing pure functions first, then register them with `FastMCP`:

- `create_app(point_map, reader)`
- `main()`
- environment variables:
  - `PLC_HOST`
  - `PLC_PORT`
  - `PLC_UNIT_ID`
  - `POINTS_FILE`

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_server_tools.py -v`

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add src/ls_modbus_mcp/server.py tests/test_server_tools.py
git commit -m "feat: expose read-only mcp tools"
```

### Task 6: Verification and Docs

**Files:**
- Modify: `README.md`
- Create: `.env.example`

**Step 1: Write the failing documentation check**

Add a lightweight test or README assertion that verifies the example config path exists and contains at least one point.

**Step 2: Run verification**

Run:

```bash
python -m pytest -v
python -m ruff check .
```

Expected: Tests and lint pass after fixes.

**Step 3: Write usage docs**

README must include:

- install command
- environment variables
- sample MCP client config
- warning that Phase 1 is read-only
- note that future control must go through PLC-side command/request logic

**Step 4: Commit**

Run:

```bash
git add README.md .env.example tests
git commit -m "docs: add setup and read-only usage"
```

### Manual PLC Smoke Test

After the address map is known, run:

```bash
$env:PLC_HOST="192.168.0.10"
$env:PLC_PORT="502"
$env:PLC_UNIT_ID="1"
$env:POINTS_FILE="config/points.yaml"
xg5000-mcp
```

Then query:

- `list_points`
- `read_point` for a known sensor
- `read_coils` or `read_holding_registers` for a known address

Do not enable write/control tools in Phase 1.
