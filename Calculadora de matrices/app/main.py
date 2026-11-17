from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routers import matrices, operations, figuras
from app.api.routers.operations import TransformParams, transformacion_3d, morph_dona_taza
from app.models.models import MorphParams

app = FastAPI(
    title="Calculadora de Matrices API",
    description="API estructurada en capas para gestionar operaciones de matrices y transformaciones 3D.",
    version="1.1.0"
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
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Registrar routers modulares
app.include_router(matrices.router)
app.include_router(operations.router)
app.include_router(figuras.router)

# --- ALIAS DIRECTOS PARA N8N Y VISOR 3D ---
@app.post("/transformaciones/matriz")
def endpoint_transformaciones_matriz(params: TransformParams):
    """Calcula la matriz homogénea 4x4 M = T*Rz*Ry*Rx para n8n y clientes 3D."""
    return transformacion_3d(params)


@app.post("/calc/morph")
def endpoint_calc_morph(params: MorphParams):
    """Calcula la deformación topológica Dona -> Taza y su tabla resumen Markdown."""
    return morph_dona_taza(params)


INDEX = static_path / "index.html"

@app.get("/")
def index():
    return FileResponse(INDEX)
