#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
VTK_PROBE="${REPO_ROOT}/build/VTK-build/bin/vtkProbeOpenGLVersion-9.5"
APP_LAUNCHER="${REPO_ROOT}/build/Slicer-build/AksaratorApp"
APP_SCRIPT="${REPO_ROOT}/scripts/print_opengl_capabilities.py"
LOG_ROOT="${REPO_ROOT}/.agent/reports/probe-logs/$(date -u +%Y%m%d_%H%M%S)"

mkdir -p "${LOG_ROOT}"

print_usage() {
  cat <<'EOF'
Usage:
  ./scripts/probe-gpu-rendering.sh <mode>

Modes:
  host
  vtk-default
  vtk-egl
  vtk-x
  app-default
  app-nvidia
  all
EOF
}

print_header() {
  local label=$1
  printf '\n### %s ###\n' "${label}"
}

print_command() {
  printf 'Command:'
  for arg in "$@"; do
    printf ' %q' "${arg}"
  done
  printf '\n'
}

classify_output() {
  local logfile=$1

  if grep -Eq 'llvmpipe' "${logfile}"; then
    printf 'Mesa llvmpipe'
    return
  fi
  if grep -Eq 'OpenGL vendor string:[[:space:]]+NVIDIA Corporation|OpenGL renderer string:[[:space:]].*NVIDIA' "${logfile}"; then
    printf 'NVIDIA'
    return
  fi
  if grep -Eq 'OpenGL renderer string:[[:space:]].*(AMD|Radeon)|OpenGL vendor string:[[:space:]]+(AMD|ATI)' "${logfile}"; then
    printf 'AMD'
    return
  fi
  if grep -Eq 'bad X server connection|could not connect to display|Can.t open display|Could not load the Qt platform plugin "xcb"|no Qt platform plugin could be initialized' "${logfile}"; then
    printf 'startup blocked'
    return
  fi
  printf 'unclassified'
}

run_probe() {
  local slug=$1
  local label=$2
  shift 2

  local logfile="${LOG_ROOT}/${slug}.log"
  local rc=0

  print_header "${label}"
  print_command "$@"
  "$@" >"${logfile}" 2>&1 || rc=$?
  cat "${logfile}"
  printf 'Exit code: %s\n' "${rc}"
  printf 'Classification: %s\n' "$(classify_output "${logfile}")"
  printf 'Log file: %s\n' "${logfile}"
}

run_optional_capture() {
  local slug=$1
  local label=$2
  shift 2

  local logfile="${LOG_ROOT}/${slug}.log"
  local rc=0

  print_header "${label}"
  print_command "$@"
  "$@" >"${logfile}" 2>&1 || rc=$?
  cat "${logfile}"
  printf 'Exit code: %s\n' "${rc}"
  printf 'Log file: %s\n' "${logfile}"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

run_host_checks() {
  if have_cmd lspci; then
    if have_cmd rg; then
      run_optional_capture host_lspci "Host PCI graphics devices" bash -lc 'lspci | rg -i "vga|3d|display"'
    else
      run_optional_capture host_lspci "Host PCI graphics devices" bash -lc 'lspci | grep -Ei "vga|3d|display"'
    fi
  else
    print_header "Host PCI graphics devices"
    printf 'lspci: not installed\n'
  fi

  if have_cmd nvidia-smi; then
    run_optional_capture host_nvidia_smi "NVIDIA-SMI" nvidia-smi -L
  else
    print_header "NVIDIA-SMI"
    printf 'nvidia-smi: not installed\n'
  fi

  if have_cmd lsmod; then
    if have_cmd rg; then
      run_optional_capture host_lsmod "Loaded NVIDIA kernel modules" bash -lc 'lsmod | rg "nvidia|nvidia_drm"'
    else
      run_optional_capture host_lsmod "Loaded NVIDIA kernel modules" bash -lc 'lsmod | grep -E "nvidia|nvidia_drm"'
    fi
  else
    print_header "Loaded NVIDIA kernel modules"
    printf 'lsmod: not installed\n'
  fi

  if have_cmd xrandr; then
    run_optional_capture host_xrandr "X providers" xrandr --listproviders
  else
    print_header "X providers"
    printf 'xrandr: not installed\n'
  fi

  if have_cmd glxinfo; then
    run_optional_capture host_glxinfo "GLX summary" glxinfo -B
  else
    print_header "GLX summary"
    printf 'glxinfo: not installed\n'
  fi

  if have_cmd eglinfo; then
    run_optional_capture host_eglinfo "EGL summary" eglinfo
  else
    print_header "EGL summary"
    printf 'eglinfo: not installed\n'
  fi
}

run_vtk_default() {
  run_probe vtk_default "VTK probe (default backend selection)" "${VTK_PROBE}"
}

run_vtk_egl() {
  run_probe vtk_egl "VTK probe (forced EGL render window)" env VTK_DEFAULT_OPENGL_WINDOW=vtkEGLRenderWindow "${VTK_PROBE}"
}

run_vtk_x() {
  run_probe vtk_x "VTK probe (forced X render window)" env VTK_DEFAULT_OPENGL_WINDOW=vtkXOpenGLRenderWindow "${VTK_PROBE}"
}

run_app_default() {
  run_probe \
    app_default \
    "AksaratorApp probe (default environment)" \
    "${APP_LAUNCHER}" \
    --launcher-no-splash \
    --no-splash \
    --ignore-slicerrc \
    --python-script "${APP_SCRIPT}"
}

run_app_nvidia() {
  run_probe \
    app_nvidia \
    "AksaratorApp probe (NVIDIA offload environment)" \
    env \
    __NV_PRIME_RENDER_OFFLOAD=1 \
    __GLX_VENDOR_LIBRARY_NAME=nvidia \
    "${APP_LAUNCHER}" \
    --launcher-no-splash \
    --no-splash \
    --ignore-slicerrc \
    --python-script "${APP_SCRIPT}"
}

mode=${1:-}
if [[ -z "${mode}" ]]; then
  print_usage
  exit 1
fi

case "${mode}" in
  host)
    run_host_checks
    ;;
  vtk-default)
    run_vtk_default
    ;;
  vtk-egl)
    run_vtk_egl
    ;;
  vtk-x)
    run_vtk_x
    ;;
  app-default)
    run_app_default
    ;;
  app-nvidia)
    run_app_nvidia
    ;;
  all)
    run_host_checks
    run_vtk_default
    run_vtk_egl
    run_vtk_x
    run_app_default
    run_app_nvidia
    ;;
  *)
    print_usage
    exit 1
    ;;
esac

printf '\nLogs saved under: %s\n' "${LOG_ROOT}"
