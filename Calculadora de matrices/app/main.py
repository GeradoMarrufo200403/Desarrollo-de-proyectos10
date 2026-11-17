from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routers import matrices, operations
from app.api.routers.operations import TransformParams, transformacion_3d, morph_dona_taza
from app.models.models import MorphParams, FiguraMorphCreate, FiguraMorphOut
from app.repositories.matrix_repo import figura_db
from typing import List

app = FastAPI(
    title="Calculadora de Matrices API",
    description="API estructurada en capas para gestionar operaciones de matrices.",
    version="1.0.0"
)

# --- MITIGACIÓN OWASP: Middleware de Cabeceras de Seguridad ---
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # 1. Anti-Clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # 2. Protección contra MIME-Sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # 3. Content Security Policy (CSP): Adaptado para permitir Swagger UI en /docs
    if request.url.path in ("/docs", "/redoc", "/openapi.json"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "connect-src 'self' http://localhost:8000; "
            "frame-ancestors 'none';"
        )
    else:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' http://localhost:8000; "
            "frame-ancestors 'none';"
        )
    
    # 4. Ocultar información del servidor para evitar Fingerprinting
    if "server" in response.headers:
        del response.headers["server"]
        
    return response

# --- MITIGACIÓN OWASP: Restricción estricta de CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Registrar routers modulares
app.include_router(matrices.router)
app.include_router(operations.router)

# --- ALIAS DIRECTO PARA N8N Y VISOR ---
@app.post("/transformaciones/matriz")
def endpoint_transformaciones_matriz(params: TransformParams):
    """Calcula la matriz homogénea 4x4 M = T*Rz*Ry*Rx para n8n y clientes 3D."""
    return transformacion_3d(params)


@app.post("/calc/morph")
def endpoint_calc_morph(params: MorphParams):
    """Endpoint de deformación topológica Dona -> Taza."""
    return morph_dona_taza(params)


@app.post("/figuras", response_model=FiguraMorphOut)
def guardar_figura_morph(payload: FiguraMorphCreate):
    """Guarda una figura del morph con nombre para consultarla después."""
    return figura_db.guardar(payload.model_dump())


@app.get("/figuras", response_model=List[FiguraMorphOut])
def listar_figuras_morph():
    """Lista las figuras guardadas con nombre."""
    return figura_db.listar()


INDEX = static_path / "index.html"

@app.get("/")
def index():
    return FileResponse(INDEX)
