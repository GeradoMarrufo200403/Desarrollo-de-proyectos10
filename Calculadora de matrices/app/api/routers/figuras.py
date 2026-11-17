from fastapi import APIRouter, HTTPException, Response
from typing import List
from app.models.models import FiguraMorphCreate, FiguraMorphOut
from app.repositories.matrix_repo import figura_db

router = APIRouter(prefix="/figuras", tags=["Figuras 3D Morph"])


@router.post("", response_model=FiguraMorphOut)
def guardar_figura(payload: FiguraMorphCreate):
    """Guarda o actualiza (de forma idempotente por nombre) una figura del morph Dona -> Taza."""
    return figura_db.guardar(payload.model_dump())


@router.get("", response_model=List[FiguraMorphOut])
def listar_figuras():
    """Lista todas las figuras guardadas del morph Dona -> Taza."""
    return figura_db.listar()


@router.get("/{id}", response_model=FiguraMorphOut)
def obtener_figura(id: int):
    """Obtiene una figura guardada por su ID."""
    figura = figura_db.obtener(id)
    if not figura:
        raise HTTPException(404, "Figura no encontrada")
    return figura


@router.delete("/{id}", status_code=204)
def eliminar_figura(id: int):
    """Elimina una figura guardada por su ID."""
    if not figura_db.eliminar(id):
        raise HTTPException(404, "Figura no encontrada")
    return Response(status_code=204)

