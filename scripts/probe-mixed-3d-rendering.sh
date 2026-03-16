#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
APP_LAUNCHER="${REPO_ROOT}/build/Slicer-build/AksaratorApp"
TRACE_SCRIPT="${REPO_ROOT}/scripts/trace_mixed_3d_rendering.py"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
DEFAULT_OUTPUT_DIR="${REPO_ROOT}/.agent/reports/render-trace-logs/${TIMESTAMP}"

mode="synthetic"
scene_path=""
view_index=0
warmup_frames=5
measured_frames=20
report_path=""
json_path=""
output_dir=""
offscreen=0
timeout_seconds=0

print_usage() {
  cat <<'EOF'
Usage:
  ./scripts/probe-mixed-3d-rendering.sh [--synthetic]
  ./scripts/probe-mixed-3d-rendering.sh --scene /absolute/path/to/scene.mrml

Options:
  --synthetic            Create and trace a synthetic scene (default)
  --scene PATH           Load and trace a specific MRML scene
  --view-index N         3D view index to trace (default: 0)
  --warmup N             Warm-up renders before sampling (default: 5)
  --frames N             Measured renders per scenario (default: 20)
  --output-dir PATH      Directory for report, JSON, and console log
  --report PATH          Explicit markdown report path
  --json PATH            Explicit JSON summary path
  --offscreen            Set QT_QPA_PLATFORM=offscreen for the launched app
  --timeout SEC          Terminate the launched app if it exceeds SEC seconds
  --help                 Show this help text
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --synthetic)
      mode="synthetic"
      shift
      ;;
    --scene)
      mode="scene"
      scene_path=${2:-}
      if [[ -z "${scene_path}" ]]; then
        echo "--scene requires a path" >&2
        exit 1
      fi
      shift 2
      ;;
    --view-index)
      view_index=${2:-}
      shift 2
      ;;
    --warmup)
      warmup_frames=${2:-}
      shift 2
      ;;
    --frames)
      measured_frames=${2:-}
      shift 2
      ;;
    --output-dir)
      output_dir=${2:-}
      shift 2
      ;;
    --report)
      report_path=${2:-}
      shift 2
      ;;
    --json)
      json_path=${2:-}
      shift 2
      ;;
    --offscreen)
      offscreen=1
      shift
      ;;
    --timeout)
      timeout_seconds=${2:-}
      shift 2
      ;;
    --help)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      print_usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -x "${APP_LAUNCHER}" ]]; then
  echo "AksaratorApp launcher not found: ${APP_LAUNCHER}" >&2
  exit 1
fi

if [[ ! -f "${TRACE_SCRIPT}" ]]; then
  echo "Trace script not found: ${TRACE_SCRIPT}" >&2
  exit 1
fi

if [[ "${mode}" == "scene" && ! -e "${scene_path}" ]]; then
  echo "Scene path does not exist: ${scene_path}" >&2
  exit 1
fi

if [[ -z "${output_dir}" ]]; then
  output_dir="${DEFAULT_OUTPUT_DIR}"
fi
mkdir -p "${output_dir}"

if [[ -z "${report_path}" ]]; then
  report_path="${output_dir}/trace-report.md"
fi

if [[ -z "${json_path}" ]]; then
  json_path="${output_dir}/trace-summary.json"
fi

console_log="${output_dir}/console.log"

echo "Output directory: ${output_dir}"
echo "Report path: ${report_path}"
echo "JSON path: ${json_path}"
echo "Console log: ${console_log}"
echo "Timeout seconds: ${timeout_seconds}"

export AIG_RENDER_TRACE_REPORT_PATH="${report_path}"
export AIG_RENDER_TRACE_JSON_PATH="${json_path}"
export AIG_RENDER_TRACE_VIEW_INDEX="${view_index}"
export AIG_RENDER_TRACE_WARMUP_FRAMES="${warmup_frames}"
export AIG_RENDER_TRACE_MEASURED_FRAMES="${measured_frames}"

if [[ "${mode}" == "synthetic" ]]; then
  export AIG_RENDER_TRACE_SYNTHETIC_SCENE=1
  unset AIG_RENDER_TRACE_SCENE_PATH
else
  export AIG_RENDER_TRACE_SYNTHETIC_SCENE=0
  export AIG_RENDER_TRACE_SCENE_PATH="${scene_path}"
fi

if [[ "${offscreen}" -eq 1 ]]; then
  export QT_QPA_PLATFORM=offscreen
fi

app_command=(
  "${APP_LAUNCHER}"
  --launcher-no-splash
  --no-splash
  --ignore-slicerrc
  --python-script "${TRACE_SCRIPT}"
)

echo "Command:" "${app_command[@]}"
if [[ "${timeout_seconds}" -gt 0 ]]; then
  timeout --signal=TERM --kill-after=10s "${timeout_seconds}s" \
    "${app_command[@]}" >"${console_log}" 2>&1
  rc=$?
else
  "${app_command[@]}" >"${console_log}" 2>&1
  rc=$?
fi

cat "${console_log}"
echo "Exit code: ${rc}"

if [[ -f "${report_path}" ]]; then
  echo "Generated report: ${report_path}"
fi
if [[ -f "${json_path}" ]]; then
  echo "Generated JSON: ${json_path}"
fi

exit "${rc}"
