# Automated application verification

Run a repeatable UI smoke check without navigating the app manually. The runner starts the real AksaratorApp, drives its PythonQt widgets, checks transitions and rendering, saves evidence, and closes the process.

This first iteration is a **UI and rendering check, not a clinical, database, or hardware validation**. It uses one synthetic surgeon account, an empty patient list, and a generated volume and sphere. Camera connections and DICOM receivers are disabled.

## Run the check

Requirements:

- Linux with Python 3.9 or later for the runner. It uses only the standard library.
- A working AksaratorApp build with the current IntraopPlanner `Runtime/` and `Pages/` layout. Slicer's embedded Python supplies Qt, VTK, and NumPy.
- A desktop display with working OpenGL, or an Xvfb installation with working software OpenGL.
- Approximately 350 MB of temporary disk space for the isolated module copy.

From the repository root:

```bash
./scripts/verify-app.py
```

No input is required. The app window appears briefly on the current display. Each run gets a unique directory under `out/verification/`. The last output line points to `report.html`; open that file in a browser to review the checks and screenshots.

Rebuild application or extension changes before running. By default, the runner checks the **built runtime**, including Nuitka extensions, not the separate extension source checkout. It does not build the project itself.

For another build or installation, pass the launcher, not the `*-real` executable:

```bash
./scripts/verify-app.py \
  --app /absolute/path/to/AksaratorApp \
  --module-dir /absolute/path/to/lib/AksaratorApp-5.11/qt-scripted-modules
```

The module directory is normally detected beside the launcher. Pass it explicitly if the application layout is different or contains multiple version directories.

### Run without a visible desktop window

If `xvfb-run`, Xvfb, `xauth`, and suitable Mesa/OpenGL libraries are already installed:

```bash
./scripts/verify-app.py --display xvfb
```

This starts a private virtual X display with a 1920 × 1080 screen. The runner does not install system packages. Xvfb mode is provided but was not runtime-verified on the initial development machine because Xvfb was absent.

`QT_QPA_PLATFORM=offscreen` is deliberately not supported. During initial verification, that Qt backend produced VTK OpenGL state warnings and a shutdown timeout on the local NVIDIA setup. The runner clears an inherited `QT_QPA_PLATFORM` so it cannot silently select that backend.

## What the check covers

| Check | Expected result |
| --- | --- |
| Startup and page construction | The app selects IntraopPlanner itself; all 12 expected page controllers and all six workflow headers exist. |
| General access PIN | A wrong PIN stays on the PIN page and clears the input; Back returns to the landing page. |
| Patient and surgeon settings | The landing-page menu leads through the PIN gate to each settings page; Back returns correctly. |
| Surgeon selection | Search filters the real account cards; the synthetic account opens its login page. |
| Surgeon PIN | A wrong PIN creates no session; the correct fixture PIN passes through the real hashing and verification logic. Account persistence is replaced. |
| Disclaimer | Agree starts disabled, scrolling to the end enables it, and clicking it opens Welcome. |
| Intraop workflow | The real buttons open Level Selection, Verification, and Scan Patient; forward remains disabled without a registered CT. |
| Plan preview and rendering | A direct page preview loads a synthetic volume, creates three independent slice views and a 3D view, and renders both a gray volume and a red sphere. Pixel checks reject blank or missing-object renders. |
| Navigate preview | Its views are independent of Plan's; the last step has no forward button. Home clears the synthetic case data. |
| Fluoroscopy workflow | Its four-step sequence opens Capture Images; forward stays disabled without assigned captures. |
| Logout and isolation | Logout removes the session and PIN; no disk database or native camera was created. Recorded Python callback exceptions and application logging errors fail the run. |

Plan and Navigate are **explicit previews**. The script enters Plan directly after checking that Scan Patient's forward gate is closed. It does not change `canAdvance()`, simulate successful registration, or claim that a clinical workflow was completed.

Slicer testing mode automatically answers the shared Home/logout confirmation dialogs. Those confirmation dialogs are not interaction-tested here. The disclaimer is different: the script drives the actual modal dialog and its scroll gate.

This iteration does not cover patient/account writes, schema migrations, DICOM transfer or import, fiducial detection, registration accuracy, screw-placement accuracy, live tracking, camera networking, robot control, all screen sizes, or visual snapshot comparison. A passing render check also does not establish rendering performance or prove that every VTK warning is harmless. Native Qt/VTK messages remain available in the console log.

