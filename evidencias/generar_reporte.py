"""Genera evidencias/reporte_seguridad.pdf (HTML -> PDF con Chrome headless).
Uso: python3 evidencias/generar_reporte.py   (solo incluye las capturas que existan)"""
import html, pathlib, subprocess

E = pathlib.Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def existe(r):
    return (E / r).exists()


def fig(r, pie, clase=""):
    return f'<figure class="{clase}"><img src="{r}"><figcaption>{pie}</figcaption></figure>' if existe(r) else ""


def fila(*figs):
    figs = [f for f in figs if f]
    return f'<div class="cols">{"".join(figs)}</div>' if figs else ""


def anexo(r, texto):
    return f'<li>{texto}: <code>evidencias/{r}</code></li>' if existe(r) else ""


CSS = """
:root { --ink:#16202a; --mute:#5b6773; --line:#d8dee4; --red:#c0392b; --amber:#b7791f; --blue:#2b6cb0; --green:#2f855a; }
@page { size: A4; margin: 15mm 14mm; }
* { box-sizing: border-box; }
body { font: 9pt/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif; color: var(--ink); }
h1 { font-size: 20pt; margin: 0; letter-spacing: -.3px; }
.sub { color: var(--mute); margin: 2px 0 10px; }
h2 { font-size: 12.5pt; margin: 16px 0 6px; padding-left: 8px; border-left: 4px solid var(--blue); break-after: avoid; }
h3 { font-size: 9.6pt; margin: 11px 0 3px; color: var(--blue); break-after: avoid; }
p { margin: 3px 0; } code { font: 7.8pt Menlo, monospace; background: #eef1f4; padding: 0 3px; border-radius: 3px; }
.kpis { display: flex; gap: 8px; margin: 8px 0 4px; }
.kpi { flex: 1; border: 1px solid var(--line); border-radius: 6px; padding: 6px 8px; }
.kpi b { display: block; font-size: 15pt; line-height: 1.1; } .kpi span { color: var(--mute); font-size: 7.6pt; }
table { border-collapse: collapse; width: 100%; font-size: 7.9pt; }
th { text-align: left; background: #f1f4f7; font-weight: 600; } th, td { border-bottom: 1px solid var(--line); padding: 4px 5px; vertical-align: top; }
tr { break-inside: avoid; }
.tag { display: inline-block; font-size: 7pt; font-weight: 700; padding: 0 5px; border-radius: 9px; color: #fff; white-space: nowrap; }
.alto { background: var(--red); } .medio { background: var(--amber); } .bajo { background: var(--blue); } .info { background: #718096; }
.ok { color: var(--green); font-weight: 600; } .fp { color: var(--blue); font-weight: 600; } .re { color: var(--red); font-weight: 600; }
figure { margin: 5px 0; break-inside: avoid; } figcaption { font-size: 7.5pt; color: var(--mute); margin-top: 2px; }
img { width: 100%; border: 1px solid var(--line); border-radius: 4px; display: block; }
.crop img { aspect-ratio: 4.4 / 1; object-fit: cover; object-position: 0 100%; }
.cols { display: flex; gap: 8px; align-items: flex-start; } .cols > * { flex: 1; min-width: 0; }
pre { background: #f6f8fa; border: 1px solid var(--line); border-radius: 4px; padding: 5px 7px; font: 6.9pt/1.35 Menlo, monospace; white-space: pre-wrap; word-break: break-all; margin: 4px 0; }
ul, ol { margin: 3px 0 3px 16px; padding: 0; } li { margin: 2px 0; }
.nota { background: #f6f8fa; border-left: 3px solid var(--line); padding: 4px 8px; margin: 6px 0; color: #34404c; }
.pb { break-before: page; }
"""

T = lambda n, c: f'<span class="tag {c}">{n}</span>'
A, M, B, I = T("Alto", "alto"), T("Medio", "medio"), T("Bajo", "bajo"), T("Info", "info")

