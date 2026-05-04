#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

NUITKA_OUTPUT_SUFFIXES = {".so", ".pyd", ".dll"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install and Nuitka-compile the aigcamera package root and its modules."
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable used to run pip and Nuitka.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Path to the aigcamera repository root.",
    )
    parser.add_argument(
        "--build-root",
        type=Path,
        required=True,
        help="Directory used to keep Nuitka build artifacts.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        required=True,
        help="Writable Nuitka cache directory.",
    )
    parser.add_argument(
        "--compile-with-nuitka",
        action="store_true",
        help="Compile the aigcamera package root and Python modules after installation.",
    )
    return parser.parse_args()


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=env)


def installed_site_packages(python_executable: str) -> Path:
    command = [
        python_executable,
        "-c",
        "import sysconfig; print(sysconfig.get_path('platlib'))",
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return Path(result.stdout.strip())


def compile_nuitka_artifact(
    python_executable: str,
    source_path: Path,
    output_dir: Path,
    cache_dir: Path,
    *,
    target_stem: str,
    extra_args: list[str] | None = None,
) -> Path:
    env = os.environ.copy()
    env["NUITKA_CACHE_DIR"] = str(cache_dir)
    env["CCACHE_DISABLE"] = "1"

    for existing_file in output_dir.glob(f"{target_stem}*"):
        if existing_file.is_file() and existing_file.suffix in NUITKA_OUTPUT_SUFFIXES:
            existing_file.unlink()

    command = [
        python_executable,
        "-m",
        "nuitka",
        "--module",
        "--nofollow-imports",
        f"--output-dir={output_dir}",
    ]
    if extra_args is not None:
        command.extend(extra_args)
    command.append(str(source_path))

    run_command(command, env=env)

    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.stem.startswith(target_stem) and path.suffix in NUITKA_OUTPUT_SUFFIXES
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected one compiled artifact for {source_path}, found {len(candidates)}"
        )
    return candidates[0]


def main() -> int:
    args = parse_args()
    python_executable = args.python_executable
    source_root = args.source_root.resolve()
    build_root = args.build_root.resolve()
    cache_dir = args.cache_dir.resolve()

    if not source_root.is_dir():
        raise SystemExit(f"Source root not found: {source_root}")

    build_root.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    install_command = [
        python_executable,
        "-m",
        "pip",
        "install",
        "--no-build-isolation",
        "--no-deps",
        "--force-reinstall",
        "--no-cache-dir",
        str(source_root),
    ]
    run_command(install_command)

    if not args.compile_with_nuitka:
        return 0

    site_packages_root = installed_site_packages(python_executable)
    package_install_root = site_packages_root / "aigcamera"
    package_source_root = source_root / "src" / "aigcamera"

    if not package_source_root.is_dir():
        raise SystemExit(f"Package source root not found: {package_source_root}")

    package_build_root = build_root / "package"
    package_build_root.mkdir(parents=True, exist_ok=True)

    compiled_package = compile_nuitka_artifact(
        python_executable=python_executable,
        source_path=package_source_root,
        output_dir=package_build_root,
        cache_dir=cache_dir,
        target_stem=package_source_root.name,
        extra_args=["--include-package=aigcamera"],
    )
    shutil.copy2(compiled_package, site_packages_root / compiled_package.name)
    init_source = package_install_root / "__init__.py"
    if init_source.exists():
        init_source.unlink()

    module_sources = sorted(path for path in package_source_root.rglob("*.py") if path.name != "__init__.py")

    for source_file in module_sources:
        relative_path = source_file.relative_to(package_source_root)
        module_dir = relative_path.parent
        build_dir = build_root / module_dir
        install_dir = package_install_root / module_dir
        build_dir.mkdir(parents=True, exist_ok=True)
        install_dir.mkdir(parents=True, exist_ok=True)

        compiled_file = compile_nuitka_artifact(
            python_executable=python_executable,
            source_path=source_file,
            output_dir=build_dir,
            cache_dir=cache_dir,
            target_stem=source_file.stem,
        )
        shutil.copy2(compiled_file, install_dir / compiled_file.name)
        source_install_file = install_dir / source_file.name
        if source_install_file.exists():
            source_install_file.unlink()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
