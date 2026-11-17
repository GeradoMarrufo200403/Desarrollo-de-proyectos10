"""Pruebas de regresión de seguridad OWASP para Calculadora de matrices y Modelador 3D."""
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

CALC_DIR = Path(__file__).resolve().parents[1] / "Calculadora de matrices"
if str(CALC_DIR) not in sys.path:
    sys.path.insert(0, str(CALC_DIR))

anterior = os.getcwd()
os.chdir(CALC_DIR)
try:
    from app.main import app as calc_app
finally:
    os.chdir(anterior)

client = TestClient(calc_app)


def test_cabeceras_seguridad_owasp_presentes():
    """Verifica mitigaciones H-04, H-05, H-06 y H-07 (CSP, X-Frame-Options, nosniff, sin header server)."""
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert "Content-Security-Policy" in r.headers
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert "server" not in r.headers


def test_proteccion_dos_algoritmico_determinante_mayor_a_8x8():
    """Verifica mitigación H-01: rechazo de determinante para matrices mayores a 8x8."""
    matriz_9x9 = [[float(i == j) for j in range(9)] for i in range(9)]
    r_create = client.post("/matrices", json={"nombre": "M9x9", "datos": matriz_9x9})
    assert r_create.status_code == 200
    m_id = r_create.json()["id"]

    r_det = client.get(f"/matrices/{m_id}/determinante")
    assert r_det.status_code == 400
    assert "8x8" in r_det.json()["detail"]


def test_rechazo_matrices_gigantes_mayores_a_10x10():
    """Verifica mitigación H-02: límite máximo 10x10 en backend Pydantic."""
    matriz_11x11 = [[1.0] * 11 for _ in range(11)]
    r = client.post("/matrices", json={"nombre": "Gigante", "datos": matriz_11x11})
    assert r.status_code == 422


@pytest.mark.parametrize("nombre_malicioso", [
    "   ",
    "<script>alert(1)</script>",
    "figura\ncon_salto",
    "{{7*7}}",
])
def test_rechazo_nombres_figura_invalidos_o_xss(nombre_malicioso):
    """Verifica que el router de figuras rechace nombres en blanco o con etiquetas HTML/inyección."""
    r = client.post("/figuras", json={"nombre": nombre_malicioso, "t": 0.5, "resolucion": 20})
    assert r.status_code == 422

