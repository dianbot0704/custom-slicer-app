# Build and Package AksaratorApp

AksaratorApp is a custom 3D Slicer application. This guide covers Linux and native 64-bit Windows builds. Do not build
the Windows application through WSL.

The initial source files were created using
[KitwareMedical/SlicerCustomAppTemplate](https://github.com/KitwareMedical/SlicerCustomAppTemplate). The
[3D Slicer Developer Guide](https://slicer.readthedocs.io/en/latest/developer_guide/index.html) provides additional
background on Slicer builds.

> **Validated Windows configuration:** The native x64 Release build, NSIS packaging, application startup, SlicerIGT
> module loading, and AimPosition runtime loading have been validated. Connecting to a physical Aim camera still
> requires a connected and correctly configured device.

## Prerequisites

All platforms require:

- Git
- CMake
- A C++ compiler toolchain
- Qt 5.15.2
- A host Python interpreter capable of running `build.py`; it does not need to match Slicer's embedded Python 3.12

A complete Slicer SuperBuild can take several hours and consume tens of gigabytes.

### Linux

Install the required compiler and Qt development packages. Ensure the Qt CMake package can be found through
`CMAKE_PREFIX_PATH` or `Qt5_DIR`, for example `/path/to/Qt5/lib/cmake/Qt5`.

### Windows

Install:

- Visual Studio 2022 with the **Desktop development with C++** workload, including:
  - MSVC v143 x64/x86 build tools
  - A Windows 10 or Windows 11 SDK
- Git for Windows
- Qt 5.15.2 `msvc2019_64`; the validated kit is `C:\Qt\5.15.2\msvc2019_64`
- Npcap, required by AimPosition to provide `wpcap.dll`
- NSIS, only when producing a Windows installer

Use a short build path, such as `C:\b\AksaratorApp`, to reduce Windows path-length risk. The `build.py` helper also
redirects deeply nested MSBuild autogen intermediates to short paths.

## Check out the source

```bash
git clone https://github.com/AIG/AIGSlicer.git
cd <repo-directory>
```

The `aigcamera` source is stored under `Python/aigcamera` and is installed into Slicer's embedded Python by the
`python-aigcamera` SuperBuild target.

## Fetch the intraoperative planner extension

The application expects the separate intraoperative planner repository at `Extensions/intraop-plan-extension`. Clone
or prepare it before the first configure:

```bash
./build.py ext-clone
```

The helper uses this SSH URL:

```text
git@github.com:dianbot0704/intraop-plan-extension.git
```

Configure a GitHub SSH key with access to that repository. To use a specific branch:

```bash
./build.py ext-clone --branch <branch-name>
```

In PowerShell, invoke the same commands through an available host Python:

```powershell
python.exe .\build.py ext-clone
python.exe .\build.py ext-clone --branch <branch-name>
```

## Build on Linux

Configure and build a Release tree:

```bash
./build.py configure \
  --cmake-prefix-path /path/to/Qt5 \
  --build-type Release

./build.py build --parallel <jobs>
```

Run the application through its launcher:

```bash
./build/Slicer-build/AksaratorApp
```

By default, the build bundles SlicerIGSIO and SlicerIGT. To disable them for faster iteration or troubleshooting,
reconfigure with:

```bash
cmake -S . -B build \
  -DCMAKE_PREFIX_PATH=/path/to/Qt5 \
  -DCMAKE_BUILD_TYPE=Release \
  -DAksaratorApp_ENABLE_SLICERIGT=OFF
```

## Build on Windows

### Prepare Developer PowerShell

Open **Developer PowerShell for VS 2022**, change to the repository, and select the x64 Visual Studio generator:

```powershell
cd C:\path\to\AksaratorApp
$env:CMAKE_GENERATOR = "Visual Studio 17 2022"
$env:CMAKE_GENERATOR_PLATFORM = "x64"
```

Confirm that the required tools are available:

```powershell
git --version
cmake --version
cl
```

Select a host Python executable:

```powershell
$HostPython = (Get-Command python.exe).Source
```

If Python is not on `PATH`, set `$HostPython` to its absolute path.

### Prepare the AimPosition runtime

Use the vendor ZIP containing the x64 CPython 3.12 `AimPosition312.pyd` API V3.1.2 binding. Keep the archive outside
version control. The configure command records its location, and the SuperBuild stages `AimPosition312.pyd` and
`libusb0.dll` into the installed `aigcamera` package.

Install Npcap before using the hardware backend. The loader searches the standard
`C:\Windows\System32\Npcap` directory for `wpcap.dll` and its dependencies.

### Configure the SuperBuild

The validated Qt kit does not include Qt WebEngine, so this command disables optional WebEngine support:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp configure `
  --cmake-prefix-path "C:\Qt\5.15.2\msvc2019_64" `
  --aimposition-archive ".\Win_Py3_2026+FileTambahan.zip" `
  --no-system-openssl `
  --no-webengine `
  --build-type Release
```

`--no-system-openssl` lets the SuperBuild provide OpenSSL. Omit `--no-webengine` only when the selected Qt kit
contains the required Qt WebEngine modules.

To intentionally delete an existing build tree and configure it again from scratch, add `--fresh`. Review the deletion
prompt carefully; add `--yes` only when unattended deletion is safe.

### Build and run

Visual Studio is a multi-configuration generator, so select the configuration explicitly:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp build `
  --config Release `
  --parallel 8
```

Reduce the job count if the machine runs short of memory. Use `build.py` rather than invoking the outer
`cmake --build` command directly because the helper supplies the MSBuild path-length workaround to nested builds.

Launch the application with:

```powershell
C:\b\AksaratorApp\Slicer-build\AksaratorApp.exe
```

Use the launcher rather than the `-real` executable because it configures the required runtime environment.

## Rebuild individual components

Rebuild only the embedded `aigcamera` package:

```bash
./build.py build --target python-aigcamera
```

For Visual Studio, add `--config Release`.

Rebuild only the compiled intraoperative planner runtime:

```bash
./build.py ext-build
```

Again, add `--config Release` for Visual Studio.

If `Python/aigcamera/pyproject.toml` dependencies change, rebuild the dependency targets as needed:

```bash
./build.py build --target python-hatchling
./build.py build --target python-pillow
```

The SuperBuild installs `opencv-python-headless` through the `python-opencv` target. Its default version is
`4.11.0.86`, selected to remain compatible with the default NumPy 1.26 pin. Rebuild it with:

```bash
./build.py build --target python-opencv
```

Verify the installed OpenCV and NumPy versions on Linux:

```bash
build/python-install/bin/PythonSlicer -c "import cv2, numpy; print(cv2.__version__); print(numpy.__version__)"
```

On Windows, run the equivalent command with
`C:\b\AksaratorApp\python-install\bin\PythonSlicer.exe`.

## Verify compiled Python modules

When `AksaratorApp_ENABLE_COMPILED_FIDUCIAL_DETECTOR` is `ON` (the default), the build compiles both `aigcamera` and
the intraoperative planner runtime with Nuitka.

On Linux, verify the embedded `aigcamera` package with:

```bash
build/python-install/bin/PythonSlicer -c "import aigcamera, aigcamera.backend.aim as aim; print(hasattr(aigcamera, '__compiled__')); print(hasattr(aim, '__compiled__'))"
```

On Windows, use:

```powershell
C:\b\AksaratorApp\python-install\bin\PythonSlicer.exe -c "import aigcamera, aigcamera.backend.aim as aim; print(hasattr(aigcamera, '__compiled__')); print(hasattr(aim, '__compiled__'))"
```

Both checks should print `True` twice. Compiled extension suffixes are `.so` on Linux and `.pyd` on Windows.

Verify the staged intraoperative planner through the application launcher:

```bash
./build/Slicer-build/AksaratorApp --no-main-window --disable-cli-modules --python-code "import IntraopPlanner, IntraopPlannerImpl, Core.fiducial_detector as fd; print(IntraopPlanner.__file__); print(hasattr(IntraopPlannerImpl, '__compiled__')); print(hasattr(fd, '__compiled__'))"
```

On Windows, run the equivalent check with:

```powershell
& "C:\b\AksaratorApp\Slicer-build\AksaratorApp.exe" --no-main-window --disable-cli-modules --python-code "import IntraopPlanner, IntraopPlannerImpl, Core.fiducial_detector as fd; print(IntraopPlanner.__file__); print(hasattr(IntraopPlannerImpl, '__compiled__')); print(hasattr(fd, '__compiled__'))"
```

The module path should end with `IntraopPlanner.pyc`, and the final two checks should print `True`.

## Windows camera runtime requirements

The Windows hardware backend uses the vendor's unsigned x64 CPython 3.12 `AimPosition312.pyd` API V3.1.2 binding.
The build validates identifying markers before staging it. Runtime loading also requires:

- `libusb0.dll`, staged from the same vendor archive
- Npcap's `wpcap.dll` and `Packet.dll`
- The Microsoft Visual C++ runtime
- The AimPosition USB driver when connecting over USB

Do not commit proprietary native libraries or vendor ZIP archives.

## Fast Python module development loop

On Linux, use the development launcher instead of rebuilding after each Python or UI edit:

```bash
./scripts/run-aksarator-dev.sh
```

The script starts the application with source module paths, enables Slicer developer mode, and updates
`Modules/AdditionalPaths` when needed. In AksaratorApp, use **Reload** or **Reload & Test** after making changes.

Use the normal build loop when changing C++, CMake, or compiled artifacts.

## Package the application

### Linux

```bash
cmake --build build/Slicer-build --target PACKAGE
```

Add the appropriate configuration option when using a multi-config generator.

### Windows installer

Install NSIS and build the package target from the inner Slicer build directory:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp\Slicer-build build `
  --config Release `
  --target PACKAGE
```

The generated installer is written under `C:\b\AksaratorApp\Slicer-build`. It remains unsigned unless code signing is
configured separately.

## Windows troubleshooting

### CMake cannot find Qt5

Check that `--cmake-prefix-path` points to the Qt kit root, such as `C:\Qt\5.15.2\msvc2019_64`. That directory must
contain `lib\cmake\Qt5`.

### `cl` is not recognized

Run the commands from **Developer PowerShell for VS 2022** or an **x64 Native Tools Command Prompt for VS 2022**.
Confirm that the Visual Studio C++ workload is installed.

### The extension clone reports an SSH or access error

Test GitHub SSH access and confirm that the key's account can access `dianbot0704/intraop-plan-extension`.

### Configuration uses the wrong generator or architecture

Delete the build directory with `configure --fresh`, set `CMAKE_GENERATOR` and `CMAKE_GENERATOR_PLATFORM` again, and
reconfigure. CMake cannot safely change the generator or architecture in an existing build tree.

### MSBuild reports `MSB3491` or a path longer than 260 characters

Resume the build through `build.py`, which gives CMake-generated `_autogen` projects short, GUID-based intermediate
directories:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp build --config Release --parallel 8
```

Do not delete the completed SuperBuild solely for this error.

### Nuitka asks to download MinGW

Reconfigure with the current sources and resume through `build.py`. The SuperBuild passes CMake's selected
`WindowsSDKVersion` to Nuitka so it uses the installed MSVC toolchain.

### AimPosition cannot load `wpcap.dll`

Install Npcap and confirm that `C:\Windows\System32\Npcap\wpcap.dll` exists. Run AksaratorApp through its launcher so
that the native DLL search paths are configured correctly.
