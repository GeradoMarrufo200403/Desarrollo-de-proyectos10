import csv
import math
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse


# URL del microservicio calculadora_matrices.
# En Docker Compose se resuelve por nombre de servicio (http://calculadora:8000);
# corriendo local sin Docker, la calculadora está expuesta en el puerto 8001.
CALC_URL = os.getenv("CALC_URL", "http://localhost:8001")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Un único cliente HTTP reutilizado (mantiene conexiones abiertas entre frames)
    app.state.calc = httpx.AsyncClient(base_url=CALC_URL, timeout=2.0)
    yield
    await app.state.calc.aclose()


app = FastAPI(title="3D Model & Matrix Transformation API", lifespan=lifespan)


# Habilitar CORS para permitir que Three.js se conecte sin restricciones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Ruta al archivo CSV con las coordenadas (debe estar en el mismo directorio o volumen Docker)
CSV_FILE_PATH = Path("modelo_3d.csv")


def cargar_puntos_csv(path: Path) -> list[list[float]]:
    """Lee un archivo CSV con encabezados x,y,z y retorna una lista de vertices [[x, y, z], ...]."""
    puntos = []
    if not path.exists():
        print(f"Advertencia: No se encontró el archivo {path}")
        return puntos

    with open(path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                puntos.append([
                    float(row["x"]),
                    float(row["y"]),
                    float(row["z"])
                ])
            except (KeyError, ValueError) as e:
                # Omitir filas mal formadas o vacías
                continue
    return puntos


# ---------------------------------------------------------------------------
# Figuras geométricas: todas con la misma cantidad de puntos que el CSV (10.000)
# ---------------------------------------------------------------------------

N_PUNTOS = 10000
RADIO_ESFERA = 6.0
MEDIO_LADO_CUBO = 5.0


def generar_esfera(n: int, r: float) -> list[list[float]]:
    """Esfera de Fibonacci: n puntos distribuidos uniformemente sobre la superficie.
    Cada punto i baja en 'y' de forma pareja y gira el ángulo áureo alrededor del eje Y."""
    angulo_aureo = math.pi * (3 - math.sqrt(5))
    puntos = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n          # de 1 a -1
        radio_y = math.sqrt(1 - y * y)     # radio del círculo a esa altura
        phi = i * angulo_aureo
        puntos.append([r * radio_y * math.cos(phi), r * y, r * radio_y * math.sin(phi)])
    return puntos


def generar_cubo(n: int, l: float) -> list[list[float]]:
    """n puntos sobre las 6 caras de un cubo de lado 2l, repartidos en forma pareja
    con la secuencia de baja discrepancia R2 (sin aleatoriedad, siempre el mismo resultado)."""
    g = 1.32471795724474602596  # número plástico
    a1, a2 = 1 / g, 1 / (g * g)
    puntos = []
    for i in range(n):
        cara, k = i % 6, i // 6
        eje, signo = cara // 2, (1 if cara % 2 == 0 else -1)
        u = ((0.5 + a1 * k) % 1) * 2 - 1
        v = ((0.5 + a2 * k) % 1) * 2 - 1
        punto = [u * l, v * l]
        punto.insert(eje, signo * l)       # fija la coordenada del eje de la cara
        puntos.append(punto)
    return puntos


@lru_cache
def obtener_figura(nombre: str) -> list[list[float]] | None:
    if nombre == "esfera":
        return generar_esfera(N_PUNTOS, RADIO_ESFERA)
    if nombre == "cubo":
        return generar_cubo(N_PUNTOS, MEDIO_LADO_CUBO)
    if nombre == "toroide":
        return cargar_puntos_csv(CSV_FILE_PATH)
    return None


FIGURAS = ["esfera", "cubo", "toroide"]


async def pedir_transformacion(client: httpx.AsyncClient, parametros: dict) -> list[float]:
    """Reenvía los parámetros de movimiento a calculadora_matrices, que construye
    M = T · Rz · Ry · Rx · S y la devuelve en Column-Major (16 floats) para Three.js."""
    response = await client.post("/calc/transformacion", json=parametros)
    response.raise_for_status()
    return response.json()["column_major"]


@app.get("/")
def read_root():
    """Endpoint raíz para verificar disponibilidad del servicio."""
    return {
        "status": "online",
        "message": "API de Modelo 3D activa (las matrices las calcula calculadora_matrices)",
        "calculadora": CALC_URL,
        "endpoints": {
            "figuras": "/api/figuras",
            "figura": "/api/figura/{nombre}",
            "csv_model": "/api/modelo-csv",
            "websocket": "/ws/transform",
            "viewer": "/view",
            "docs": "/docs"
        }
    }


@app.get("/api/modelo-csv")
def obtener_puntos_modelo():
    """Devuelve los vértices 3D parseados desde el archivo CSV."""
    puntos = cargar_puntos_csv(CSV_FILE_PATH)
    return {
        "total_puntos": len(puntos),
        "vertices": puntos
    }


@app.get("/api/figuras")
def listar_figuras():
    return {"figuras": FIGURAS, "puntos_por_figura": N_PUNTOS}


@app.get("/api/figura/{nombre}")
def obtener_puntos_figura(nombre: str):
    """Devuelve los vértices de una figura: esfera, cubo o toroide."""
    puntos = obtener_figura(nombre)
    if puntos is None:
        raise HTTPException(404, f"figura desconocida: {nombre}. Opciones: {', '.join(FIGURAS)}")
    return {
        "figura": nombre,
        "total_puntos": len(puntos),
        "vertices": puntos
    }


@app.websocket("/ws/transform")
async def websocket_transform(websocket: WebSocket):
    """Canal WebSocket: recibe parámetros de movimiento y devuelve la matriz 4x4 calculada por calculadora_matrices."""
    await websocket.accept()
    client: httpx.AsyncClient = websocket.app.state.calc
    try:
        while True:
            data = await websocket.receive_json()

            # Extraer traslaciones, rotaciones (grados) y escala recibidas
            parametros = {k: float(data.get(k, 1.0 if k == "escala" else 0.0))
                          for k in ("tx", "ty", "tz", "rx", "ry", "rz", "escala")}

            try:
                matrix_4x4 = await pedir_transformacion(client, parametros)
            except httpx.HTTPError as e:
                # Si la calculadora no responde, avisamos al cliente sin cortar el WebSocket
                await websocket.send_json({
                    "status": "error",
                    "detail": f"calculadora no disponible: {e.__class__.__name__}"
                })
                continue

            # Responder con la matriz procesada
            await websocket.send_json({
                "matrix": matrix_4x4,
                "status": "ok"
            })
    except WebSocketDisconnect:
        print("Cliente WebSocket desconectado")


@app.get("/view", response_class=HTMLResponse)
def serve_viewer():
    """Servidor web directo para ver la interfaz 3D."""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
