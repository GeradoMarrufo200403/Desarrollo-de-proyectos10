"""Pruebas del servicio Modelador3D_matrices (modelos CSV, visor Glassmorphism y cabeceras)."""
import importlib.util
import os
from pathlib import Path
from fastapi.testclient import TestClient

VISOR_DIR = Path(__file__).resolve().parents[1] / "Modelador3D_matrices"


def cargar_visor_app():
    anterior = os.getcwd()
    os.chdir(VISOR_DIR)
    try:
        spec = importlib.util.spec_from_file_location("modelador_main", VISOR_DIR / "main.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    finally:
        os.chdir(anterior)


def test_visor_lista_modelos_3d_disponibles():
    app = cargar_visor_app()
    client = TestClient(app)
    r = client.get("/api/modelos")
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()["modelos"]]
    assert {"dona", "esfera", "piramide"}.issubset(set(ids))


def test_visor_sirve_interfaz_glassmorphism_con_controles_morph():
    anterior = os.getcwd()
    os.chdir(VISOR_DIR)
    try:
        app = cargar_visor_app()
        client = TestClient(app)
        r = client.get("/view")
        assert r.status_code == 200
        html = r.text
        assert "Matrix API Transform" in html
        assert "btn-fig-dona" in html
        assert "btn-fig-esfera" in html
        assert "btn-fig-piramide" in html
        assert "btn-fig-morph" in html
        assert "morph-panel" in html
    finally:
        os.chdir(anterior)