TABLA = f"""
<table><tr><th>Hallazgo</th><th>Riesgo</th><th>¿Real o falso positivo?</th><th>Mitigación</th><th>Estado final</th></tr>
<tr><td colspan="5" style="background:#fafbfc"><b>Encontrados a mano</b> (ni ZAP ni Burp los reportaron)</td></tr>
<tr><td><b>M1</b> <code>GET /matrices</code> lista las matrices de todos; IDs secuenciales</td><td>{A}</td><td class="re">Real. Burp (captura 3) muestra datos de otros sin autenticarse.</td><td>Matrices privadas por sesión (cookie <code>sid</code> HttpOnly, SameSite=Strict); la ajena responde 404.</td><td class="ok">Corregido</td></tr>
<tr><td><b>M2</b> WebSocket del visor acepta cualquier <code>Origin</code> (CSWSH)</td><td>{A}</td><td class="re">Real. Una web en otro puerto lo abrió desde Chrome.</td><td>Lista de orígenes permitidos; el handshake devuelve 403. Máx. 20 conexiones y 200 msg/s.</td><td class="ok">Corregido</td></tr>
<tr><td><b>M3</b> CORS reflejado con credenciales en el visor</td><td>{M}</td><td class="re">Real: devolvía <code>ACAO: http://evil.example</code> + <code>ACAC: true</code>. ZAP no envía <code>Origin</code>.</td><td>Lista blanca, sin credenciales, solo GET.</td><td class="ok">Corregido</td></tr>
<tr><td><b>M4</b> Entradas sin límite (matrices 400×400, cadenas, almacenamiento)</td><td>{M}</td><td class="re">Real. ×300 tarda 0,9 s y crece como n³; el escaneo de ZAP llegó a guardar 135+ matrices basura.</td><td>≤50×50, ≤10 matrices por cadena, |x|≤1e12, ≤100 matrices por sesión, mensaje WS ≤1 KB.</td><td class="ok">Corregido</td></tr>
<tr><td><b>M5</b> <code>NaN</code> → error 500; <code>{{"rx":"abc"}}</code> cierra el WebSocket; matriz irregular suma sin avisar</td><td>{M}</td><td class="re">Real; los tres reproducidos.</td><td>Validación Pydantic; error 422 sin devolver la entrada; el WS responde <code>error</code> y sigue abierto.</td><td class="ok">Corregido</td></tr>
<tr><td><b>M6</b> <code>/docs</code>, URL interna en <code>/</code>, puertos en 0.0.0.0, contenedor root</td><td>{B}</td><td class="re">Real.</td><td>Docs apagados por defecto, puertos en 127.0.0.1, usuario no root, <code>cap_drop</code>, versiones fijas.</td><td class="ok">Corregido</td></tr>
<tr><td colspan="5" style="background:#fafbfc"><b>Alertas de ZAP</b> (8 por aplicación)</td></tr>
<tr><td>CSP Header Not Set</td><td>{M}</td><td class="re">Real (defensa en profundidad).</td><td>CSP con <code>script-src 'self'</code>; JS y CSS movidos a <code>/static</code>.</td><td class="ok">Corregido. Queda <i>style-src unsafe-inline</i> (ver abajo)</td></tr>
<tr><td>Missing Anti-clickjacking Header</td><td>{M}</td><td class="re">Real.</td><td><code>X-Frame-Options: DENY</code> y <code>frame-ancestors 'none'</code>.</td><td class="ok">Corregido</td></tr>
<tr><td>Sub Resource Integrity Missing</td><td>{M}</td><td class="re">Real: se cargaba código/estilos de terceros sin verificar.</td><td>Sin terceros: fuentes del sistema y <code>three.min.js</code> local.</td><td class="ok">Corregido</td></tr>
<tr><td>X-Content-Type-Options Missing</td><td>{B}</td><td class="re">Real.</td><td><code>nosniff</code>.</td><td class="ok">Corregido</td></tr>
<tr><td>Cross-Domain Misconfiguration</td><td>{M}</td><td class="fp">Falso positivo sobre nuestro código: las URLs de la alerta son <code>fonts.googleapis.com</code> y <code>fonts.gstatic.com</code> (ACAO <code>*</code> en fuentes públicas). El CORS inseguro real es M3.</td><td>Se quitaron las fuentes externas.</td><td class="ok">Desapareció</td></tr>
<tr><td>Strict-Transport-Security Not Set</td><td>{B}</td><td class="fp">Falso positivo en local: HSTS solo aplica sobre HTTPS y el laboratorio es <code>http://localhost</code>. Sería real en producción.</td><td><code>ENABLE_HSTS=1</code> listo para usar detrás de TLS.</td><td class="ok">Desapareció (ZAP la evalúa en respuestas HTTPS, que eran las de terceros)</td></tr>
<tr><td>Retrieved from Cache</td><td>{I}</td><td class="fp">Falso positivo aquí (recursos públicos de terceros).</td><td><code>Cache-Control: no-store</code>.</td><td class="ok">Desapareció</td></tr>
<tr><td>Modern Web Application</td><td>{I}</td><td class="fp">Falso positivo: solo avisa que la app usa JavaScript.</td><td>—</td><td>Sigue (esperado)</td></tr>
<tr><td>CSP: style-src unsafe-inline <i>(nueva)</i></td><td>{M}</td><td class="re">Real, menor: aparece ahora que existe CSP.</td><td>Pendiente: los resultados se pintan con <code>style="…"</code> generado por JS; habría que pasarlos a clases CSS. <code>script-src</code> sí es estricta.</td><td>Sigue (deuda documentada)</td></tr>
<tr><td>Session Management Response Identified <i>(nueva)</i></td><td>{I}</td><td class="fp">Falso positivo: ZAP detecta la cookie <code>sid</code> que añadimos a propósito.</td><td>—</td><td>Sigue (esperado)</td></tr>
</table>"""

