import math
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

MAX_DIMENSION_MATRIZ = 10
MAX_MAGNITUD_VALOR = 1e9


class MatrixCreate(BaseModel):
    nombre: Optional[str] = Field(default=None, max_length=60)
    datos: List[List[float]] = Field(..., description="Matriz bidimensional de números")

    @field_validator("datos")
    @classmethod
    def validar_dimensiones_y_valores(cls, v):
        if not v or not v[0]:
            raise ValueError("La matriz no puede estar vacía")
        if len(v) > MAX_DIMENSION_MATRIZ or len(v[0]) > MAX_DIMENSION_MATRIZ:
            raise ValueError(
                f"Por seguridad, la dimensión máxima permitida es {MAX_DIMENSION_MATRIZ}x{MAX_DIMENSION_MATRIZ}"
            )
        largos = [len(fila) for fila in v]
        if len(set(largos)) > 1:
            raise ValueError("Todas las filas deben tener el mismo largo")
        for fila in v:
            for val in fila:
                if not math.isfinite(val) or abs(val) > MAX_MAGNITUD_VALOR:
                    raise ValueError("Todos los valores deben ser números finitos dentro del rango permitido")
        return v


class MatrixOut(MatrixCreate):
    id: int


class MorphParams(BaseModel):
    t: float = Field(0.0, ge=0.0, le=1.0, allow_inf_nan=False, description="Factor de deformación: 0.0 = Dona, 1.0 = Taza")
    resolucion: int = Field(50, ge=4, le=100, description="Resolución por eje (genera resolucion^2 vértices)")


class FiguraMorphCreate(MorphParams):
    nombre: str = Field(..., min_length=1, max_length=60, description="Nombre personalizado de la figura")

    @field_validator("nombre")
    @classmethod
    def validar_nombre_seguro(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("El nombre de la figura no puede estar vacío ni contener solo espacios")
        if any(c in limpio for c in ("<", ">", "{", "}", "\n", "\r")):
            raise ValueError("El nombre contiene caracteres no permitidos")
        return limpio


class FiguraMorphOut(FiguraMorphCreate):
    id: int
