import csv
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import httpx
import numpy as np
from fastapi.responses import HTMLResponse
 
app = FastAPI(title="3D Model & Matrix Transformation API")
 
# Habilitar CORS para permitir que Three.js se conecte sin restricciones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
MODELS_DIR = Path("modelos_3d")
CSV_FILE_PATH = Path("modelo_3d.csv")
# Ahora apuntamos al nuevo endpoint de la calculadora que arma y multiplica las matrices
CALCULADORA_API_URL = "http://host.docker.internal:8000/operaciones/transformacion-3d"
 
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
    
    # Mapeo de nombres o alternativas comunes
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
    
    # Si no existe en modelos_3d, buscar en la raíz
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
    
    # Cliente HTTP asíncrono para comunicarnos con la API Calculadora de Matrices
    async with httpx.AsyncClient() as client:
        try:
            while True:
                data = await websocket.receive_json()
    
                # Extraemos los datos recibidos del frontend
                payload = {
                    "tx": float(data.get("tx", 0.0)),
                    "ty": float(data.get("ty", 0.0)),
                    "tz": float(data.get("tz", 0.0)),
                    "rx": float(data.get("rx", 0.0)),
                    "ry": float(data.get("ry", 0.0)),
                    "rz": float(data.get("rz", 0.0))
                }
    
                # Hacemos POST a la Calculadora enviando SOLAMENTE los parámetros,
                # para que la calculadora sea la encargada de armar las matrices y multiplicarlas.
                response = await client.post(
                    CALCULADORA_API_URL, 
                    json=payload,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    matriz_resultante = response.json().get("resultado")
                    
                    # Transponer (.T) a Column-Major order y aplanar a lista de 16 floats para Three.js
                    M = np.array(matriz_resultante)
                    matriz_flat = M.T.flatten().tolist()
    
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