ANEXOS = "".join([
    anexo("zap/reporte_antes_calculadora.html", "Reporte ZAP antes, calculadora"),
    anexo("zap/reporte_antes_modelo3d.html", "Reporte ZAP antes, visor"),
    anexo("zap/reporte_despues_calculadora.html", "Reporte ZAP después, calculadora"),
    anexo("zap/reporte_despues_modelo3d.html", "Reporte ZAP después, visor"),
])
ANEXOS = f"<h2>Anexos</h2><ul>{ANEXOS}<li>Pruebas manuales y de regresión: <code>evidencias/antes/</code>, <code>evidencias/despues/</code>, <code>test_e2e/test_regresion_seguridad.py</code></li></ul>"

HTML = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Reporte de seguridad</title><style>{CSS}</style></head><body>

<h1>Seguridad de la calculadora de matrices y el visor 3D</h1>
<p class="sub">Gianina Casanova · <a href="https://github.com/Ninacruz25/calculadora">github.com/Ninacruz25/calculadora</a> · rama <code>seguridad/zap-burp-mitigaciones</code><br>
OWASP ZAP 2.17 (Automated Scan, <i>Dev Standard</i>), Burp Suite y revisión manual. Solo apps propias en entorno local.</p>

<div class="kpis">
<div class="kpi"><b>8 → 3</b><span>alertas de ZAP en la calculadora (4 medias → 1 media)</span></div>
<div class="kpi"><b>6</b><span>hallazgos reales que ZAP y Burp no reportaron</span></div>
<div class="kpi"><b>14 / 15</b><span>pruebas de seguridad que fallan en la versión vulnerable</span></div>
<div class="kpi"><b>23 / 23</b><span>pruebas e2e que pasan tras las correcciones</span></div>
</div>

<h2>1. Hallazgos</h2>
{TABLA}

<h2>2. Prioridad</h2>
<p>Criterio: <b>impacto × probabilidad × facilidad de explotación</b>, pensando en que los datos fueran sensibles. Pesa más lo que da acceso a datos ajenos o lo puede disparar otra web sin que la víctima haga algo; las cabeceras pesan menos porque solo ayudan cuando ya existe otro fallo.</p>
<ol>
<li><b>M1</b>: un <code>GET</code> sin autenticar expone todo. Impacto máximo, esfuerzo mínimo.</li>
<li><b>M2 y M3</b>: cualquier web que visite la víctima puede operar el visor.</li>
<li><b>M4</b>: un solo <code>POST</code> degrada el servicio para todos.</li>
<li><b>M5</b>: un resultado incorrecto sin error es peor que un error, porque nadie lo nota.</li>
<li><b>CSP, clickjacking, SRI, nosniff</b>: reducen el daño de otro fallo. SRI sube por riesgo de cadena de suministro.</li>
<li><b>M6 y HSTS</b>: bajo en local, relevante al desplegar.</li></ol>

<h2 class="pb">3. Evidencias por paso</h2>

<h3>Paso 1 · Estado inicial con ZAP</h3>
<p>Ambos servicios con <code>docker compose up</code>, escaneados en <code>host.docker.internal:8001</code> (calculadora) y <code>:8000</code> (visor). Resultado: 8 alertas en cada uno (0 altas, 4 medias, 2 bajas, 2 informativas).</p>
{fig("zap/antes_calculadora_8001.jpeg", "Calculadora, antes: 8 alertas", "crop")}
{fig("zap/antes_modelo3d_8000.jpeg", "Visor 3D, antes: 8 alertas", "crop")}

