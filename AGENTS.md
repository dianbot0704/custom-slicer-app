# Repository Guidelines

## ExecPlans
 
When writing complex features or significant refactors, use an ExecPlan (as described in .agent/PLANS.md) from design to implementation.

To persist your ExecPlan, you can use the .agent directory (alongside the file PLANS.md).
Do not alter the .agent/PLANS.md file.
Use a unique name for each of your ExecPlan.

## Project Structure & Module Organization

- `Applications/`: the custom Slicer application (`AksaratorApp`) and its C++/Qt UI code.
- `Modules/Scripted/`: in-tree scripted modules (Python + Qt `.ui` + resources).
- `Extensions/`: Slicer extensions (e.g., `Extensions/IntraOperativePlan/Modules/Scripted/...`).
- `build/`: *local* CMake/SuperBuild output (ignored by git). Do not edit or commit generated files.

## Build, Test, and Development Commands

This repo uses a Slicer SuperBuild driven by CMake (see `BUILD.md` for Windows details).

- Configure (example): `cmake -S . -B build -DQt5_DIR=/path/to/Qt5/lib/cmake/Qt5`
- Build: `cmake --build build --config Release`
- Run (after build): `./build/Slicer-build/AksaratorApp` (launcher) or `./build/Slicer-build/bin/AksaratorApp-real`
- Package (Windows/NSIS or if enabled): `cmake --build build/Slicer-build --config Release --target PACKAGE`

## Coding Style & Naming Conventions

- Python: formatted/linted by Ruff (`.ruff.toml`), max line length 120, target Python 3.12.
- Pre-commit: install once with `pre-commit install`, run with `pre-commit run -a`.
- Scripted module layout: `.../Modules/Scripted/<ModuleName>/<ModuleName>.py` + `Resources/` (icons, `.ui`, `.qrc`).
- Follow existing conventions for CMake and C++/Qt code in `Applications/`.

## Testing Guidelines

- CI runs `pre-commit` hooks; keep the tree clean of generated artifacts (e.g., `__pycache__/`).
- For built test suites (Slicer/CTK/VTK), run: `ctest --test-dir build/Slicer-build -C Release`.

## Commit & Pull Request Guidelines

- Commit messages follow the repo’s existing “Conventional Commits”-style subjects (e.g., `feat: ...`, `fix: ...`) and must pass the “Commit Message Check” workflow.
- PRs should include: a clear description, rationale, steps to validate (build/run), and screenshots/gifs for UI changes.
- When submitting a PR, add a `Cc: @Aksarator/developers` comment (see `CONTRIBUTING.md`).

## Security & Data

Do not commit patient data (DICOM/PHI) or large binary assets; use sanitized test data and keep local datasets outside the repo.
