#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"
APP_LAUNCHER="${REPO_ROOT}/build/Slicer-build/AksaratorApp"
SESSION_RENDER_TRACE=0
SESSION_RENDER_TRACE_OUTPUT_DIR=""

APP_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-render-trace)
      SESSION_RENDER_TRACE=1
      shift
      ;;
    --session-render-trace-output-dir)
      SESSION_RENDER_TRACE_OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    *)
      APP_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ! -x "${APP_LAUNCHER}" ]]; then
  echo "AksaratorApp launcher not found or not executable: ${APP_LAUNCHER}" >&2
  echo "Build the project first (see BUILD.md)." >&2
  exit 1
fi

# Source module directories used for fast scripted-module iteration.
MODULE_PATHS=(
  "${REPO_ROOT}/Modules/Scripted/Home"
  "${REPO_ROOT}/Modules/Scripted/SessionRenderTrace"
)

EXISTING_MODULE_PATHS=()
for module_path in "${MODULE_PATHS[@]}"; do
  if [[ -d "${module_path}" ]]; then
    EXISTING_MODULE_PATHS+=("${module_path}")
  fi
done

if [[ ${#EXISTING_MODULE_PATHS[@]} -eq 0 ]]; then
  echo "No configured module source directories were found." >&2
  exit 1
fi

MODULE_PATHS_ENV=""
for module_path in "${EXISTING_MODULE_PATHS[@]}"; do
  if [[ -z "${MODULE_PATHS_ENV}" ]]; then
    MODULE_PATHS_ENV="${module_path}"
  else
    MODULE_PATHS_ENV="${MODULE_PATHS_ENV}:${module_path}"
  fi
done

export AKSARATOR_DEV_MODULE_PATHS="${MODULE_PATHS_ENV}"
if [[ "${SESSION_RENDER_TRACE}" -eq 1 ]]; then
  export AKSARATOR_SESSION_RENDER_TRACE=1
  if [[ -n "${SESSION_RENDER_TRACE_OUTPUT_DIR}" ]]; then
    export AKSARATOR_SESSION_RENDER_TRACE_OUTPUT_DIR="${SESSION_RENDER_TRACE_OUTPUT_DIR}"
  fi
fi

PYTHON_INIT_CODE=$(cat <<'PYCODE'
import os

import qt

settings = qt.QSettings()
settings.setValue("Developer/DeveloperMode", "true")

raw_paths = os.environ.get("AKSARATOR_DEV_MODULE_PATHS", "")
source_paths = [path for path in raw_paths.split(os.pathsep) if path]

existing_paths = settings.value("Modules/AdditionalPaths", [])
if isinstance(existing_paths, str):
    existing_paths = [existing_paths]
elif existing_paths is None:
    existing_paths = []

for source_path in source_paths:
    if source_path not in existing_paths:
        existing_paths.append(source_path)

settings.setValue("Modules/AdditionalPaths", existing_paths)
settings.sync()
PYCODE
)

exec "${APP_LAUNCHER}" \
  --additional-module-paths "${EXISTING_MODULE_PATHS[@]}" \
  --python-code "${PYTHON_INIT_CODE}" \
  "${APP_ARGS[@]}"