<h3>Paso 2 · Tráfico en Burp Suite</h3>
<p>Todo viaja en claro (<code>http</code> y <code>ws</code>). La calculadora envía matrices en JSON y los IDs van en la URL (<code>/operaciones/sumar?id1=136&amp;id2=…</code>). El visor descarga 10 000 puntos y, por WebSocket, intercambia unos 60 mensajes por segundo: el navegador manda <code>tx, ty, tz, rx, ry, rz, escala</code> y recibe la matriz 4×4. Con Repeater o Intercept se puede cambiar un ID, alterar un frame o modificar la matriz de respuesta, porque no hay TLS ni firma.</p>
{fig("burp/01_http_history.png", "HTTP history: calculadora y visor")}
{fig("burp/02_websocket_history.png", "WebSockets history: parámetros hacia el servidor y matriz de vuelta")}
{fig("burp/03_repeater_idor.png", "Repeater: <code>GET /matrices</code> sin credenciales devuelve todas las matrices, incluidas las que dejó el escaneo de ZAP (p. ej. nombre <code>c:/Windows/system.ini</code>)")}
{fig("burp/04_ws_origin_y_tamper.png", "WebSocket con Origin ajeno o frame alterado")}

<h3>Pasos 3 y 4 · Clasificación y lo que las herramientas no vieron</h3>
<p>La clasificación está en la tabla del §1. ZAP hace análisis pasivo y ataques genéricos, pero no sabe que <code>/matrices</code> debería ser privado, no envía <code>Origin</code> y no manda frames mal formados al WebSocket. M1 a M6 salieron de leer <code>main.py</code> y probar a mano:</p>
<pre>ANTES (versión vulnerable)
CORS con Origin hostil     → access-control-allow-origin: http://evil.example + allow-credentials: true
GET /matrices (sin sesión) → [{{"nombre":"cuenta_secreta","datos":[[1500000.5,42.0]],"id":1}}]
WebSocket, Origin evil     → aceptado, devuelve la matriz
WebSocket {{"rx":"abc"}}    → conexión cerrada sin aviso (ConnectionClosedError)
POST {{"m":[[NaN]]}}        → 500      suma de matrices irregulares → 200 con resultado incorrecto
determinante 400×400       → 200 (aceptado)</pre>

<h3>Paso 6 · Mitigaciones</h3>
<ul>
<li><b>M1</b> (<code>calculadora_matrices/main.py</code>, <code>repository.py</code>): cada navegador recibe un <code>sid</code> aleatorio y el repositorio filtra por dueño. Ataca la causa, que era la falta de autorización por objeto.</li>
<li><b>M2 y M3</b> (<code>modelo-3D/main.py</code>): el navegador siempre envía <code>Origin</code>; si no está en la lista, el handshake se rechaza. Ya no basta con que la víctima visite una web hostil.</li>
<li><b>M4 y M5</b>: se valida en la entrada (rectangular, finita, tamaños y rangos acotados) y el WebSocket limita tamaño, ritmo y conexiones. Un mensaje inválido recibe <code>error</code> y el canal sigue.</li>
<li><b>Cabeceras</b>: CSP, <code>X-Frame-Options</code>, <code>nosniff</code>, <code>Referrer-Policy</code>, <code>no-store</code>. Para cumplir la CSP se sacó el JS y el CSS a archivos, se reemplazaron los 15 <code>onclick</code> por <code>data-action</code> y se eliminaron Google Fonts y el CDN de three.js.</li>
<li><b>Docker</b>: usuario no root, <code>cap_drop: ALL</code>, puertos solo en 127.0.0.1, dependencias fijadas.</li></ul>

<h3>Paso 7 · Estado final con ZAP</h3>
<p>Misma configuración que el paso 1. La calculadora pasó de 8 a 3 alertas; las que quedan están explicadas en la tabla (CSP de estilos, Modern Web Application y la cookie <code>sid</code>).</p>
{fig("zap/despues_calculadora_8001.png", "Calculadora, después: 3 alertas (0 altas, 1 media, 2 informativas)", "crop")}
{fig("zap/despues_modelo3d_8000.png", "Visor 3D, después", "crop")}
<pre>DESPUÉS (versión corregida)
CORS con Origin hostil     → sin cabeceras access-control (el navegador bloquea la lectura)
GET /matrices (otra sesión)→ []
WebSocket, Origin evil     → handshake rechazado, HTTP 403
WebSocket {{"rx":"abc"}}    → {{"status":"error","detail":"parámetros inválidos"}} y el canal sigue
POST {{"m":[[NaN]]}}        → 422      matrices irregulares → 422      determinante 400×400 → 422</pre>

