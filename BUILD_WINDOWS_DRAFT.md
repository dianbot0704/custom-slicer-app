# Build AksaratorApp on Windows

> **Status:** The native x64 Release build, NSIS packaging, application startup, and AimPosition runtime loading have been validated. Physical camera validation still requires a connected device.

AksaratorApp is a custom 3D Slicer application. Build it as a native 64-bit Windows application rather than through WSL.

## Prerequisites

Install the following tools:

- Visual Studio 2022 with the **Desktop development with C++** workload, including:
  - MSVC v143 x64/x86 build tools
  - A Windows 10 or Windows 11 SDK
- CMake
- Git for Windows
- A host Python interpreter capable of running `build.py`; it does not have to match Slicer's embedded Python 3.12
- Qt 5.15.2 `msvc2019_64`, installed at `C:\Qt\5.15.2\msvc2019_64`; this installation does not include Qt WebEngine
- Npcap, required by the AimPosition runtime to provide `wpcap.dll`
- NSIS, only when producing a Windows installer

The complete Slicer SuperBuild can take several hours and consume tens of gigabytes. Use a reasonably short build path. The `build.py` helper redirects deeply nested MSBuild autogen intermediates to avoid the legacy 260-character path limit.

## Prepare the build shell

Open **Developer PowerShell for VS 2022** and change to the repository directory:

```powershell
cd C:\path\to\AksaratorApp
```

Select the 64-bit Visual Studio generator:

```powershell
$env:CMAKE_GENERATOR = "Visual Studio 17 2022"
$env:CMAKE_GENERATOR_PLATFORM = "x64"
```

Confirm that the required tools are available in this shell:

```powershell
git --version
cmake --version
cl
```

Select an available host Python executable:

```powershell
$HostPython = (Get-Command python.exe).Source
```

If Python is not on `PATH`, set `$HostPython` to its absolute path.

## Fetch the intraoperative planner extension

The application includes `Extensions/intraop-plan-extension` as a Slicer extension source directory, so it must exist before configuration:

```powershell
& $HostPython .\build.py ext-clone
```

The helper clones the following SSH URL:

```text
git@github.com:dianbot0704/intraop-plan-extension.git
```

Configure a GitHub SSH key with access to that repository before running the command. To use a specific extension branch:

```powershell
& $HostPython .\build.py ext-clone --branch <branch-name>
```

The `Python\aigcamera` source is already present in a normal checkout of this repository and should not be cloned over an existing directory.

## Prepare the Windows AimPosition runtime

Use the vendor ZIP containing the x64 CPython 3.12 `AimPosition312.pyd` API V3.1.2 binding. Keep the archive outside
version control. The configure command records its location, and the SuperBuild stages `AimPosition312.pyd` and
`libusb0.dll` into the installed `aigcamera` package.

The binding also depends on `wpcap.dll`. Install Npcap before running the hardware backend; the loader searches the
standard `C:\Windows\System32\Npcap` directory.

## Configure the SuperBuild

Use the installed Qt kit and pass the vendor archive:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp configure `
  --cmake-prefix-path "C:\Qt\5.15.2\msvc2019_64" `
  --aimposition-archive ".\Win_Py3_2026+FileTambahan.zip" `
  --no-system-openssl `
  --no-webengine `
  --build-type Release
```

The `--no-system-openssl` option sets `Slicer_USE_SYSTEM_OpenSSL=OFF`, allowing the SuperBuild to provide OpenSSL instead of requiring a separate system OpenSSL installation. The installed Qt kit does not include WebEngine, so `--no-webengine` disables Slicer's optional WebEngine support.

To intentionally delete an existing build tree and reconfigure it from scratch:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp configure --fresh `
  --cmake-prefix-path "C:\Qt\5.15.2\msvc2019_64" `
  --aimposition-archive ".\Win_Py3_2026+FileTambahan.zip" `
  --no-system-openssl `
  --no-webengine `
  --build-type Release
```

Review the deletion prompt carefully. Add `--yes` only when unattended deletion of the selected build directory is safe.

## Build the application

Visual Studio is a multi-configuration generator, so select the configuration when building:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp build --config Release --parallel 8
```

Reduce the parallel job count if the machine runs short of memory. On Windows, use this helper instead of invoking the outer `cmake --build` command directly; it supplies the MSBuild intermediate-path workaround to nested SuperBuilds.

## Run the application

After a successful build, launch the application with:

```powershell
C:\b\AksaratorApp\Slicer-build\AksaratorApp.exe
```

Use the launcher rather than invoking the `-real` executable directly because the launcher configures the required runtime environment.

## Package a Windows installer

Install NSIS and ensure it is available to CMake, then build the package target:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp\Slicer-build build `
  --config Release `
  --target PACKAGE
```

The generated package should appear under the Slicer build directory.

## Use a different build directory

Place the global `--build-dir` option before the command. A short build path can help avoid Windows path-length problems:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp configure `
  --cmake-prefix-path "C:\Qt\5.15.2\msvc2019_64" `
  --aimposition-archive ".\Win_Py3_2026+FileTambahan.zip" `
  --no-system-openssl `
  --no-webengine `
  --build-type Release

& $HostPython .\build.py --build-dir C:\b\AksaratorApp build `
  --config Release `
  --parallel 8
```

When using a different build directory, launch the application from that directory's `Slicer-build` subdirectory.

## AIG camera runtime requirements

The Windows hardware backend uses the vendor's unsigned x64 CPython 3.12 `AimPosition312.pyd` API V3.1.2 binding.
The build validates identifying markers in the binding before staging it. Runtime loading additionally requires:

- `libusb0.dll`, staged from the same vendor archive
- Npcap's `wpcap.dll`
- The Microsoft Visual C++ runtime
- The AimPosition USB driver when connecting over USB

Do not commit the proprietary binding, runtime DLL, or vendor ZIP to the repository.

## Troubleshooting

### CMake cannot find Qt5

Check that `--cmake-prefix-path` points to the Qt kit root, for example:

```text
C:\Qt\5.15.2\msvc2019_64
```

That directory should contain `lib\cmake\Qt5`.

### `cl` is not recognized

Run the commands from **Developer PowerShell for VS 2022** or an **x64 Native Tools Command Prompt for VS 2022**. Confirm that the Visual Studio C++ workload is installed.

### The extension clone asks for credentials or reports access denied

Test GitHub SSH access and confirm that the key's account can access `dianbot0704/intraop-plan-extension`.

### Configuration uses the wrong generator or architecture

Delete the build directory with `configure --fresh`, set `CMAKE_GENERATOR` and `CMAKE_GENERATOR_PLATFORM` again, and reconfigure. CMake cannot safely change generator or architecture in an existing build tree.

### MSBuild reports `MSB3491` or a path exceeding 260 characters

Build through `build.py`, which gives CMake-generated `_autogen` projects a short, GUID-based intermediate directory:

```powershell
& $HostPython .\build.py --build-dir C:\b\AksaratorApp build --config Release --parallel 8
```

Do not delete the completed SuperBuild solely for this error; after switching to the helper, the build resumes incrementally.

### Nuitka asks to download MinGW in a non-interactive build

Reconfigure with the current sources and resume through `build.py`. The SuperBuild passes CMake's selected `WindowsSDKVersion` to Nuitka so that it uses the installed MSVC toolchain.
