# Lo que falta capturar a mano (el reporte ya tiene el hueco marcado en rojo)

Generar el PDF al terminar: `python3 evidencias/generar_reporte.py` → `evidencias/reporte_seguridad.pdf`.

## Burp Suite (paso 2) → `evidencias/burp/`
Usar el navegador integrado de Burp (Proxy → Intercept → *Open browser*); es el que no se salta el proxy con `localhost`.
1. `01_http_history.png` – Proxy → HTTP history, tras abrir `http://localhost:8001/` (guardar 2 matrices, sumar) y `http://localhost:8000/view`.
2. `02_websocket_history.png` – Proxy → WebSockets history: frames `{"tx":…,"rx":…,"escala":…}` y `{"matrix":[…],"status":"ok"}`.
3. `03_repeater_idor.png` – (versión **vulnerable**) Repeater: `GET /matrices` sin cookie devuelve las matrices de otro.
4. `04_ws_origin_y_tamper.png` – WebSocket: reenviar un frame con `escala` o `rx:"abc"` alterados (vulnerable: se cierra el canal; corregida: responde `parámetros inválidos`).

Para correr la versión vulnerable: `git worktree add ../vuln 726743c && cd ../vuln && docker compose up -d --build` (detener antes la corregida con `docker compose down`).

## ZAP (pasos 1 y 7) → `evidencias/zap/`
Misma configuración que el escaneo inicial (Automated Scan, *Dev Standard*, spider tradicional + cliente, `http://host.docker.internal:8001` y `:8000`).
- Anexo A (antes): Report → Generate Report (HTML) → `reporte_antes_calculadora.html`, `reporte_antes_modelo3d.html`; captura de la lista de alertas expandida → `anexo_a_alertas_antes_*.png`.
- Anexo B (después): lo mismo con la rama corregida → `reporte_despues_*.html` y capturas `despues_calculadora_8001.png`, `despues_modelo3d_8000.png`.
- Si alguna alerta sigue, el reporte ya explica HSTS, Modern Web Application y `style-src unsafe-inline`; ajustar §3 paso 7 con lo que realmente salga.
