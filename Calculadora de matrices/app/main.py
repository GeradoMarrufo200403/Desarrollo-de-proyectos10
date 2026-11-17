from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routers import matrices, operations

app = FastAPI(
    title="Calculadora de Matrices API",
    description="API estructurada en capas para gestionar operaciones de matrices.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# La carpeta static ahora está un nivel arriba de app (en la raíz)
static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Registrar los routers modulares
app.include_router(matrices.router)
app.include_router(operations.router)

INDEX = static_path / "index.html"

@app.get("/")
def index():
    return FileResponse(INDEX)
