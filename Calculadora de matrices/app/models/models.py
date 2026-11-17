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


class MorphParams(BaseModel):
    t: float = Field(0.0, ge=0.0, le=1.0, description="Factor de deformación: 0.0 = Dona, 1.0 = Taza")
    resolucion: int = Field(50, ge=4, le=100, description="Resolución por eje (genera resolucion^2 vértices)")


class FiguraMorphCreate(MorphParams):
    nombre: str = Field(..., min_length=1, max_length=60, description="Nombre personalizado de la figura")


class FiguraMorphOut(FiguraMorphCreate):
    id: int

