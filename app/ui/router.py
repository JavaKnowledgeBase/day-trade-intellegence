"""Routes that serve the built-in operator console and its static assets."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

STATIC_DIR = Path(__file__).resolve().parent / "static"


@router.get("/console")
def console_index() -> FileResponse:
    """Serve the operator console entry page for local and demo environments."""
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/console/styles.css")
def console_styles() -> FileResponse:
    """Serve the operator console stylesheet."""
    return FileResponse(STATIC_DIR / "styles.css", media_type="text/css")


@router.get("/console/app.js")
def console_script() -> FileResponse:
    """Serve the operator console JavaScript bundle."""
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")
