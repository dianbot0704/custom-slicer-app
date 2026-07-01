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

When `AksaratorApp_ENABLE_COMPILED_FIDUCIAL_DETECTOR` is `ON` (the default),
the build compiles both the embedded `aigcamera` package and the
`Extensions/intraop-plan-extension/TesModule` runtime Python modules with
Nuitka. The built app stages the intraop planner implementation as shared
libraries in `qt-scripted-modules`, keeps only bytecode bootstraps for Slicer
module discovery, and leaves `.ui` assets staged as `.ui` files.

To verify the built package is coming from the compiled artifact rather than
the source `.py` file, run:

```bash
build/python-install/bin/PythonSlicer -c "import aigcamera, aigcamera.backend.aim as aim; print(hasattr(aigcamera, '__compiled__')); print(hasattr(aim, '__compiled__'))"
```

The command should print `True` twice. On disk, the compiled package root
should appear as something like
`build/python-install/lib/python3.12/site-packages/aigcamera.cpython-312-*.so`,
and the compiled submodule should appear as
`build/python-install/lib/python3.12/site-packages/aigcamera/backend/aim.cpython-312-*.so`.

To clone the separate intraop planner extension repository into the expected
`Extensions/intraop-plan-extension` path:

```bash
./build.py ext-clone
./build.py ext-clone --branch CobaCoba
```

To rebuild only the intraop planner extension's compiled runtime payload:

```bash
cmake --build build/Slicer-build --target CompileTesModuleNuitkaModule
```

To verify the built app is loading the compiled intraop planner payload rather
than staged source `.py` files, run:

```bash
./build/Slicer-build/AksaratorApp --no-main-window --disable-cli-modules --python-code "import IntraopPlanner, IntraopPlannerImpl, Core.fiducial_detector as fd; print(IntraopPlanner.__file__); print(hasattr(IntraopPlannerImpl, '__compiled__')); print(hasattr(fd, '__compiled__'))"
```

The first line should end with `IntraopPlanner.pyc`, and the last two lines
should both print `True`.

If `pyproject.toml` dependencies change, also rebuild the dependency targets:

```bash
cmake --build build --target python-hatchling
cmake --build build --target python-pillow
```

## OpenCV (`cv2`) Python package

The SuperBuild installs OpenCV into the embedded Python as target
`python-opencv` using `opencv-python-headless`.

Default pinning keeps it compatible with the default NumPy pin:

- `AksaratorApp_PIN_OPENCV=ON`
- `AksaratorApp_OPENCV_VERSION=4.11.0.86`

To rebuild only OpenCV in the embedded Python:

```bash
cmake --build build --target python-opencv
```

Quick runtime validation:

```bash
build/python-install/bin/PythonSlicer -c "import cv2, numpy; print(cv2.__version__); print(numpy.__version__)"
```

## Build

Note: The build process can take a few hours.

```bash
cmake -S . -B build -DQt5_DIR=/path/to/Qt5/lib/cmake/Qt5 -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

By default, this configure step bundles the `SlicerIGSIO` and `SlicerIGT` extensions.
To disable that integration (for faster iteration or troubleshooting), add:

```bash
cmake -S . -B build -DQt5_DIR=/path/to/Qt5/lib/cmake/Qt5 -DCMAKE_BUILD_TYPE=Release -DAksaratorApp_ENABLE_SLICERIGT=OFF
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