## Artifacts and exit status

| Artifact | Purpose |
| --- | --- |
| `report.html` | Local report with per-check results, scope notes, and a screenshot gallery. No web server is required. |
| `result.json` | Final result, process exit code, duration, command, runtime origin, and OpenGL capabilities. |
| `scenario.json` | Incremental in-app checkpoints. It remains useful if the app crashes or hangs later. |
| `console.log` | Combined application stdout and stderr, including native Qt/VTK messages. |
| `*.png` | App-window screenshots and the synthetic 3D render. The desktop is not captured. |

Exit codes:

- `0`: every check passed, the completion token belongs to this run, and the application exited successfully.
- `1`: a failed check, crash, timeout, missing/incomplete report, or runner failure after output setup.
- `2`: invalid arguments or missing prerequisites.

The default application timeout is 180 seconds. It includes startup, all checks, and shutdown, but not staging the module copy. On timeout or Ctrl+C, the runner terminates its private process group, including launcher children. Temporary settings and runtime files are then removed. A timeout still fails even if every UI checkpoint passed before shutdown.

To change the timeout or choose an artifact directory:

```bash
./scripts/verify-app.py --timeout 240 --output-dir out/verification/review-001
```

An explicit output directory must be new or empty. Existing artifacts are never reused or overwritten. `out/` is ignored by Git.

To verify failure reporting deliberately:

```bash
./scripts/verify-app.py --force-failure
```

Expected: exit `1`, a failed startup checkpoint, a screenshot, and a failure report. This is not an application defect.

## Isolation and implementation

Only `scripts/verify-app.py` is a normal Python entry point. Do not launch the support scripts directly in your usual Slicer session.

The runner copies the built `Runtime`, `Core`, `Pages`, `PatientData`, and `Libraries` packages and known static resource directories into a fresh temporary directory. It excludes live database/resource-data directories, DICOM datasets, HL7 output, and captures. A verification-only discovery bootstrap loads those copied runtime classes and installs the UI fixtures **before widget setup**. Therefore the shipped discovery bootstrap itself is not tested by this run.

A temporary `HOME` and XDG settings/data/cache directories isolate user state. Slicer runs with `--testing`, which disables user settings and ignores `.slicerrc.py`. The DICOM module and optional render tracing are not started. Python SQLite connections are blocked; the fixtures do not run migrations or open existing databases. The in-memory surgeon store supplies a hashed synthetic PIN to the real surgeon manager. Camera and receiver start calls are counted but do not connect to hardware or listen on network ports.

This is test isolation for the known application, not an operating-system security sandbox for arbitrary code. No production module, extension checkout, CMake output, or user database is modified by the automation code.

Files:

- `../verify-app.py`: process supervision, temporary runtime/settings, timeout, and final reports.
- `IntraopPlanner.py`: temporary discovery bootstrap.
- `ui_fixtures.py`: explicit in-memory storage and disabled hardware dependencies.
- `scenario.py`: the concrete UI scenario, assertions, screenshots, and incremental checkpoints.

To extend coverage, add concrete actions and assertions to `scenario.py`. Keep unsupported external operations explicit. Do not silently replace a failed production controller or weaken a workflow gate to make a check pass. Database/hardware integration needs a separately approved disposable-data and device-safety setup.

## Initial verification evidence

The implementation was run against the local Linux Debug build with the compiled IntraopPlanner runtime and an NVIDIA RTX 3050 OpenGL context. Repeated normal-display runs passed all 12 checks, including mixed volume/model rendering. Intentional failure and timeout runs returned nonzero status and preserved diagnostics. A disposable module copy with a renamed Start button also failed automatically and produced a diagnostic screenshot; the real built UI was not changed.

A disposable runner harness also checked missing reports, malformed reports, a stale completion token, incomplete/failed/empty check lists, a nonzero app exit after completion, child-process timeout cleanup, and refusal to overwrite existing artifacts. It was created outside the repository and removed after execution. Ruff lint and formatting checks passed for the new Python files.

A before/after byte comparison also confirmed that the selected original database and application settings files were unchanged by a normal run.

The local review report is at `out/verification/review/report.html`. Generated evidence is intentionally not committed.
