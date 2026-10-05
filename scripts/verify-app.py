#!/usr/bin/env python3
"""Run isolated UI verification in a built AksaratorApp (Linux, standard library only)."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import suppress
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_DIR = Path(__file__).resolve().parent / "verification"


def main() -> int:  # noqa: PLR0912, PLR0915
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=REPO_ROOT / "build/Slicer-build/AksaratorApp", help="App launcher")
    parser.add_argument(
        "--module-dir", type=Path, help="Built qt-scripted-modules directory (auto-detected by default)"
    )
    parser.add_argument(
        "--output-dir", type=Path, help="New/empty artifact directory (default: out/verification/<run>)"
    )
    parser.add_argument("--timeout", type=int, default=180, help="Whole-process timeout in seconds (default: 180)")
    parser.add_argument(
        "--display", choices=("current", "xvfb"), default="current", help="Qt display mode (default: current)"
    )
    parser.add_argument(
        "--force-failure", action="store_true", help="Fail after startup to verify the failure/report path"
    )
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("This first iteration supports Linux only.")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    app = args.app.expanduser().resolve()
    if not app.is_file() or not os.access(app, os.X_OK):
        parser.error(f"Launcher is not executable: {app}. Build the app first.")
    module_dir = args.module_dir
    if module_dir is None:
        candidates = sorted(app.parent.glob("lib/*/qt-scripted-modules"))
        if len(candidates) != 1:
            parser.error("Cannot identify the built module directory. Pass --module-dir explicitly.")
        module_dir = candidates[0]
    module_dir = module_dir.expanduser().resolve()
    if not (module_dir / "Runtime").is_dir() or not (module_dir / "Pages").is_dir():
        parser.error(f"IntraopPlanner Runtime/Pages not found in {module_dir}")
    if args.display == "current" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        parser.error("No display found. Use --display xvfb (requires xvfb-run).")
    if args.display == "xvfb" and shutil.which("xvfb-run") is None:
        parser.error("xvfb-run is not installed. Install Xvfb separately or use the current display.")
    run_id = uuid.uuid4().hex
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.output_dir or REPO_ROOT / "out/verification" / f"{stamp}-{run_id[:8]}").expanduser().resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error(f"Artifact directory must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    result = {
        "schema_version": 1,
        "run_id": run_id,
        "started_utc": stamp,
        "app": str(app),
        "module_dir": str(module_dir),
        "display_mode": args.display,
        "timeout_seconds": args.timeout,
        "status": "failed",
        "checks": [],
        "scope": "Real UI and rendering; in-memory account/patient fixtures; camera and DICOM receivers disabled",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="aksarator-verification-") as temporary:
            sandbox = Path(temporary)
            runtime = sandbox / "module"
            runtime.mkdir()
            # Copy only runtime code and known static asset directories. Never copy
            # Resources/Resources (live databases), DICOM, HL7, or case captures.
            for directory in ("Runtime", "Core", "Pages", "PatientData", "Libraries"):
                shutil.copytree(
                    module_dir / directory,
                    runtime / directory,
                    ignore=shutil.ignore_patterns("__pycache__", "*.db*", "*.sql*"),
                )
            for directory in ("UI", "Icons", "Images", "Models", "Screw", "AimTools", "FixtureLayouts"):
                shutil.copytree(module_dir / "Resources" / directory, runtime / "Resources" / directory)
            shutil.copy2(SUPPORT_DIR / "IntraopPlanner.py", runtime / "IntraopPlanner.py")
            support_package = runtime / "verification_support"
            support_package.mkdir()
            shutil.copy2(SUPPORT_DIR / "ui_fixtures.py", support_package / "__init__.py")
            home = sandbox / "home"
            home.mkdir()
            environment = os.environ.copy()
            environment.update(
                HOME=str(home),
                XDG_CONFIG_HOME=str(home / ".config"),
                XDG_DATA_HOME=str(home / ".local/share"),
                XDG_CACHE_HOME=str(home / ".cache"),
                TMPDIR=str(sandbox),
                PYTHONDONTWRITEBYTECODE="1",
                PYTHONNOUSERSITE="1",
                AKSARATOR_VERIFY_SANDBOX=str(sandbox),
                AKSARATOR_VERIFY_OUTPUT=str(output),
                AKSARATOR_VERIFY_RUN_ID=run_id,
                AKSARATOR_VERIFY_FORCE_FAILURE="1" if args.force_failure else "0",
                INTRAOPPLANNER_HOST_APP="aksarator",
            )
            # Do not inherit optional tracing, source-module overrides, or Python
            # startup hooks from a developer shell.
            for name in list(environment):
                if name.startswith(("AKSARATOR_DEV_", "AKSARATOR_SESSION_RENDER_TRACE", "AIG_RENDER_TRACE")):
                    environment.pop(name)
            for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
                environment.pop(name, None)
            environment.pop("QT_QPA_PLATFORM", None)
            command = [
                str(app),
                "--launcher-no-splash",
                "--launcher-ignore-user-additional-settings",
                "--no-splash",
                "--testing",
                "--modules-to-ignore",
                "DICOM,DICOMwebBrowser,DICOMPatcher,SessionRenderTrace",
                "--additional-module-path",
                str(runtime),
                "--python-script",
                str(SUPPORT_DIR / "scenario.py"),
            ]
            if args.display == "xvfb":
                command = ["xvfb-run", "-a", "-s", "-screen 0 1920x1080x24", *command]
            result["command"] = command
            print(f"Artifacts: {output}", flush=True)
            with (output / "console.log").open("w", encoding="utf-8") as console:
                process = subprocess.Popen(  # noqa: S603 - explicit local application, no shell
                    command,
                    cwd=sandbox,
                    env=environment,
                    stdout=console,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    result["exit_code"] = process.wait(timeout=args.timeout)
                except subprocess.TimeoutExpired:
                    result["error"] = f"Application exceeded the {args.timeout}s timeout"
                finally:
                    # Kill the private process group, including any launcher children.
                    # Also run this after a premature launcher exit or Ctrl+C.
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    else:
                        time.sleep(0.5)
                        with suppress(ProcessLookupError):
                            os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    result.setdefault("exit_code", process.returncode)
            scenario_path = output / "scenario.json"
            if scenario_path.is_file():
                scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
                if not isinstance(scenario, dict) or not isinstance(scenario.get("checks"), list):
                    raise ValueError("Malformed scenario.json: expected an object with a checks list")
                if any(
                    not isinstance(check, dict)
                    or not isinstance(check.get("name"), str)
                    or not isinstance(check.get("status"), str)
                    for check in scenario["checks"]
                ):
                    raise ValueError("Malformed scenario.json: invalid check entry")
                for check in scenario["checks"]:
                    for field in ("scope", "error", "screenshot"):
                        if field in check and not isinstance(check[field], str):
                            raise ValueError(f"Malformed scenario.json: check {field} must be text")
                if "error" in scenario and not isinstance(scenario["error"], str):
                    raise ValueError("Malformed scenario.json: error must be text")
                if not isinstance(scenario.get("runtime", {}), dict):
                    raise ValueError("Malformed scenario.json: runtime must be an object")
                result["checks"] = scenario["checks"]
                result["runtime"] = scenario.get("runtime", {})
                completed = (
                    scenario.get("run_id") == run_id
                    and scenario.get("completed") is True
                    and bool(result["checks"])
                    and all(check.get("status") == "passed" for check in result["checks"])
                )
                if completed and result.get("exit_code") == 0 and "error" not in result:
                    result["status"] = "passed"
                else:
                    result.setdefault("error", scenario.get("error") or "Incomplete checks or nonzero application exit")
            else:
                result.setdefault("error", "Application did not produce scenario.json; see console.log")
    except (OSError, ValueError, KeyboardInterrupt) as exc:
        result["error"] = str(exc) or type(exc).__name__
    result["duration_seconds"] = round(time.monotonic() - started, 3)
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    rows = []
    for check in result["checks"]:
        screenshot = check.get("screenshot")
        image = f'<a href="{html.escape(screenshot)}">Screenshot</a>' if screenshot else ""
        rows.append(
            f"<tr><td>{html.escape(check['name'])}</td><td>{html.escape(check['status'])}</td>"
            f"<td>{html.escape(check.get('scope', ''))}</td>"
            f"<td><pre>{html.escape(check.get('error', ''))}</pre></td><td>{image}</td></tr>"
        )
    gallery = "".join(
        f'<figure><a href="{html.escape(image.name)}">'
        f'<img loading="lazy" src="{html.escape(image.name)}" alt="{html.escape(image.stem)}" style="max-width:100%">'
        f"</a><figcaption>{html.escape(image.stem)}</figcaption></figure>"
        for image in sorted(output.glob("*.png"))
    )
    (output / "report.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Aksarator UI verification</title>'
        "<style>body{font:16px sans-serif;max-width:1100px;margin:40px auto;padding:0 20px}"
        "td,th{padding:10px;border:1px solid #ccc;text-align:left}table{border-collapse:collapse}"
        "pre{white-space:pre-wrap}</style>"
        f"<h1>UI verification: {result['status'].upper()}</h1>"
        f"<p>{html.escape(result['scope'])}</p><p>Duration: {result['duration_seconds']} seconds</p>"
        f"<pre>{html.escape(result.get('error', ''))}</pre>"
        '<p><a href="console.log">Console log</a> · <a href="result.json">JSON result</a></p>'
        "<table><tr><th>Check</th><th>Status</th><th>Scope notes</th><th>Error</th><th>Evidence</th></tr>"
        + "".join(rows)
        + "</table><h2>Screenshots</h2>"
        + gallery
        + "</html>\n",
        encoding="utf-8",
    )
    for check in result["checks"]:
        print(f"{check['status'].upper():6} {check['name']}")
    if result.get("error"):
        print(result["error"], file=sys.stderr)
    print(f"{result['status'].upper()}: {output / 'report.html'}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
