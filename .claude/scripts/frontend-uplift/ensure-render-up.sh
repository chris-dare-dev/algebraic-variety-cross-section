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

# The Python heredoc probes below import `surfaces` and `appearance_panel` —
# both live at the repo root.  Running this script from any other CWD (e.g.
# from an agent's worktree dispatch, from /tmp, or from a parent shell that
# chdir'd elsewhere) would cause ModuleNotFoundError before the smoke probe
# can fail meaningfully.  cd to the repo root so the imports resolve.
cd "$REPO_ROOT"

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
  :  # off-screen surface pipeline ok — fall through to the panel-chrome probe
else
  cat <<EOF >&2
[fail] off-screen surface-render pipeline NOT operational.

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
fi

# --- Tier 1 panel-chrome probe ------------------------------------------------
# The panel-chrome scout grabs the three QWidget panels under
# QT_QPA_PLATFORM=offscreen.  AI-3 forbids MainWindow under offscreen because
# its embedded QtInteractor segfaults; pure-Qt panels DO NOT host QtInteractor
# and are safe.  Smoke-probe one panel here so a panel-chrome breakage shows
# up at preflight, not deep inside the visual scout.
PROBE_PANEL_PNG="$TMPDIR/avc-panel-probe-$$.png"
trap 'rm -f "$PROBE_PNG" "$PROBE_PANEL_PNG"' EXIT

if QT_QPA_PLATFORM=offscreen "$PY" - "$PROBE_PANEL_PNG" <<'PYEOF' 2>/dev/null
import os, sys
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from appearance_panel import AppearancePanel  # safe: no QtInteractor inside

app = QApplication.instance() or QApplication([sys.argv[0]])
w = AppearancePanel(get_actor=lambda: None, get_plotter=lambda: MagicMock())
w.resize(QSize(320, 720))
w.show()
app.processEvents()
pix = w.grab()
ok = (not pix.isNull()) and pix.save(sys.argv[1])
sys.exit(0 if ok and os.path.getsize(sys.argv[1]) > 1024 else 12)
PYEOF
then
  echo "[ok] off-screen surface + panel-chrome pipelines operational ($PY)"
  exit 0
fi

cat <<EOF >&2
[fail] panel-chrome capture NOT operational.

The off-screen surface pipeline succeeded, but constructing AppearancePanel
under \`QT_QPA_PLATFORM=offscreen\` + \`QWidget.grab()\` failed.  This is
allowed under AI-3 (pure-Qt panels host no VTK GL context); something else
broke.

Recovery:

  1. PySide6 install state — exercise:
        $PY -c "from PySide6.QtWidgets import QApplication; print('ok')"

  2. Panel module import — exercise:
        $PY -c "from appearance_panel import AppearancePanel; print('ok')"

  3. If a panel constructor signature drifted (e.g. AppearancePanel now takes
     a different callable shape), update render-panel-chrome.py to match.

Then re-invoke /frontend-uplift <ID>.
EOF
exit 1
