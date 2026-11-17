from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class MatrixCreate(BaseModel):
    nombre: Optional[str] = None
    datos: List[List[float]] = Field(..., description="Matriz bidimensional de números")

    @field_validator("datos")
    @classmethod
    def filas_parejas(cls, v):
        if not v:
            return v
        largos = [len(fila) for fila in v]
        if len(set(largos)) > 1:
            raise ValueError("Todas las filas deben tener el mismo largo")
        return v

class MatrixOut(MatrixCreate):
    id: int
