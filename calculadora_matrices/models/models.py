# models.py

from pydantic import BaseModel, field_validator

class MatrixCreate(BaseModel):
    nombre: str
    datos: list[list[float]]
    
    @field_validator("datos")
    @classmethod
    def filas_parejas(cls, v):
        largos = {len(fila) for fila in v}
        if len(largos) != 1:
            raise ValueError("todas las filas deben tener el mismo largo")
        return v

class MatrixOut(MatrixCreate):
    id: int

# Modelos para operaciones sin estado (las matrices viajan en el body, no se guardan)

class DosMatrices(BaseModel):
    m1: list[list[float]]
    m2: list[list[float]]

class UnaMatriz(BaseModel):
    m: list[list[float]]

class Transformacion(BaseModel):
    tx: float = 0.0
    ty: float = 0.0
    tz: float = 0.0
    rx: float = 0.0  # grados
    ry: float = 0.0
    rz: float = 0.0
    escala: float = 1.0

class CadenaMatrices(BaseModel):
    matrices: list[list[list[float]]]
    transponer: bool = False

    @field_validator("matrices")
    @classmethod
    def no_vacia(cls, v):
        if not v:
            raise ValueError("se requiere al menos una matriz")
        return v
