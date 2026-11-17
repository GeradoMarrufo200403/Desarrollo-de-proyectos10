"""Pruebas en rojo de la revision de codigo (Actividad #12 - Rama review-act12).

Cada prueba en este archivo falla sobre la rama `feat/morph-dona-taza` (PR #2)
y demuestra empiricamente un defecto real encontrado durante la auditoria.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
CALC_DIR = ROOT_DIR / "calculadora_matrices"
VISOR_DIR = ROOT_DIR / "modelo-3D"


@pytest.fixture(scope="module")
def calc_mod():
    anterior = os.getcwd()
    os.chdir(CALC_DIR)
    try:
        if str(CALC_DIR) not in sys.path:
            sys.path.insert(0, str(CALC_DIR))
        import main as calc_main
        from services import services as calc_services
        yield calc_main, calc_services
    finally:
        os.chdir(anterior)


@pytest.fixture(scope="module")
def visor_mod():
    anterior = os.getcwd()
    os.chdir(VISOR_DIR)
    try:
        spec = importlib.util.spec_from_file_location("visor_main_review", VISOR_DIR / "main.py")
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        yield modulo
    finally:
        os.chdir(anterior)


# ---------------------------------------------------------------------------
# DEFECTO 1 [Bloqueante]: Ejecutar `pytest tests_unitarias` desde la raiz del
# repositorio (como indica el README y la descripcion del PR) falla al importar
# `calculadora_matrices/main.py` porque monta `StaticFiles(directory="web/static")`
# con una ruta relativa al CWD en lugar de usar `Path(__file__).parent`.
# ---------------------------------------------------------------------------
def test_defecto1_pytest_desde_raiz_no_debe_fallar_por_ruta_relativa():
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "tests_unitarias/test_morph.py", "-k", "test_morph_es_determinista"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
         check=False,
    )
    assert resultado.returncode == 0, (
        f"Correr pytest desde la raiz fallo con codigo {resultado.returncode}:\n{resultado.stdout}\n{resultado.stderr}"
    )


# ---------------------------------------------------------------------------
# DEFECTO 2 [Bloqueante]: Las figuras guardadas desde el visor WebSocket usan
# un `sid` efimero inventado dentro de `websocket_transform` que ignora la
# cookie `sid` del navegador y nunca se devuelve al cliente. Al consultar
# `GET /figuras` con la sesion del usuario, la figura guardada no aparece.
# ---------------------------------------------------------------------------
def test_defecto2_figura_guardada_por_ws_debe_poder_consultarse_en_get_figuras(calc_mod, visor_mod):
    calc_main, _ = calc_mod
    cliente_calc = TestClient(calc_main.app)

    # 1. El navegador obtiene su cookie de sesion `sid` al visitar la calculadora
    r_home = cliente_calc.get("/")
    sid_navegador = r_home.cookies.get("sid")
    assert sid_navegador is not None

    # 2. Conectamos el visor enviando esa misma cookie `sid` del usuario y guardamos una figura
    def redirigir_a_calc(request: httpx.Request) -> httpx.Response:
        resp = cliente_calc.request(
            request.method,
            request.url.path,
            content=request.content,
            headers=dict(request.headers),
        )
        return httpx.Response(resp.status_code, headers=dict(resp.headers), content=resp.content)

    with TestClient(visor_mod.app, cookies={"sid": sid_navegador}) as cliente_visor:
        visor_mod.app.state.calc = httpx.AsyncClient(
            transport=httpx.MockTransport(redirigir_a_calc), base_url="http://calculadora"
        )
        with cliente_visor.websocket_connect("/ws/transform") as ws:
            ws.send_text(json.dumps({"guardar": {"nombre": "TazaUsuario", "t": 1.0, "resolucion": 10}}))
            respuesta_ws = ws.receive_json()
            assert respuesta_ws["status"] == "ok"

    # 3. Al consultar `GET /figuras` con la sesion del usuario, debe aparecer "TazaUsuario"
    figuras_usuario = cliente_calc.get("/figuras", cookies={"sid": sid_navegador}).json()
    nombres = [f["nombre"] for f in figuras_usuario]
    assert "TazaUsuario" in nombres, (
        f"La figura guardada por WebSocket quedo huerfana en un sid efimero; GET /figuras devolvio: {figuras_usuario}"
    )


# ---------------------------------------------------------------------------
# DEFECTO 3 [Mayor]: Validacion insuficiente de `nombre` en `FiguraCreate` y
# `GuardarPedido`. La regex `^[\w .\-]+$` acepta nombres vacios compuestos solo
# por espacios ("   ") o solo por puntos/guiones ("...", "---").
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nombre_vacio", ["   ", ".....", "-----", " . - . "])
def test_defecto3_nombre_solo_espacios_o_puntuacion_debe_rechazarse(calc_mod, nombre_vacio):
    calc_main, _ = calc_mod
    cliente = TestClient(calc_main.app)
    r = cliente.post("/figuras", json={"nombre": nombre_vacio, "t": 0.5, "resolucion": 10})
    assert r.status_code == 422, (
        f"POST /figuras acepto el nombre invalido {nombre_vacio!r} con status {r.status_code}: {r.json()}"
    )


# ---------------------------------------------------------------------------
# DEFECTO 4 [Mayor]: `services.morph(t, resolucion)` carece de validacion de
# dominio en la capa de servicios (a diferencia de sumar/multiplicar/determinante).
# Acepta t fuera de [0, 1] (extrapolando sin error), resolucion negativa
# (devolviendo lista vacia) y resolucion=0 (lanzando ZeroDivisionError).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("t,resolucion", [
    (1.5, 10),
    (-1.0, 10),
    (0.5, -4),
    (0.5, 0),
    (0.5, 500),
])
def test_defecto4_servicio_morph_debe_validar_dominio_con_value_error(calc_mod, t, resolucion):
    _, calc_services = calc_mod
    with pytest.raises(ValueError):
        calc_services.morph(t, resolucion)


# ---------------------------------------------------------------------------
# DEFECTO 5 [Mayor]: Cuando la calculadora responde HTTP 429 en `/figuras`,
# `responder()` en `modelo-3D/main.py` atrapa `httpx.HTTPError`, reporta
# falsamente "calculadora no disponible" y devuelve `costoso = False`, lo que
# evita incrementar el contador `morphs` y permite saltar el rate-limit de
# `MAX_MORPH_POR_SEG` (20 peticiones/s) hasta 200 peticiones/s.
# ---------------------------------------------------------------------------
def test_defecto5_error_429_de_calculadora_no_debe_saltar_rate_limit_ni_mentir(visor_mod, monkeypatch):
    pedidos_recibidos = 0

    def calc_saturada(request: httpx.Request) -> httpx.Response:
        nonlocal pedidos_recibidos
        pedidos_recibidos += 1
        return httpx.Response(429, json={"detail": "máximo 100 figuras por sesión"})

    monkeypatch.setattr(visor_mod.time, "monotonic", lambda: 1000.0)
    with TestClient(visor_mod.app) as cliente:
        visor_mod.app.state.calc = httpx.AsyncClient(
            transport=httpx.MockTransport(calc_saturada), base_url="http://calculadora"
        )
        with cliente.websocket_connect("/ws/transform") as ws:
            for _ in range(visor_mod.MAX_MORPH_POR_SEG + 15):
                ws.send_text(json.dumps({"guardar": {"nombre": "Taza", "t": 1, "resolucion": 10}}))
                ultimo = ws.receive_json()

    assert pedidos_recibidos <= visor_mod.MAX_MORPH_POR_SEG, (
        f"Se enviaron {pedidos_recibidos} peticiones costosas en 1s (limite={visor_mod.MAX_MORPH_POR_SEG}) "
        f"porque responder() devuelve costoso=False ante HTTPStatusError. Ultima respuesta: {ultimo}"
    )
