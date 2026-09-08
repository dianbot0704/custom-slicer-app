# Repository Guidelines

## Project Structure & Module Organization

- `Applications/`: the custom Slicer application (`AksaratorApp`) and its C++/Qt UI code.
- `Modules/Scripted/`: in-tree scripted modules (Python + Qt `.ui` + resources).
- `Extensions/`: Slicer extensions.
- `build/`: *local* CMake/SuperBuild output (ignored by git). Do not edit or commit generated files.

## Build, Test, and Development Commands

This repo uses a CMake-driven Slicer SuperBuild. Prefer the repository's `build.py` helper for common workflows (see `BUILD.md` for details).

- Show available commands and options: `./build.py --help` or `./build.py <command> --help`.
- Clone or prepare the intraop planner extension: `./build.py ext-clone` (optionally `--branch <branch>`). This uses the extension repository's SSH URL.
- Configure: `./build.py configure --cmake-prefix-path /path/to/Qt5`. The helper defaults to a Debug build, system OpenSSL, and NumPy 1.26.4.
- Reconfigure from scratch: `./build.py configure --fresh`; add `--yes` only when intentional deletion of the selected build directory is safe.
- Build: `./build.py build --parallel <jobs>`; for multi-config generators, add `--config Debug` (or the configured variant).
- Rebuild the compiled intraop planner extension target: `./build.py ext-build`; it accepts the same `--parallel` and `--config` options as `build`.
- To use a non-default build tree, put the global option before the command, for example `./build.py --build-dir build-debug configure`.
- Run (after build): `./build/Slicer-build/AksaratorApp` (launcher) or `./build/Slicer-build/bin/AksaratorApp-real`.
- Package (Windows/NSIS or if enabled): `cmake --build build/Slicer-build --config Release --target PACKAGE`.

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
