from fastapi import APIRouter, HTTPException, Response
from typing import List
from app.models.models import MatrixCreate, MatrixOut
from app.repositories.matrix_repo import matrix_db

router = APIRouter(prefix="/matrices", tags=["Matrices"])

@router.post("", response_model=MatrixOut)
def crear_matriz(payload: MatrixCreate):
    return matrix_db.crear(payload.model_dump())

@router.get("", response_model=List[MatrixOut])
def listar_matrices():
    return matrix_db.listar()

@router.get("/{id}", response_model=MatrixOut)
def obtener_matriz(id: int):
    matriz = matrix_db.obtener(id)
    if not matriz:
        raise HTTPException(404, "Matriz no encontrada")
    return matriz

@router.put("/{id}", response_model=MatrixOut)
def reemplazar_matriz(id: int, payload: MatrixCreate):
    matriz = matrix_db.actualizar(id, payload.model_dump())
    if not matriz:
        raise HTTPException(404, "Matriz no encontrada")
    return matriz

@router.delete("/{id}", status_code=204)
def eliminar_matriz(id: int):
    if not matrix_db.eliminar(id):
        raise HTTPException(404, "Matriz no encontrada")
    return Response(status_code=204)

@router.get("/{id}/transpuesta")
def transponer_matriz(id: int):
    from app.services import matrix_service
    matriz = matrix_db.obtener(id)
    if not matriz:
        raise HTTPException(404, "Matriz no encontrada")
    return {"resultado": matrix_service.transponer(matriz["datos"])}

@router.get("/{id}/determinante")
def determinante_matriz(id: int):
    from app.services import matrix_service
    matriz = matrix_db.obtener(id)
    if not matriz:
        raise HTTPException(404, "Matriz no encontrada")
    try:
        return {"determinante": matrix_service.determinante(matriz["datos"])}
    except ValueError as e:
        raise HTTPException(400, str(e))
