"""Pruebas del morph Dona -> Taza y guardado de figuras en Calculadora de matrices y Modelador 3D."""
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

CALC_DIR = Path(__file__).resolve().parents[1] / "Calculadora de matrices"
if str(CALC_DIR) not in sys.path:
    sys.path.insert(0, str(CALC_DIR))

anterior = os.getcwd()
os.chdir(CALC_DIR)
try:
    from app.main import app as calc_app
    from app.services import matrix_service
finally:
    os.chdir(anterior)

client = TestClient(calc_app)


def test_morph_t0_coincide_con_dona():
    puntos = matrix_service.calcular_morph(0.0, 10)
    assert len(puntos) == 100
    assert puntos[0] == [15.0, 0.0, 0.0]


def test_morph_t1_coincide_con_taza():
    puntos_dona = matrix_service.calcular_morph(0.0, 10)
    puntos_taza = matrix_service.calcular_morph(1.0, 10)
    assert len(puntos_taza) == 100
    assert puntos_dona != puntos_taza


def test_endpoint_calc_morph_devuelve_vertices():
    r = client.post("/operaciones/morph-3d", json={"t": 0.5, "resolucion": 12})
    assert r.status_code == 200
    body = r.json()
    assert body["total_puntos"] == 144
    assert len(body["vertices"]) == 144
    assert "resumen_markdown" in body
    assert "Transición (50.0%)" in body["resumen_markdown"]


def test_guardar_y_listar_figura_morph():
    r = client.post("/figuras", json={"nombre": "Taza Glassmorphism", "t": 1.0, "resolucion": 20})
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == "Taza Glassmorphism"
    fig_id = data["id"]

    # Consultar por ID y en la lista
    assert client.get(f"/figuras/{fig_id}").status_code == 200
    lista = client.get("/figuras").json()
    assert any(f["nombre"] == "Taza Glassmorphism" for f in lista)

    # Eliminar figura por ID
    assert client.delete(f"/figuras/{fig_id}").status_code == 204
    assert client.get(f"/figuras/{fig_id}").status_code == 404