<h3>Paso 8 · Nada se rompió</h3>
<p>Las 8 pruebas e2e originales siguen pasando y se agregaron 15 de seguridad: <b>14 fallan en la versión vulnerable y todas pasan en la corregida</b> (23 en total). Dos de las pruebas originales cambiaron: elegían la matriz por ID global y solo funcionaban porque todos compartían la misma lista; ahora eligen por posición en la lista propia (esa dependencia era M1).</p>
{fila(fig("despues/calculadora_funciona.png", "Calculadora: A + B = resultado"), fig("despues/visor_funciona.png", "Visor: WebSocket conectado, 10 000 puntos"))}

<h2 class="pb">4. ¿Y si los números fueran datos sensibles?</h2>
<p>Alertas como <i>Retrieved from Cache</i> o HSTS se clasificaron como falsos positivos <b>para este laboratorio</b>. Con montos, cuentas o expedientes dejarían de serlo. Un atacante podría:</p>
<table><tr><th style="width:17%">Hacer</th><th style="width:40%">Cómo (ya demostrado, salvo lo indicado)</th><th>Protección</th></tr>
<tr><td><b>Ver</b> datos de otros</td><td>M1: <code>GET /matrices</code> devolvía todo.</td><td>Autenticación y autorización por objeto; IDs no secuenciales; 404 igual para “no existe” y “no es tuyo”. <span class="ok">Aplicado (sesión).</span></td></tr>
<tr><td><b>Leer</b> el tráfico</td><td>Burp muestra cuerpos y frames en claro.</td><td>TLS (<code>https</code>/<code>wss</code>), HSTS (aquí sí sería real), cookies <code>Secure</code>, cifrado en reposo.</td></tr>
<tr><td><b>Modificar</b> montos</td><td>Sin TLS ni firma se puede alterar una respuesta; con <code>POST</code> abierto, crear o cambiar registros.</td><td>TLS, validación y rangos <span class="ok">(aplicado)</span>, firma/HMAC, auditoría, permisos de escritura separados.</td></tr>
<tr><td><b>Actuar por la víctima</b> desde otra web</td><td>M2 y M3: CSWSH y CORS reflejado.</td><td>Lista de orígenes y <code>SameSite=Strict</code> <span class="ok">(aplicado)</span>; token anti-CSRF para escrituras.</td></tr>
<tr><td><b>Tumbar</b> el servicio o sacar datos de errores</td><td>M4 y M5: entradas enormes, <code>NaN</code>, errores que repetían la entrada.</td><td>Límites, <i>rate limiting</i>, errores genéricos <span class="ok">(aplicado en parte)</span>; no registrar valores sensibles.</td></tr>
<tr><td><b>Recuperar</b> datos de cachés</td><td><i>Retrieved from Cache</i>: copias en navegador, proxy o CDN.</td><td><code>no-store</code> y sin terceros que vean IP o <i>Referer</i> <span class="ok">(aplicado)</span>.</td></tr></table>
<div class="nota">Un dato es sensible por <b>quién puede leerlo o cambiarlo</b>, no por su forma. Una matriz de rotación y una de saldos viajan igual; cambia el costo de que alguien ajeno la vea o la altere.</div>

<h2>5. Conclusión</h2>
<p>ZAP encontró bien lo que se ve en una respuesta HTTP aislada (cabeceras, SRI, recursos de terceros), pero <b>no encontró ninguno de los seis hallazgos más importantes</b>. Esos requieren entender la intención de la app (“estos datos son de cada usuario”), probar con un <code>Origin</code> hostil o un frame mal formado, o notar que sumar matrices irregulares sin error es un fallo de integridad. Además, varias alertas eran falsos positivos según el contexto (HSTS en HTTP local, CORS de Google Fonts) y hay que saber explicarlo. Las herramientas sirven como primer filtro y como red de regresión; la revisión de código, el modelado de amenazas y las pruebas propias son las que cierran el trabajo.</p>

{ANEXOS}
{fila(fig("zap/anexo_a_alertas_antes_calculadora.png", "Anexo A · alertas detalladas de la calculadora, antes"), fig("zap/anexo_a_alertas_antes_modelo3d.png", "Anexo A · alertas detalladas del visor, antes"))}
</body></html>"""

out = E / "reporte_seguridad.html"
out.write_text(HTML, encoding="utf-8")
pdf = E / "reporte_seguridad.pdf"
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", out.as_uri()], check=True, capture_output=True)
print("PDF:", pdf)
