# Build and Package AksaratorApp

This document summarizes how to build and package AksaratorApp on Linux.

AksaratorApp is a custom Slicer application. Reading the [3D Slicer Developer Documentation](https://slicer.readthedocs.io/en/latest/developer_guide/index.html) may help answer additional questions.

The initial source files were created using [KitwareMedical/SlicerCustomAppTemplate](https://github.com/KitwareMedical/SlicerCustomAppTemplate).

## Prerequisites

- Install git, CMake, a C++ compiler toolchain, and Qt5.
- Ensure `Qt5_DIR` points to your Qt5 CMake package (for example: `/path/to/Qt5/lib/cmake/Qt5`).

## Checkout

```bash
git clone https://github.com/AIG/AIGSlicer.git
cd <repo-directory>
```

## AIGCamera Python package

The `aigcamera` Python package is a separate repository and must be cloned into
`Python/aigcamera` before the first configure. It is installed into Slicer's
embedded Python via the superbuild target `python-aigcamera`.

1. Clone the source into the repository:

```bash
mkdir -p Python
git clone https://github.com/alwint3r/aigcamera Python/aigcamera
```

2. If you already cloned it, update it:

```bash
git -C Python/aigcamera pull
```

3. Rebuild only the embedded package after changes:

```bash
cmake --build build --target python-aigcamera
```

For multi-config generators, add `--config Release`.

If `pyproject.toml` dependencies change, also rebuild the dependency targets:

```bash
cmake --build build --target python-hatchling
cmake --build build --target python-pillow
```

## Build

Note: The build process can take a few hours.

```bash
cmake -S . -B build -DQt5_DIR=/path/to/Qt5/lib/cmake/Qt5 -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

## Fast Python module development loop

For scripted-module development, use the dev launcher instead of rebuilding after
each Python/UI edit:

```bash
./scripts/run-aksarator-dev.sh
```

This launcher:

- starts `build/Slicer-build/AksaratorApp`
- adds source module paths via `--additional-module-paths`
- enables Slicer developer mode (`Developer/DeveloperMode=true`)
- appends those source paths to `Modules/AdditionalPaths` if needed

Inside AksaratorApp, open your scripted module and use `Reload` (or
`Reload & Test`) in the module panel after edits.

You can verify source loading from the Python console:

```python
print(slicer.util.modulePath("Home"))
print(slicer.util.modulePath("IntraOperativePlan"))
print(slicer.util.modulePath("LiveTransform"))
```

The printed paths should point to your repository source tree, not
`build/.../qt-scripted-modules/...`.

Use the normal build loop when you change C++, CMake, or other compiled
artifacts.

## Package

```bash
cmake --build build/Slicer-build --target PACKAGE
```

For multi-config generators, add `--config Release`.
