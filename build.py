#!/usr/bin/env python3
"""Small build helper for common AksaratorApp development workflows."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_BUILD_DIR = "build"
DEFAULT_BUILD_TYPE = "Debug"
DEFAULT_NUMPY_VERSION = "1.26.4"
EXT_BUILD_TARGET = "CompileTesModuleNuitkaModule"
INTRAOP_PLAN_EXTENSION_REPOSITORY = "git@github.com:dianbot0704/intraop-plan-extension.git"
INTRAOP_PLAN_EXTENSION_DIR = Path("Extensions/intraop-plan-extension")
WINDOWS_MSBUILD_PROPS = Path("scripts/windows-msbuild-short-intermediate.props")


def numpy_v1_version(value: str) -> str:
    """Validate a strict major.minor.patch NumPy version with major version 1."""
    parts = value.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise argparse.ArgumentTypeError("NumPy version must use strict major.minor.patch form, e.g. 1.26.4")

    major, minor, patch = (int(part) for part in parts)
    if major != 1:
        raise argparse.ArgumentTypeError("AksaratorApp requires NumPy major version 1")

    return f"{major}.{minor}.{patch}"


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def expand_path_arg(value: str) -> str:
    return os.path.expanduser(os.path.expandvars(value))


def print_command(command: list[str]) -> None:
    print(f"$ {shlex.join(command)}", flush=True)


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
    print_command(command)
    try:
        return subprocess.run(command, cwd=cwd, env=env, check=False).returncode
    except FileNotFoundError:
        print(f"error: executable not found: {command[0]}", file=sys.stderr)
        return 127


def run_capture(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def resolve_build_dir(repo_root: Path, build_dir: str) -> Path:
    path = Path(expand_path_arg(build_dir))
    if not path.is_absolute():
        path = repo_root / path
    return path


def confirm_delete(path: Path) -> bool:
    reply = input(f"Delete build directory '{path}'? [y/N] ").strip().lower()
    return reply in {"y", "yes"}


def configure(args: argparse.Namespace, repo_root: Path) -> int:
    build_dir = resolve_build_dir(repo_root, args.build_dir)
    aimposition_archive: Path | None = None
    if args.aimposition_archive:
        aimposition_archive = Path(expand_path_arg(args.aimposition_archive))
        if not aimposition_archive.is_absolute():
            aimposition_archive = repo_root / aimposition_archive
        aimposition_archive = aimposition_archive.resolve()
        if not aimposition_archive.is_file():
            print(f"error: AimPosition archive not found: {aimposition_archive}", file=sys.stderr)
            return 2

    if args.fresh and build_dir.exists():
        if not build_dir.is_dir():
            print(f"error: --fresh target exists but is not a directory: {build_dir}", file=sys.stderr)
            return 2
        if not args.yes and not confirm_delete(build_dir):
            print("Fresh configure cancelled.")
            return 1
        shutil.rmtree(build_dir)

    command = [
        args.cmake,
        "-B",
        str(build_dir),
        "-S",
        ".",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        f"-DSlicer_USE_SYSTEM_OpenSSL={'OFF' if args.no_system_openssl else 'ON'}",
        f"-DSlicer_BUILD_WEBENGINE_SUPPORT={'OFF' if args.no_webengine else 'ON'}",
        f"-DCMAKE_BUILD_TYPE={args.build_type}",
        "-DAksaratorApp_PIN_NUMPY=ON",
        f"-DAksaratorApp_NUMPY_VERSION={args.numpy_version}",
    ]

    if args.cmake_prefix_path:
        command.append(f"-DCMAKE_PREFIX_PATH={expand_path_arg(args.cmake_prefix_path)}")
    if aimposition_archive is not None:
        command.append(f"-DAksaratorApp_AIMPOSITION_ARCHIVE={aimposition_archive}")

    return run(command, cwd=repo_root)


def append_build_options(command: list[str], args: argparse.Namespace) -> None:
    if args.config:
        command.extend(["--config", args.config])
    if args.parallel:
        command.extend(["--parallel", str(args.parallel)])


def build_environment(repo_root: Path, build_dir: Path) -> dict[str, str] | None:
    if os.name != "nt":
        return None

    env = os.environ.copy()
    env["ForceImportBeforeCppTargets"] = str(repo_root / WINDOWS_MSBUILD_PROPS)
    env["AksaratorAppMSBuildIntermediateRoot"] = str(build_dir / "msbuild-int")
    return env


def build(args: argparse.Namespace, repo_root: Path) -> int:
    build_dir = resolve_build_dir(repo_root, args.build_dir)
    command = [args.cmake, "--build", str(build_dir)]
    if args.target:
        command.extend(["--target", args.target])
    append_build_options(command, args)
    return run(command, cwd=repo_root, env=build_environment(repo_root, build_dir))


def ext_build(args: argparse.Namespace, repo_root: Path) -> int:
    build_dir = resolve_build_dir(repo_root, args.build_dir)
    slicer_build_dir = build_dir / "Slicer-build"
    command = [args.cmake, "--build", str(slicer_build_dir), "--target", EXT_BUILD_TARGET]
    append_build_options(command, args)
    return run(command, cwd=repo_root, env=build_environment(repo_root, build_dir))


def git_capture(git: str, git_args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return run_capture([git, *git_args], cwd=cwd)


def git_run(git: str, git_args: list[str], *, cwd: Path) -> int:
    return run([git, *git_args], cwd=cwd)


def is_git_worktree(git: str, path: Path) -> bool:
    result = git_capture(git, ["-C", str(path), "rev-parse", "--is-inside-work-tree"], cwd=path.parent)
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_origin_url(git: str, path: Path) -> str | None:
    result = git_capture(git, ["-C", str(path), "remote", "get-url", "origin"], cwd=path.parent)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def checkout_extension_branch(git: str, extension_dir: Path, branch: str) -> int:
    if git_run(git, ["-C", str(extension_dir), "fetch", "origin"], cwd=extension_dir.parent) != 0:
        return 1

    local_branch = git_capture(
        git,
        ["-C", str(extension_dir), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=extension_dir.parent,
    )
    if local_branch.returncode == 0:
        return git_run(git, ["-C", str(extension_dir), "checkout", branch], cwd=extension_dir.parent)

    remote_branch = git_capture(
        git,
        ["-C", str(extension_dir), "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        cwd=extension_dir.parent,
    )
    if remote_branch.returncode != 0:
        print(f"error: branch not found on origin: {branch}", file=sys.stderr)
        return 1

    return git_run(
        git,
        ["-C", str(extension_dir), "checkout", "-b", branch, "--track", f"origin/{branch}"],
        cwd=extension_dir.parent,
    )


def ext_clone(args: argparse.Namespace, repo_root: Path) -> int:
    extension_dir = repo_root / INTRAOP_PLAN_EXTENSION_DIR
    extension_parent = extension_dir.parent
    extension_parent.mkdir(parents=True, exist_ok=True)

    git = args.git
    if shutil.which(git) is None:
        print(f"error: executable not found: {git}", file=sys.stderr)
        return 127

    if extension_dir.exists() or extension_dir.is_symlink():
        if not extension_dir.is_dir():
            print(f"error: extension path exists but is not a directory: {extension_dir}", file=sys.stderr)
            return 2
        if not is_git_worktree(git, extension_dir):
            print(f"error: extension path exists but is not a git repository: {extension_dir}", file=sys.stderr)
            return 2

        origin_url = get_origin_url(git, extension_dir)
        if origin_url != INTRAOP_PLAN_EXTENSION_REPOSITORY:
            print(
                "error: extension repository has unexpected origin URL:\n"
                f"  path: {extension_dir}\n"
                f"  expected: {INTRAOP_PLAN_EXTENSION_REPOSITORY}\n"
                f"  actual: {origin_url or '<missing>'}",
                file=sys.stderr,
            )
            return 2

        print(f"Extension already present at {extension_dir}")
        if args.branch:
            return checkout_extension_branch(git, extension_dir, args.branch)
        return 0

    command = [git, "clone"]
    if args.branch:
        command.extend(["--branch", args.branch])
    command.extend([INTRAOP_PLAN_EXTENSION_REPOSITORY, str(extension_dir)])
    return run(command, cwd=repo_root)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configure and build common AksaratorApp development targets.",
    )
    parser.add_argument(
        "--build-dir",
        default=DEFAULT_BUILD_DIR,
        help=f"build directory relative to the repository root unless absolute (default: {DEFAULT_BUILD_DIR})",
    )
    parser.add_argument("--cmake", default="cmake", help="CMake executable to run (default: cmake)")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    configure_parser = subparsers.add_parser("configure", help="configure the debug build directory")
    configure_parser.add_argument("--fresh", action="store_true", help="delete the build directory before configuring")
    configure_parser.add_argument("--yes", action="store_true", help="do not prompt before deleting with --fresh")
    configure_parser.add_argument(
        "--cmake-prefix-path",
        help="optional CMAKE_PREFIX_PATH; shell variables and ~ are expanded",
    )
    configure_parser.add_argument(
        "--no-system-openssl",
        action="store_true",
        help="configure with Slicer_USE_SYSTEM_OpenSSL=OFF instead of the default ON",
    )
    configure_parser.add_argument(
        "--no-webengine",
        action="store_true",
        help="configure with Slicer_BUILD_WEBENGINE_SUPPORT=OFF when Qt WebEngine is unavailable",
    )
    configure_parser.add_argument(
        "--numpy-version",
        default=DEFAULT_NUMPY_VERSION,
        type=numpy_v1_version,
        help=f"pinned NumPy 1.x version in major.minor.patch form (default: {DEFAULT_NUMPY_VERSION})",
    )
    configure_parser.add_argument(
        "--build-type",
        default=DEFAULT_BUILD_TYPE,
        help=f"CMAKE_BUILD_TYPE value for single-config generators (default: {DEFAULT_BUILD_TYPE})",
    )
    configure_parser.add_argument(
        "--aimposition-archive",
        help="optional ZIP archive containing the Windows AimPosition312.pyd runtime",
    )
    configure_parser.set_defaults(func=configure)

    build_parser = subparsers.add_parser("build", help="build the configured project")
    build_parser.add_argument("--config", help="configuration for multi-config generators, e.g. Debug")
    build_parser.add_argument("--parallel", type=positive_int, help="number of parallel build jobs")
    build_parser.add_argument("--target", help="optional CMake build target, e.g. PACKAGE")
    build_parser.set_defaults(func=build)

    ext_build_parser = subparsers.add_parser("ext-build", help="build the compiled intraop planner extension target")
    ext_build_parser.add_argument("--config", help="configuration for multi-config generators, e.g. Debug")
    ext_build_parser.add_argument("--parallel", type=positive_int, help="number of parallel build jobs")
    ext_build_parser.set_defaults(func=ext_build)

    ext_clone_parser = subparsers.add_parser("ext-clone", help="clone or prepare the intraop planner extension")
    ext_clone_parser.add_argument("--branch", help="optional branch to clone or checkout")
    ext_clone_parser.add_argument("--git", default="git", help="Git executable to run (default: git)")
    ext_clone_parser.set_defaults(func=ext_clone)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    repo_root = Path(__file__).resolve().parent
    return args.func(args, repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
