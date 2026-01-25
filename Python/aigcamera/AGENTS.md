# AIGCamera Agent Guide

This file tells agentic coding assistants how to work safely and consistently
in this repository. Follow it for any change within `aigcamera`.

## Project Snapshot
- Pure Python library exposing a unified interface for AIGCamera hardware.
- Python 3.12; full type annotations expected everywhere.
- Protocol-first architecture defined in `src/aigcamera/types.py`.
- ReturnCode-based flow control; no exceptions for routine outcomes.
- Dependencies: standard library, `numpy`, `pillow`, proprietary AimPosition `.so`.
- Package code lives under `src/aigcamera`; examples under `examples/`.

## Build / Run
- Use the project venv managed by `uv` for all Python tooling.
- No build step needed for local use; run modules with `uv run`.
- Quick import check: `uv run python -c "from aigcamera.backend.simulated import SimulatedCamera"`.
- Run simulated backend main: `uv run python -m aigcamera.backend.simulated`.
- Aim demo (requires `AimTools` and `AimPosition312.so`): `uv run python examples/aim_backend_demo.py`.
- Hatch wheel build (if needed): `uv run python -m build` with `hatchling` backend; wheel picks up `src/aigcamera/_native/AimPosition312.so` when present.

## Lint / Format
- Use Ruff if configured:
  - Lint: `uv run ruff check .`
  - Format: `uv run ruff format .`
- Keep manual formatting consistent with existing style if Ruff is unavailable.

## Tests
- No tests currently committed.
- Standard pytest usage when tests are added:
  - Full suite: `uv run pytest tests/`
  - Single file: `uv run pytest tests/test_file.py`
  - Single test: `uv run pytest tests/test_file.py::test_name`
- Note absence of tests when adding new APIs and consider adding focused cases.

## Repository Layout
```
aigcamera/
├── src/aigcamera/
│   ├── __init__.py
│   ├── types.py          # Protocols, enums, dataclasses
│   ├── backend/
│   │   ├── simulated.py  # SimulatedCamera
│   │   └── aim.py        # AimCamera
│   ├── _native_loader.py # Shared library loader
│   └── _aimpos.py        # Low-level Aim wrappers
├── examples/             # Demo scripts (Aim requires native lib)
├── ll_aim_api/           # C headers/reference only
└── pyproject.toml        # Hatch build config, deps
```

## Import Conventions
- Order: standard library, third-party (none typical), then local `aigcamera` imports.
- Separate groups with one blank line.
- Prefer explicit imports; avoid star imports.
- Example:
```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from aigcamera.types import CameraProtocol, ReturnCode
```

## Formatting Guidelines
- 4-space indentation; no tabs.
- One class or function per block for clarity.
- Keep line length reasonable and match surrounding style.
- Avoid inline comments unless explicitly requested.
- Preserve blank lines between logical sections; avoid extra trailing whitespace.

## Typing Rules
- Annotate every parameter and return value.
- Use built-in generics (`list[str]`, `dict[str, int]`).
- Use `| None` instead of `Optional`.
- Favor `Protocol` for interfaces and `@dataclass` for data containers.
- Avoid `Any` unless absolutely required; document why if used.

## Naming Conventions
- Classes/Protocols: `PascalCase` (e.g., `SimulatedCamera`).
- Enums: `PascalCase` with `UPPER_CASE` members.
- Functions/Methods: `snake_case`.
- Variables: `snake_case`; private attributes prefixed with `_`.
- Constants: `UPPER_SNAKE_CASE` when needed.

## Error Handling (Critical)
- Do not use exceptions for routine control flow.
- Use `ReturnCode` enums for outcomes and `(ReturnCode, result)` tuples for data.
- Always check `ReturnCode.OK` before using returned data; return early on non-OK.
- Keep error pathways explicit and minimal; avoid silent fallthrough.
- When wrapping native calls, translate native codes to `ReturnCode` immediately.

## Architecture Guidelines
- Define and adjust interfaces in `src/aigcamera/types.py` first.
- Implement protocols in `backend/simulated.py` and mirror behavior in `backend/aim.py`.
- Simulated backend should model controllable state for testing; Aim backend wraps native API via `_native_loader`/`_aimpos`.
- Keep protocol signatures and return types identical across backends.
- Avoid introducing new dependencies.

## Data Structures
- Add or modify dataclass fields in `types.py` first, then propagate to backends.
- Keep dataclass shapes explicit and stable; avoid implicit defaults that obscure intent.
- Maintain list shapes (e.g., rotation vectors, quaternions) as documented.

## Backend Notes
- Simulated backend manages state via `sim_*` helpers; add matching `sim_set_*` when introducing new state.
- Aim backend should mirror simulated semantics where possible and translate native enums/codes carefully.
- Keep connection state in `_connected`; avoid global state.
- Prefer small conversion helpers (e.g., native -> `ReturnCode`, enum translators) to keep methods readable.

## Connection Management
- `connect` should set `_connected` on success; return appropriate `ReturnCode` otherwise.
- `disconnect` must reset handles and `_connected`.
- `is_connected` should be a simple boolean check.
- When a tools path is required, store it and apply after successful connect.

## State & Simulation Helpers
- Methods prefixed with `sim_` are for test control only.
- Keep deterministic defaults for simulated temperature, FPS, warnings, etc.
- Provide clear ways to add/remove/clear simulated tools and status objects.

## Documentation Expectations
- Add docstrings to public methods, classes, and dataclasses describing behavior and return codes.
- Update `README.md` when public APIs change or new usage patterns appear.
- Mention current test coverage gaps when adding new features.

## Dependency Notes
- Core runtime: standard library, `numpy`, `pillow`.
- Native `.so` (`AimPosition312.so`) is proprietary and may be distributed manually; do not assume it exists in CI.
- Do not add new dependencies without discussion.

## Quality Checklist for Agents
- Preserve import order and type annotations.
- Keep `ReturnCode` usage consistent; avoid exception-driven flows.
- Ensure protocol signatures stay in sync across backends.
- Add/extend `sim_` helpers when introducing new stateful behavior.
- Keep docstrings and README in sync with API changes.
- Avoid unnecessary refactors; stay focused on requested scope.

## Testing & Validation Tips
- If tests are added, run the narrowest relevant pytest target first (file or test node).
- For lint/format, prefer Ruff commands above; avoid other linters unless configured.
- When touching Aim backend, be mindful that native `.so` may be absent; guard calls accordingly.

## Cursor / Copilot Rules
- No `.cursor/rules`, `.cursorrules`, or Copilot instruction files are present.
- If such rules appear later, they must be followed in addition to this guide.

## Contribution Etiquette
- Do not introduce new tools or services; stay within existing stack.
- Keep changes minimal, well-typed, and protocol-aligned.
- Use explicit returns for non-OK paths; avoid hidden side effects.
- Respect existing public API surface; avoid breaking changes without documentation updates.

## Quick Commands Summary
- Run simulated backend: `uv run python -m aigcamera.backend.simulated`
- Aim demo (native lib required): `uv run python examples/aim_backend_demo.py`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Tests (when present):
  - Suite: `uv run pytest tests/`
  - File: `uv run pytest tests/test_file.py`
  - Test: `uv run pytest tests/test_file.py::test_name`

(End of agent guide)
