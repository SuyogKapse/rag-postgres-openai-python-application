from pathlib import Path
import os
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount, Route, Router

# Fixed path
static_dir = Path("/app/backend/static")
assets_dir = static_dir / "assets"

# Create dirs if missing
os.makedirs(assets_dir, exist_ok=True)


async def index(request):
    index_file = static_dir / "index.html"

    print("INDEX PATH:", index_file)
    print("INDEX EXISTS:", index_file.exists())

    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html NOT FOUND")

    return FileResponse(index_file)


async def favicon(request):
    favicon_file = static_dir / "favicon.ico"

    print("FAVICON PATH:", favicon_file)
    print("FAVICON EXISTS:", favicon_file.exists())

    if favicon_file.exists():
        return FileResponse(favicon_file)

    raise HTTPException(status_code=404, detail="favicon not found")


router = Router(
    routes=[
        # ✅ Static assets MUST come before SPA fallback
        Mount("/assets", app=StaticFiles(directory=assets_dir), name="static_assets"),

        Route("/favicon.ico", endpoint=favicon),
        Route("/", endpoint=index),

        # ✅ SPA fallback LAST
        Route("/{full_path:path}", endpoint=index),
    ]
)