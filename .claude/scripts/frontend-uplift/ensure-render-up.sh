#!/usr/bin/env bash
# Verify the algebraic-variety-cross-section off-screen render pipeline is
# operational before dispatching the visual scout.  The visual scout drives
# pv.OFF_SCREEN renders of representative surfaces and reads the resulting
# PNGs — if the pipeline is broken, the scout produces zero-evidence briefs.
#
# Exits 0 on green, 1 on red.  The slash command body invokes this BEFORE
# Phase 1 dispatch as a preflight check.
#
# Usage: ensure-render-up.sh

set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

PY=""
if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PY="$REPO_ROOT/.venv/bin/python"
elif [[ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]]; then
  PY="$REPO_ROOT/.venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  cat <<'EOF' >&2
[fail] no Python interpreter found.

Expected one of:
  ./.venv/bin/python       (POSIX virtualenv)
  ./.venv/Scripts/python.exe  (Windows virtualenv)
  python3 on PATH

Create the virtualenv first:
    python3.12 -m venv .venv
    .venv/bin/activate                  # POSIX
    .venv/Scripts/Activate.ps1          # Windows PowerShell
    pip install -r requirements.txt
EOF
  exit 1
fi

TMPDIR="${TMPDIR:-/tmp}"
PROBE_PNG="$TMPDIR/avc-render-probe-$$.png"
trap 'rm -f "$PROBE_PNG"' EXIT

# Quick off-screen smoke render: instantiate one inexpensive surface and verify
# we get a non-empty PNG out the other side.  ~1.5 s wall-clock on a laptop.
if "$PY" - "$PROBE_PNG" <<'PYEOF' 2>/dev/null
import os, sys
png = sys.argv[1]
import pyvista as pv
pv.OFF_SCREEN = True
from surfaces import VARIETIES
# Pick the cheapest implicit surface for the probe — Kummer at defaults.
key = next(iter(VARIETIES["K3 surface"]))
surf = VARIETIES["K3 surface"][key]
mesh = surf.generate()
p = pv.Plotter(off_screen=True, window_size=(320, 240))
p.add_mesh(mesh, color="#9aa6c8", smooth_shading=True)
p.show(screenshot=png)
sys.exit(0 if os.path.getsize(png) > 1024 else 11)
PYEOF
then
  echo "[ok] off-screen render pipeline operational ($PY)"
  exit 0
fi

cat <<EOF >&2
[fail] off-screen render pipeline NOT operational.

The visual scout requires \`pv.OFF_SCREEN = True\` + \`pv.Plotter(off_screen=True).show(screenshot=...)\` to produce a non-empty PNG.  The smoke probe failed.

Common causes + recovery:

  1. Dependencies missing — install:
        $PY -m pip install -r requirements.txt

  2. surfaces.py import error — exercise:
        $PY -c "import surfaces; print(list(surfaces.VARIETIES))"

  3. On Linux without OpenGL — install the system GL libs:
        sudo apt-get install libgl1 libxrender1 libxext6   # Debian/Ubuntu

  4. macOS Qt+VTK GUI offscreen segfault — confirm you're using \`pv.OFF_SCREEN\` and NOT QT_QPA_PLATFORM=offscreen with a QApplication.  The visual scout pipeline never instantiates MainWindow.

Then re-invoke /frontend-uplift <ID> — init-uplift.sh is idempotent and status.sh will show phase=init ready to advance.
EOF
exit 1
