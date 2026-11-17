from fastapi import APIRouter, HTTPException
from app.repositories.matrix_repo import matrix_db
from app.services import matrix_service

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
