import csv
import math
import os
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from fastapi.responses import HTMLResponse

app = FastAPI(title="3D Model & Matrix Transformation API")

# --- MITIGACIÓN OWASP: Middleware de Cabeceras de Seguridad ---
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' ws://localhost:8001 http://localhost:8000 http://localhost:8001; "
        "frame-ancestors 'none';"
    )
    if "server" in response.headers:
        del response.headers["server"]
    return response

# --- MITIGACIÓN OWASP: Restricción de CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

MODELS_DIR = Path("modelos_3d")
CSV_FILE_PATH = Path("modelo_3d.csv")
CALCULADORA_BASE_URL = os.getenv("CALCULADORA_BASE_URL", "http://host.docker.internal:8000")
CALCULADORA_API_URL = f"{CALCULADORA_BASE_URL}/operaciones/transformacion-3d"
CALCULADORA_MORPH_URL = f"{CALCULADORA_BASE_URL}/calc/morph"
CALCULADORA_FIGURAS_URL = f"{CALCULADORA_BASE_URL}/figuras"

def cargar_puntos_csv(path: Path) -> list[list[float]]:
    puntos = []
    if not path.exists():
        print(f"Advertencia: No se encontró el archivo {path}")
        return puntos

    with open(path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                puntos.append([float(row["x"]), float(row["y"]), float(row["z"])])
            except (KeyError, ValueError):
                continue
    return puntos

@app.get("/")
def read_root():
    return {"status": "online", "message": "API Modelador 3D (Render) activa"}

@app.get("/api/modelos")
def listar_modelos():
    """Retorna el listado de figuras 3D disponibles en la carpeta modelos_3d"""
    return {
        "modelos": [
            {
                "id": "dona",
                "nombre": "Toroide (Dona)",
                "icono": "🍩",
                "archivo": "dona.csv",
                "descripcion": "Superficie de revolución toroidal (10,000 vértices)"
            },
            {
                "id": "esfera",
                "nombre": "Esfera",
                "icono": "🔮",
                "archivo": "esfera.csv",
                "descripcion": "Esfera paramétrica de alta densidad (10,000 vértices)"
            },
            {
                "id": "piramide",
                "nombre": "Pirámide",
                "icono": "🔺",
                "archivo": "piramide.csv",
                "descripcion": "Pirámide de base cuadrada con caras malladas (6,530 vértices)"
            }
        ]
    }

@app.get("/api/modelo-csv")
def obtener_puntos_modelo(figura: str = "dona"):
    figura_norm = figura.strip().lower()

    mapeo = {
        "dona": "dona.csv",
        "toroide": "dona.csv",
        "toro": "dona.csv",
        "modelo_3d": "modelo_3d.csv",
        "modelo_3d_dona": "modelo_3d_dona.csv",
        "esfera": "esfera.csv",
        "modelo_3d_esfera": "modelo_3d_esfera.csv",
        "piramide": "piramide.csv",
        "pirámide": "piramide.csv",
        "modelo_3d_piramide": "modelo_3d_piramide.csv"
    }

    archivo_objetivo = mapeo.get(figura_norm, f"{figura_norm}.csv")
    path = MODELS_DIR / archivo_objetivo

    if not path.exists():
        if Path(archivo_objetivo).exists():
            path = Path(archivo_objetivo)
        elif (MODELS_DIR / "dona.csv").exists():
            path = MODELS_DIR / "dona.csv"
        elif CSV_FILE_PATH.exists():
            path = CSV_FILE_PATH

    puntos = cargar_puntos_csv(path)
    return {
        "figura": figura_norm,
        "archivo": path.name,
        "total_puntos": len(puntos),
        "vertices": puntos
    }

@app.get("/api/modelo/{figura}")
def obtener_puntos_por_figura(figura: str):
    return obtener_puntos_modelo(figura)

@app.websocket("/ws/transform")
async def websocket_transform(websocket: WebSocket):
    await websocket.accept()

    async with httpx.AsyncClient() as client:
        try:
            while True:
                data = await websocket.receive_json()

                # 1. Relevo de deformación topológica (Morph Dona -> Taza)
                if "morph" in data and isinstance(data["morph"], dict):
                    try:
                        t_val = float(data["morph"].get("t", 0.0))
                        res_val = int(data["morph"].get("resolucion", 50))
                    except (ValueError, TypeError):
                        await websocket.send_json({"status": "error", "detail": "parámetros de morph inválidos"})
                        continue
                    if not math.isfinite(t_val) or not (0.0 <= t_val <= 1.0) or not (4 <= res_val <= 100):
                        await websocket.send_json({"status": "error", "detail": "parámetros de morph fuera de rango"})
                        continue
                    resp_morph = await client.post(
                        CALCULADORA_MORPH_URL,
                        json={"t": t_val, "resolucion": res_val},
                        timeout=5.0,
                    )
                    if resp_morph.status_code == 200:
                        body = resp_morph.json()
                        await websocket.send_json({
                            "status": "ok",
                            "morph": {
                                "t": t_val,
                                "total_puntos": body.get("total_puntos", 0),
                                "vertices": body.get("vertices", []),
                            }
                        })
                    else:
                        await websocket.send_json({"status": "error", "detail": "error calculando morph"})
                    continue

                # 2. Relevo de guardado de figura con nombre
                if "guardar" in data and isinstance(data["guardar"], dict):
                    nombre = str(data["guardar"].get("nombre", "")).strip()
                    try:
                        t_val = float(data["guardar"].get("t", 0.0))
                        res_val = int(data["guardar"].get("resolucion", 50))
                    except (ValueError, TypeError):
                        await websocket.send_json({"status": "error", "detail": "parámetros inválidos"})
                        continue
                    if not nombre or len(nombre) > 60:
                        await websocket.send_json({"status": "error", "detail": "nombre de figura inválido"})
                        continue
                    resp_save = await client.post(
                        CALCULADORA_FIGURAS_URL,
                        json={"nombre": nombre, "t": t_val, "resolucion": res_val},
                        timeout=5.0,
                    )
                    if resp_save.status_code == 200:
                        await websocket.send_json({"status": "ok", "guardada": resp_save.json()})
                    else:
                        await websocket.send_json({"status": "error", "detail": "no se pudo guardar la figura"})
                    continue

                try:
                    tx = float(data.get("tx", 0.0))
                    ty = float(data.get("ty", 0.0))
                    tz = float(data.get("tz", 0.0))
                    rx = float(data.get("rx", 0.0))
                    ry = float(data.get("ry", 0.0))
                    rz = float(data.get("rz", 0.0))
                except (ValueError, TypeError):
                    continue

                # --- MITIGACIÓN: Sanitización de entradas numéricas ---
                if not all(math.isfinite(v) for v in (tx, ty, tz, rx, ry, rz)):
                    continue

                payload = {
                    "tx": tx, "ty": ty, "tz": tz,
                    "rx": rx, "ry": ry, "rz": rz
                }

                response = await client.post(
                    CALCULADORA_API_URL,
                    json=payload,
                    timeout=5.0
                )

                if response.status_code == 200:
                    matriz_resultante = response.json().get("resultado")
                    matriz_flat = [
                        float(matriz_resultante[r][c])
                        for c in range(len(matriz_resultante[0]))
                        for r in range(len(matriz_resultante))
                    ]
                    await websocket.send_json({"matrix": matriz_flat, "status": "ok"})
                else:
                    print(f"Error de Calculadora: {response.text}")

        except WebSocketDisconnect:
            print("Cliente WebSocket desconectado")
        except Exception as e:
            print(f"Error de conexión HTTP: {e}")

@app.get("/view", response_class=HTMLResponse)
def serve_viewer():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
