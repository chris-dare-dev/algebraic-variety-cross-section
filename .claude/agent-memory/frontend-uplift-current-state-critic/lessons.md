# Lessons — frontend-uplift-current-state-critic

- **2026-05-20 (2026q2-panel-refresh):** AI-11 unqualified-enum drift survives only in `app.py:425` (`Qt.AA_ShareOpenGLContexts`) — extend the AI-11 audit to `QApplication.setAttribute` call sites and application-attribute enum usages when reviewing any new startup/platform code, not just widget-layout callbacks.
