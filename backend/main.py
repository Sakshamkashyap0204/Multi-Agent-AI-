import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from models.database import init_db, db
from services.seed import seed_database
from services.websocket_manager import manager
from api.auth import router as auth_router
from api.tasks import router as tasks_router
from api.agents import router as agents_router
from api.approvals import router as approvals_router
from api.governance import router as governance_router
from api.audit import router as audit_router
from api.analytics import router as analytics_router

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and seed initial data
    try:
        await init_db()
        await seed_database(db)
    except Exception as e:
        print("[WARN] Startup database initialization note:", e)
    yield
    # Shutdown


app = FastAPI(
    title="OrchestrateAI API",
    description="Enterprise Multi-Agent Operations Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers directly
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(agents_router)
app.include_router(approvals_router)
app.include_router(governance_router)
app.include_router(audit_router)
app.include_router(analytics_router)

# Also include with /api prefix for standard enterprise api routing
app.include_router(auth_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(governance_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "OrchestrateAI Backend",
        "version": "1.0.0",
        "agents_available": [
            "planner", "research", "data_analyst", "finance",
            "compliance", "writer", "reviewer", "synthesis"
        ],
    }


@app.websocket("/ws")
async def websocket_global_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "global")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "global")
    except Exception:
        manager.disconnect(websocket, "global")


@app.websocket("/ws/{room}")
async def websocket_room_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception:
        manager.disconnect(websocket, room)


# Mount built frontend files if dist directory exists
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes or WS
        if full_path.startswith("api/") or full_path in ["health", "docs", "openapi.json"]:
            return None
        file_path = DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "name": "OrchestrateAI",
            "tagline": "Enterprise Multi-Agent Operations Platform",
            "docs": "/docs",
            "version": "1.0.0",
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

