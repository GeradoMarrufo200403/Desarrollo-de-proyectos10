"""Sonda manual del WebSocket del visor. Uso: docker compose exec -T modelo3d python - < evidencias/ws_probe.py"""
import asyncio, json, websockets
from websockets.exceptions import InvalidStatus

URL = "ws://localhost:8000/ws/transform"

async def prueba(titulo, origin, mensajes, **kw):
    try:
        async with websockets.connect(URL, origin=origin, **kw) as ws:
            for m in mensajes:
                await ws.send(m)
                try:
                    print(f"{titulo}: {str(m)[:30]!r} -> {(await asyncio.wait_for(ws.recv(), 3))[:70]}")
                except Exception as e:
                    print(f"{titulo}: {str(m)[:30]!r} -> conexión cerrada ({type(e).__name__})")
                    return
    except InvalidStatus as e:
        print(f"{titulo}: handshake rechazado, HTTP {e.response.status_code}")

async def main():
    ok = "http://localhost:8000"
    await prueba("origen evil.example", "http://evil.example", ['{"rx":45}'])
    await prueba("origen legítimo", ok, ['{"rx":45,"escala":2}'])
    await prueba("rx='abc'", ok, ['{"rx":"abc"}', '{"rx":10}'])
    await prueba("lista JSON", ok, ['[1,2,3]', '{"rx":10}'])
    await prueba("NaN", ok, ['{"rx":NaN}'])
    await prueba("mensaje 20MB", ok, [json.dumps({"rx": 1, "pad": "A" * 20_000_000})], max_size=None)

asyncio.run(main())
