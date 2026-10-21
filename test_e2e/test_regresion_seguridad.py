"""Regresión de las correcciones de seguridad (ZAP + Burp). Cada test falla en la versión vulnerable."""
import http.server
import threading

import pytest
from playwright.sync_api import Page, Playwright

CALC = "http://localhost:8001"
VISOR = "http://localhost:8000"


@pytest.fixture
def web_ajena():
    """Una 'web maliciosa' real en otro origen (localhost:9999) para probar ataques cross-site."""
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html></html>")

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 9999), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield "http://localhost:9999/"
    srv.shutdown()
    srv.server_close()


@pytest.fixture
def api(playwright: Playwright):
    ctx = playwright.request.new_context()
    yield ctx
    ctx.dispose()


def test_calculadora_cabeceras_de_seguridad(api):
    h = api.get(f"{CALC}/").headers
    assert "script-src 'self'" in h["content-security-policy"]
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert h["x-frame-options"] == "DENY"
    assert h["x-content-type-options"] == "nosniff"


def test_visor_cabeceras_de_seguridad(api):
    h = api.get(f"{VISOR}/view").headers
    assert "content-security-policy" in h
    assert h["x-frame-options"] == "DENY"
    assert h["x-content-type-options"] == "nosniff"


def test_visor_cors_no_refleja_origen_ajeno(api):
    r = api.get(f"{VISOR}/api/figuras", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers
    assert "access-control-allow-credentials" not in r.headers


def test_websocket_rechaza_origen_ajeno(page: Page, web_ajena: str):
    """Una web ajena no puede usar el visor desde el navegador de la víctima (CSWSH)."""
    page.goto(web_ajena)
    abierto = page.evaluate("""() => new Promise(res => {
        const ws = new WebSocket('ws://localhost:8000/ws/transform');
        ws.onopen = () => res(true);
        ws.onerror = () => res(false);
        ws.onclose = () => res(false);
    })""")
    assert abierto is False


def test_websocket_sobrevive_a_entrada_invalida(page: Page):
    page.goto(f"{VISOR}/view")
    respuestas = page.evaluate("""() => new Promise(res => {
        const ws = new WebSocket('ws://localhost:8000/ws/transform');
        const out = [];
        ws.onopen = () => { ws.send('{"rx":"abc"}'); ws.send('[1,2,3]'); ws.send('{"rx":45}'); };
        ws.onmessage = e => { out.push(JSON.parse(e.data)); if (out.length === 3) res(out); };
        ws.onclose = () => res(out);
    })""")
    assert [r["status"] for r in respuestas] == ["error", "error", "ok"]


def test_matrices_son_privadas_por_sesion(playwright: Playwright):
    a, b = playwright.request.new_context(), playwright.request.new_context()
    try:
        r = a.post(f"{CALC}/matrices", data={"nombre": "secreta", "datos": [[1, 2]]})
        assert r.ok
        assert len(a.get(f"{CALC}/matrices").json()) >= 1
        assert b.get(f"{CALC}/matrices").json() == []
        id_ajeno = r.json()["id"]
        assert b.post(f"{CALC}/operaciones/transponer?id={id_ajeno}").status == 404
    finally:
        a.dispose()
        b.dispose()


@pytest.mark.parametrize("ruta,cuerpo", [
    ("/calc/sumar", {"m1": [[1, 2], [3]], "m2": [[1, 2], [3, 4]]}),        # matriz irregular
    ("/calc/transponer", {"m": [[1e308, 1e308]]}),                          # valor desmedido
    ("/calc/determinante", {"m": [[1] * 51] * 51}),                         # 51x51 > límite
    ("/calc/multiplicar-cadena", {"matrices": [[[1]]] * 11}),               # cadena > 10
    ("/calc/transformacion", {"escala": 1e308}),                            # fuera de rango
    ("/matrices", {"nombre": "x" * 61, "datos": [[1]]}),                    # nombre largo
])
def test_calculadora_rechaza_entradas_abusivas(api, ruta, cuerpo):
    assert api.post(f"{CALC}{ruta}", data=cuerpo).status == 422


def test_calculadora_rechaza_nan(api):
    r = api.post(f"{CALC}/calc/transponer", headers={"content-type": "application/json"}, data='{"m":[[NaN]]}')
    assert r.status == 422


def test_docs_no_expuestos(api):
    assert api.get(f"{CALC}/openapi.json").status == 404
    assert api.get(f"{VISOR}/docs").status == 404
    assert "calculadora" not in api.get(f"{VISOR}/").json()


def test_calculadora_sigue_calculando(api):
    r = api.post(f"{CALC}/calc/multiplicar", data={"m1": [[1, 2], [3, 4]], "m2": [[5, 6], [7, 8]]})
    assert r.json() == {"resultado": [[19, 22], [43, 50]]}
    assert api.post(f"{CALC}/calc/determinante", data={"m": [[1, 2], [3, 4]]}).json() == {"resultado": -2.0}
