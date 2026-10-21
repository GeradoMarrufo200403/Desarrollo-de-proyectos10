from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
from models.models import MatrixCreate, DosMatrices, UnaMatriz, CadenaMatrices, Transformacion
from repository.repository import MatrixRepository
from services import services

app = FastAPI()

repo = MatrixRepository()

@app.get("/")
def home():
    return FileResponse("./web/index.html")

@app.post("/matrices")
def crear_matriz(payload: MatrixCreate):
    return repo.crear(payload.model_dump())

@app.post("/operaciones/sumar")
def sumar_matrices(id1: int, id2: int): 
    m1, m2 = repo.obtener(id1), repo.obtener(id2)     
    if not m1 or not m2:         
        raise HTTPException(404, "matriz no encontrada")     
    try:         
        return {"resultado": services.sumar(m1["datos"], m2["datos"])} 
    except ValueError as e:         
        raise HTTPException(400, str(e))

@app.post("/operaciones/multiplicar")
def multiplicar_matrices(id1: int, id2: int): 
    m1, m2 = repo.obtener(id1), repo.obtener(id2)     
    if not m1 or not m2:         
        raise HTTPException(404, "matriz no encontrada")     
    try:         
        return {"resultado": services.multiplicar(m1["datos"], m2["datos"])} 
    except ValueError as e:         
        raise HTTPException(400, str(e))

@app.post("/operaciones/transponer")
def transponer_matriz(id: int): 
    m = repo.obtener(id)     
    if not m:         
        raise HTTPException(404, "matriz no encontrada")     
    try:         
        return {"resultado": services.transponer(m["datos"])} 
    except ValueError as e:         
        raise HTTPException(400, str(e))

@app.post("/operaciones/determinante")
def determinante_matriz(id: int): 
    m = repo.obtener(id)     
    if not m:         
        raise HTTPException(404, "matriz no encontrada")     
    try:         
        return {"resultado": services.determinante(m["datos"])} 
    except ValueError as e:         
        raise HTTPException(400, str(e))

@app.get("/matrices")
def listar_matrices():
    return repo.listar()

# Operaciones sin estado: reciben las matrices en el body y no las guardan.
# Pensadas para que otros servicios (p. ej. modelo-3D) consuman la calculadora.

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/calc/sumar")
def calc_sumar(p: DosMatrices):
    try:
        return {"resultado": services.sumar(p.m1, p.m2)}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/calc/multiplicar")
def calc_multiplicar(p: DosMatrices):
    try:
        return {"resultado": services.multiplicar(p.m1, p.m2)}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/calc/transponer")
def calc_transponer(p: UnaMatriz):
    try:
        return {"resultado": services.transponer(p.m)}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/calc/determinante")
def calc_determinante(p: UnaMatriz):
    try:
        return {"resultado": services.determinante(p.m)}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/calc/transformacion")
def calc_transformacion(p: Transformacion):
    """Construye M = T · Rz · Ry · Rx · S a partir de traslación, rotación (grados) y escala.
    Devuelve M por filas y aplanada en Column-Major (formato que usa Three.js)."""
    M = services.transformacion(p.tx, p.ty, p.tz, p.rx, p.ry, p.rz, p.escala)
    return {
        "resultado": M,
        "column_major": services.column_major(M)
    }

@app.post("/calc/multiplicar-cadena")
def calc_multiplicar_cadena(p: CadenaMatrices):
    """Calcula A @ B @ C ... en una sola llamada; opcionalmente transpone el resultado."""
    try:
        resultado = p.matrices[0]
        for m in p.matrices[1:]:
            resultado = services.multiplicar(resultado, m)
        if p.transponer:
            resultado = services.transponer(resultado)
        return {"resultado": resultado}
    except ValueError as e:
        raise HTTPException(400, str(e))

    