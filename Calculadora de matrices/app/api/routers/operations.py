from fastapi import APIRouter, HTTPException
from app.repositories.matrix_repo import matrix_db
from app.services import matrix_service
from pydantic import BaseModel
from typing import List
import math

router = APIRouter(prefix="/operaciones", tags=["Operaciones"])

@router.post("/sumar")
def sumar_matrices(id1: int, id2: int):
    m1 = matrix_db.obtener(id1)
    m2 = matrix_db.obtener(id2)

    if not m1 or not m2:
        raise HTTPException(404, "Una o ambas matrices no fueron encontradas")

    try:
        return {"resultado": matrix_service.sumar(m1["datos"], m2["datos"])}
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/multiplicar")
def multiplicar_matrices(id1: int, id2: int):
    m1 = matrix_db.obtener(id1)
    m2 = matrix_db.obtener(id2)

    if not m1 or not m2:
        raise HTTPException(404, "Una o ambas matrices no fueron encontradas")

    try:
        return {"resultado": matrix_service.multiplicar(m1["datos"], m2["datos"])}
    except ValueError as e:
        raise HTTPException(400, str(e))

class MatrizSecuencia(BaseModel):
    matrices: List[List[List[float]]]

@router.post("/multiplicar-secuencia")
def multiplicar_secuencia(payload: MatrizSecuencia):
    """Multiplica una secuencia de matrices al vuelo (sin usar la base de datos)."""
    if not payload.matrices or len(payload.matrices) < 2:
        raise HTTPException(400, "Debe enviar al menos 2 matrices")
    
    try:
        resultado = payload.matrices[0]
        for matriz in payload.matrices[1:]:
            resultado = matrix_service.multiplicar(resultado, matriz)
        return {"resultado": resultado}
    except ValueError as e:
        raise HTTPException(400, str(e))

class TransformParams(BaseModel):
    tx: float
    ty: float
    tz: float
    rx: float
    ry: float
    rz: float

@router.post("/transformaciones/matriz")
@router.post("/transformacion-3d")
def transformacion_3d(params: TransformParams):
    """Genera matrices 4x4 (Traslación * Rotación Z-Y-X) y las multiplica."""
    rad_x, rad_y, rad_z = math.radians(params.rx), math.radians(params.ry), math.radians(params.rz)
 
    Rx = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, math.cos(rad_x), -math.sin(rad_x), 0.0],
        [0.0, math.sin(rad_x), math.cos(rad_x), 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]
 
    Ry = [
        [math.cos(rad_y), 0.0, math.sin(rad_y), 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-math.sin(rad_y), 0.0, math.cos(rad_y), 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]
 
    Rz = [
        [math.cos(rad_z), -math.sin(rad_z), 0.0, 0.0],
        [math.sin(rad_z), math.cos(rad_z), 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]
 
    T = [
        [1.0, 0.0, 0.0, params.tx],
        [0.0, 1.0, 0.0, params.ty],
        [0.0, 0.0, 1.0, params.tz],
        [0.0, 0.0, 0.0, 1.0]
    ]
    
    # Multiplicar en el orden correcto: T * Rz * Ry * Rx
    res1 = matrix_service.multiplicar(Ry, Rx)
    res2 = matrix_service.multiplicar(Rz, res1)
    res3 = matrix_service.multiplicar(T, res2)
    
    # 1. Formateo visual monoespaciado en bloque de código con corchetes
    filas_txt = []
    for row in res3:
        filas_txt.append("[ " + "  ".join(f"{val:>8.4f}" for val in row) + " ]")
    matriz_bloque = "```\n" + "\n".join(filas_txt) + "\n```"

    # 2. Formato tabla Markdown (renderizable nativamente en n8n chat)
    tabla_md = "| Col 1 | Col 2 | Col 3 | Traslación |\n| :---: | :---: | :---: | :---: |\n"
    for row in res3:
        tabla_md += f"| {row[0]:.4f} | {row[1]:.4f} | {row[2]:.4f} | {row[3]:.4f} |\n"

    return {
        "resultado": res3,
        "matriz_renderizada": matriz_bloque,
        "matriz_tabla_markdown": tabla_md
    }
