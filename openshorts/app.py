"""FastAPI application entrypoint for the openshorts package.

This module exposes the FastAPI ``app`` instance used by uvicorn:

    uvicorn openshorts.app:app --host 0.0.0.0 --port 8000

The actual route handlers still live in the root-level ``app.py`` during the
restructure. A future commit will split that monolith into the planned router
modules under openshorts/routes/ (process, editing, subtitles, hooks,
translation, thumbnails, saasshorts, audio, layouts, motion_graphics, social).
Until then this module simply re-exports the existing FastAPI instance so the
Dockerfile / docker-compose entrypoint can target the package path.
"""
import os
import sys

# Make sure the repo root is on sys.path so `import app` resolves to the
# original root-level app.py rather than this package's own openshorts/app.py.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from app import app  # noqa: E402,F401
