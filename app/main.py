from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.api.routes import router


from contextlib import asynccontextmanager
from db.init_db import init_database
from app.services.provider_factory import create_providers
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[SYSTEM] Initializing database schema...")
    init_database()
    
    print("[SYSTEM] Checking available providers...")
    providers = create_providers()
    print(f"[SYSTEM] Available providers: {list(providers.keys())}")
    
    yield
    
    # Shutdown
    print("[SYSTEM] Shutting down...")

app = FastAPI(
    title="LinkedIn Lead Engine",
    description=(
        "AI-assisted opportunity, company, "
        "people, and public contact discovery system."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    router,
    prefix="/api",
)


# ============================================================
# ROOT / STATIC UI
# ============================================================

# Mount static directory
STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )