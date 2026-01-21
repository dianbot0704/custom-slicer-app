# Build and Package AIGSlicer

This document summarizes how to build and package AIGSlicer on Linux.

AIGSlicer is a custom Slicer application. Reading the [3D Slicer Developer Documentation](https://slicer.readthedocs.io/en/latest/developer_guide/index.html) may help answer additional questions.

The initial source files were created using [KitwareMedical/SlicerCustomAppTemplate](https://github.com/KitwareMedical/SlicerCustomAppTemplate).

## Prerequisites

- Install git, CMake, a C++ compiler toolchain, and Qt5.
- Ensure `Qt5_DIR` points to your Qt5 CMake package (for example: `/path/to/Qt5/lib/cmake/Qt5`).

## Checkout

```bash
git clone https://github.com/AIG/AIGSlicer.git
cd AIGSlicer
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

## Package

```bash
cmake --build build/Slicer-build --target PACKAGE
```

For multi-config generators, add `--config Release`.
