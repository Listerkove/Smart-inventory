from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .api.routes import dashboard
from .api.routes import auth, products, inventory, sales
from .core.config import settings
from .api.routes import replenishment
from .api.routes import reports
from .api.routes import integration
from .api.routes import admin



app = FastAPI(
    title="Smart Inventory System API",
    version="1.0.0",
    description="Automated stock tracking and predictive replenishment"
)

# ----------------------------------------------------------------------
# ✅ CRITICAL: Handle OPTIONS preflight requests BEFORE any other logic
#    This MUST be the FIRST middleware.
# ----------------------------------------------------------------------
@app.middleware("http")
async def options_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response()
        origin = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    return await call_next(request)

# ----------------------------------------------------------------------
# ✅ CORS middleware (backup – still useful for normal responses)
# ----------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development – tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------
# ✅ Include all API routers
# ----------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(dashboard.router)
app.include_router(replenishment.router)
app.include_router(reports.router)
app.include_router(integration.router)
app.include_router(admin.router)


# ----------------------------------------------------------------------
# ✅ Serve static frontend files (HTML, CSS, JS)
# ----------------------------------------------------------------------
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

# ----------------------------------------------------------------------
# ✅ Health check endpoint
# ----------------------------------------------------------------------
@app.get("/api/health")
def health_check():
    return {"status": "ok", "database": settings.DB_NAME}