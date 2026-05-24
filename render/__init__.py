"""Render pipeline: QThreadPool worker + helpers for off-thread mesh computation.

Per restructure-feature-subpackages-2026q2-r2 Batch 2: extracted from root-level
render_worker.py into a feature subpackage to make room for future render-pipeline
modules (cache helpers, async dispatchers, etc.).

The canonical worker class is `render.worker.MeshWorker`. Old imports via
`render_worker` still work via a Template-2 shim at the root path; they emit
DeprecationWarning.
"""
