from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.services.storage_client import ensure_buckets


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_buckets()
    yield


app = FastAPI(title="Planar", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Routers
from app.routers import auth, projects, files, chat, ppt  # noqa: E402

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(files.router)
app.include_router(chat.router)
app.include_router(ppt.router)


# Serve UI
UI_PATH = Path(__file__).resolve().parent.parent.parent / "ui" / "index.html"


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    if UI_PATH.exists():
        return HTMLResponse(UI_PATH.read_text())
    return HTMLResponse("<h1>Planar API</h1><p>UI not found. Visit <a href='/docs'>/docs</a> for API docs.</p>")
