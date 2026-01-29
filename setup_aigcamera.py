#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

CANDIDATE_NAMES = ("AimPosition312_noOpenCV.so", "AimPosition312.so")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy AimPosition shared object into aigcamera/_native as AimPosition312.so for development."
        )
    )
    parser.add_argument(
        "source_dir",
        type=Path,
        help="Directory containing AimPosition312_noOpenCV.so or AimPosition312.so.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search recursively under the source directory for the library.",
    )
    return parser.parse_args()


def find_candidates(source_dir: Path, recursive: bool) -> dict[str, list[Path]]:
    matches: dict[str, list[Path]] = {}
    for name in CANDIDATE_NAMES:
        if recursive:
            paths = [path for path in source_dir.rglob(name) if path.is_file()]
        else:
            path = source_dir / name
            paths = [path] if path.is_file() else []
        matches[name] = sorted(paths)
    return matches


def prompt_choice(prompt: str, options: list[str]) -> str:
    print(prompt)
    for index, option in enumerate(options, start=1):
        print(f"{index}) {option}")
    while True:
        response = input(f"Select [1-{len(options)}]: ").strip()
        if response.isdigit():
            selection = int(response)
            if 1 <= selection <= len(options):
                return options[selection - 1]
        print("Invalid selection. Please choose a number from the list.")


def prompt_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{hint}]: ").strip().lower()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


def relative_display(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def select_candidate(matches: dict[str, list[Path]], source_dir: Path) -> Path:
    names_with_matches = [name for name, paths in matches.items() if paths]
    if not names_with_matches:
        raise SystemExit("No AimPosition shared object found in the provided directory.")

    if len(names_with_matches) > 1:
        selection = prompt_choice(
            "Multiple candidate filenames found. Choose which library to use:",
            names_with_matches,
        )
    else:
        selection = names_with_matches[0]

    selected_paths = matches[selection]
    if len(selected_paths) == 1:
        return selected_paths[0]

    options = [relative_display(path, source_dir) for path in selected_paths]
    chosen = prompt_choice("Multiple matches found. Choose the path to copy:", options)
    return selected_paths[options.index(chosen)]


def main() -> int:
    args = parse_args()
    source_dir = args.source_dir.expanduser()
    if not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")

    matches = find_candidates(source_dir, args.recursive)
    selected_path = select_candidate(matches, source_dir)

    repo_root = Path(__file__).resolve().parent
    target_dir = repo_root / "Python" / "aigcamera" / "src" / "aigcamera" / "_native"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "AimPosition312.so"

    if target_path.exists():
        if not prompt_yes_no(f"{target_path} already exists. Overwrite?", default=False):
            print("Copy skipped.")
            return 0

    shutil.copy2(selected_path, target_path)
    print(f"Copied {selected_path} -> {target_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
