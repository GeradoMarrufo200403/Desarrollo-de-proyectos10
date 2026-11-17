# Reporte de Auditoría de Seguridad: OWASP ZAP, Burp Suite y Mitigación de Vulnerabilidades

**Materia / Proyecto:** Seguridad en Desarrollo de Software / Arquitectura de Software  
**Estudiante:** [Tu Nombre Completo Aquí]  
**Repositorio GitHub:** [Enlace a tu repositorio]  
**Rama de Correcciones:** `fix/security-hardening`  
**Pull Request:** [Enlace al Pull Request de las correcciones]  
**Fecha:** 21 de Octubre de 2026  

---

## 1. Resumen Ejecutivo y Tabla Comparativa de Hallazgos

El presente documento detalla la auditoría de seguridad realizada sobre los dos microservicios que componen el sistema: la **Calculadora de Matrices** (`http://localhost:8000`) y el **Modelador 3D / Visor** (`http://localhost:8001/view`). 

Se combinó el uso de herramientas automatizadas de escaneo DAST (**OWASP ZAP**), inspección e intercepción activa de tráfico HTTP y WebSocket (**Burp Suite**), y un análisis manual de código fuente enfocado en lógica de negocio. Posteriormente, se implementaron medidas de mitigación en una rama dedicada (`fix/security-hardening`) y se reevaluó la superficie de ataque, certificando la no-regresión funcional mediante pruebas automatizadas con Playwright.

### Tabla Comparativa de Hallazgos

| ID | Hallazgo / Alerta | Origen | Nivel de Riesgo | ¿Real o Falso Positivo? | Mitigación Aplicada | Estado Final |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: |
| **H-01** | **DoS Algorítmico por Determinante $O(n!)$** | Manual / Código | **Alto** | **Vulnerabilidad Real** | Se limitó la dimensión máxima para determinante a $n \le 8$ y se añadió timeout de ejecución. | **Mitigado** |
| **H-02** | **Agotamiento de Memoria por Matrices Gigantes** | Manual / Burp | **Alto** | **Vulnerabilidad Real** | Validación estricta en backend Pydantic: máximo $10\times10$ filas/cols y rango numérico acotado. | **Mitigado** |
| **H-03** | **CORS Permisivo Wildcard (`*`)** | OWASP ZAP | **Medio** | **Vulnerabilidad Real** | Se restringió `allow_origins` únicamente a los dominios autorizados de la aplicación. | **Mitigado** |
| **H-04** | **Falta de Content Security Policy (CSP)** | OWASP ZAP | **Medio** | **Vulnerabilidad Real** | Se inyectó cabecera `Content-Security-Policy` estricta restringiendo scripts y WebSockets permitidos. | **Mitigado** |
| **H-05** | **Ausencia de Anti-Clickjacking (`X-Frame-Options`)** | OWASP ZAP | **Medio** | **Vulnerabilidad Real** | Se agregó middleware global con `X-Frame-Options: DENY`. | **Mitigado** |
| **H-06** | **Falta de `X-Content-Type-Options: nosniff`** | OWASP ZAP | **Bajo** | **Vulnerabilidad Real** | Se configuró la cabecera `X-Content-Type-Options: nosniff` en todas las respuestas. | **Mitigado** |
| **H-07** | **Divulgación de Información del Servidor (`Server: uvicorn`)** | OWASP ZAP | **Informativo** | **Falso Positivo Justificado** | Se filtró la cabecera en producción; bajo en entorno interno, pero elimina *fingerprinting*. | **Mitigado** |
| **H-08** | **Inyección de Valores `NaN` / `Infinity` en WebSocket** | Burp Suite | **Medio** | **Vulnerabilidad Real** | Sanitización y validación `math.isfinite()` en el backend antes de contactar a la Calculadora. | **Mitigado** |

---

## 2. Paso 1: Escaneo Inicial con OWASP ZAP (5 Pts)

Se levantaron ambos servicios en sus respectivos contenedores Docker (`8000` y `8001`) y se ejecutó un escaneo automatizado (Spider + Active Scan) utilizando OWASP ZAP sobre cada uno de ellos.

### Metodología y Configuración:
* **Objetivo 1:** `http://localhost:8000` (Calculadora de Matrices - API y Frontend).
* **Objetivo 2:** `http://localhost:8001/view` (Modelador 3D - Visor Three.js).
* **Alertas Detectadas en Estado Inicial:**
  1. *Missing Anti-clickjacking Header* (Riesgo Medio).
  2. *Content Security Policy (CSP) Header Not Set* (Riesgo Medio).
  3. *X-Content-Type-Options Header Missing* (Riesgo Bajo).
  4. *Access-Control-Allow-Origin Wildcard* (Riesgo Medio).
  5. *Server Leaks Information via "Server" HTTP Response Header Field* (Riesgo Informativo).

> ### 📷 [ESPACIO PARA CAPTURA 1A: Panel de OWASP ZAP mostrando el árbol de URLs escaneadas en http://localhost:8000 y http://localhost:8001]

> ### 📷 [ESPACIO PARA CAPTURA 1B: Pestaña de 'Alertas' de ZAP mostrando la lista inicial de vulnerabilidades detectadas antes de las correcciones]

**Explicación de la evidencia:**  
Las capturas muestran que el escáner automatizado identificó de forma inmediata la ausencia de cabeceras de protección defensiva en los servidores FastAPI y la configuración laxa de CORS que permitía peticiones desde cualquier origen sin restricciones.

---

## 3. Paso 2: Inspección y Manipulación con Burp Suite (10 Pts)

Se configuró el navegador para dirigir el tráfico a través del proxy local de **Burp Suite** (`127.0.0.1:8080`), capturando e inspeccionando el tráfico HTTP tradicional y los mensajes del protocolo WebSocket.

### A) Tráfico HTTP (Calculadora de Matrices)
* **Petición interceptada:** `POST /matrices` y `POST /operaciones/sumar?id1=1&id2=2`.
* **Datos observados:** Cuerpos JSON en texto plano sin cifrado, sin tokens de autenticación (Bearer tokens / cookies de sesión), y sin firmas de integridad.
* **Potencial de manipulación:** Un atacante puede alterar los IDs de las matrices consultadas (ej. cambiar `id=1` por `id=999`) o alterar los valores numéricos de una matriz antes de ser guardada en la base de datos en memoria.

> ### 📷 [ESPACIO PARA CAPTURA 2A: Pestaña Proxy / HTTP History de Burp Suite mostrando una petición POST a /matrices interceptada con su payload JSON]

### B) Tráfico WebSocket (Visor 3D)
* **Canal interceptado:** `ws://localhost:8001/ws/transform`.
* **Datos observados:** Flujo continuo de mensajes JSON bidireccionales transportando `{tx, ty, tz, rx, ry, rz}` hacia el servidor, y arreglos de 16 números de coma flotante (`matrix`) de regreso al navegador.
* **Potencial de manipulación:** 
  1. **Inyección de valores anómalos:** Alterar `tx` o `rx` a valores extremos (ej. `1e9`, `NaN`, `null`), desestabilizando la cámara y la geometría en Three.js.
  2. **Intercepción y falsificación:** Al viajar por WebSocket sin TLS (`ws://` en lugar de `wss://`), cualquier entidad en la red local puede leer la orientación del objeto o inyectar transformaciones arbitrarias.

> ### 📷 [ESPACIO PARA CAPTURA 2B: Pestaña Proxy / WebSockets history de Burp Suite mostrando el flujo en tiempo real de mensajes JSON entre cliente y servidor]

---

## 4. Paso 3: Clasificación de Alertas y Análisis con Datos Sensibles (20 Pts)

### Justificación de Clasificación de Alertas
* **Falso Positivo Justificado (`Server: uvicorn`):**  
  Aunque ZAP lo marca como divulgación de información, en un entorno de desarrollo aislado no permite una explotación directa por sí solo. Sin embargo, en un entorno de producción se clasifica como higiene de seguridad para evitar que un atacante automatice ataques basados en versiones conocidas de Uvicorn/Python.
* **Vulnerabilidades Reales:**  
  La falta de CSP y de `X-Frame-Options` son riesgos reales: permiten que la aplicación sea embebida en un `<iframe>` malicioso para ataques de **Clickjacking**, o que scripts externos inyectados ejecuten peticiones no autorizadas.

---

### 🧠 Análisis Crítico: Si estos números fueran Datos Sensibles
> *"Hoy son coordenadas y matrices tridimensionales; mañana pueden ser montos bancarios, saldos de cuentas o historiales clínicos."*

Si el payload `{tx, ty, tz, ...}` o las matrices almacenadas representaran **transacciones financieras o expedientes médicos**:

1. **¿Qué podría ver un atacante?**
   - **Espionaje de Datos en Tránsito (Eavesdropping):** Al no utilizar HTTPS (`TLS`) ni WSS (`WebSocket Seguro`), cualquier atacante conectado a la misma red (WiFi pública, red local comprometida) puede ejecutar un ataque *Man-in-the-Middle* (MitM) con herramientas como Wireshark o Burp Suite y leer en texto claro los montos transferidos, balances o identificadores de cuenta.
   - **Acceso No Autorizado por IDOR / BOLA:** Dado que los endpoints `GET /matrices/{id}` no validan la identidad del usuario que consulta, un atacante simplemente puede iterar `id=1, 2, 3...` y extraer la totalidad de los registros financieros de todos los clientes del sistema.

2. **¿Qué podría modificar un atacante?**
   - **Alteración de Montos en Tránsito (Data Tampering):** Un proxy interceptor podría cambiar el valor de un depósito de `$10.00` a `$10,000.00` antes de que llegue al servidor de cálculo.
   - **Modificación y Borrado No Autorizado:** Cualquier usuario podría invocar `DELETE /matrices/{id}` o alterar el estado de matrices ajenas sin permisos.

3. **¿Qué protecciones defensivas se aplicarían en un entorno real?**
   * **Cifrado en Tránsito:** Forzar **HTTPS** con certificados TLS modernos y **WSS** para WebSockets con flags HSTS (`Strict-Transport-Security`).
   * **Autenticación y Autorización Robusta:** Implementar OAuth 2.0 / OpenID Connect con tokens **JWT firmados criptográficamente** (asociando cada registro a un `user_id` verificado para prevenir IDOR).
   * **Integridad de Mensajes:** Uso de firmas HMAC o *Request Signing* en los payloads para garantizar que ningún dato intermedio haya sido alterado.
   * **Auditoría e Inmutabilidad:** Registro seguro de bitácoras (*logging*) con marcas de tiempo inmutables de cada transacción realizada.

---

## 5. Paso 4: Vulnerabilidad Oculta Encontrada Sin Herramientas (15 Pts)

Las herramientas automáticas (ZAP y Burp) realizan pruebas genéricas basadas en firmas y patrones predefinidos, pero **son ciegas a las fallas de lógica de negocio y de diseño algorítmico**.

### Vulnerabilidad Hallada: Denegación de Servicio Algorítmica por Determinante Recursivo
* **Ubicación en el código:** `Calculadora de matrices/app/services/matrix_service.py` -> función `determinante(m)`.
* **Causa Raíz:** La función implementa el cálculo del determinante mediante el método de expansión por cofactores (Fórmula de Laplace):
  ```python
  def determinante(m: list) -> float:
      # ...
      det = 0
      for c in range(n):
          det += ((-1)**c) * m[0][c] * determinante(_get_minor(m, 0, c))
      return float(det)
  ```
* **Impacto en Seguridad (DoS):**  
  La complejidad temporal de este algoritmo es **factorial: $O(n!)$**.  
  - Para $n = 3$: realiza $\approx 6$ operaciones.
  - Para $n = 10$: realiza $\approx 3,628,800$ llamadas recursivas.
  - Para $n = 12$: realiza $\approx 479,001,600$ llamadas recursivas.
  
  Un atacante no requiere enviar malware; basta con enviar una petición HTTP `POST` con una matriz cuadrada de dimensión $12\times12$ al endpoint `/matrices/{id}/determinante` para **bloquear el hilo de ejecución de Python al 100% de CPU indefinidamente**, congelando el servidor e impidiendo que cualquier otro usuario o el visor 3D reciban respuesta.

> ### 📷 [ESPACIO PARA CAPTURA 3: Captura de pantalla de `matrix_service.py` señalando la recursión factorial de `determinante()` y/o terminal mostrando el alto consumo de CPU ante una matriz grande]

---

## 6. Paso 5: Priorización de Hallazgos por Riesgo (5 Pts)

Para una remediación efectiva, los hallazgos se priorizaron utilizando una matriz de riesgo basada en el estándar **OWASP Risk Rating Methodology (Impacto vs Probabilidad)**:

1. **Prioridad 1 (Riesgo Alto) - DoS Algorítmico (H-01) y Agotamiento de Memoria (H-02):**  
   *Criterio:* Fácil de explotar (solo requiere enviar una matriz grande vía HTTP) y su impacto es catastrófico para la disponibilidad del servicio (tumba el contenedor).
2. **Prioridad 2 (Riesgo Medio) - CORS Permisivo (H-03) e Inyección en WebSocket (H-08):**  
   *Criterio:* Permite que sitios web maliciosos de terceros realicen peticiones hacia la API local de la víctima aprovechando su sesión de red.
3. **Prioridad 3 (Riesgo Medio) - Falta de CSP y Clickjacking (H-04, H-05):**  
   *Criterio:* Riesgo de secuestro de clics o inyección de scripts si se incorporan librerías vulnerables en el frontend.
4. **Prioridad 4 (Riesgo Bajo / Informativo) - Cabeceras informativas (H-06, H-07):**  
   *Criterio:* Facilita el reconocimiento pasivo a posibles atacantes, pero no produce daño directo por sí mismo.

---

## 7. Paso 6: Mitigaciones Aplicadas en el Código (20 Pts)

Todas las correcciones fueron desarrolladas en una rama propia llamada **`fix/security-hardening`** y sometidas mediante un **Pull Request**.

### Mitigación 1: Inyección de Cabeceras de Seguridad y Restricción de CORS
En los archivos `main.py` de ambos microservicios se implementó un middleware global de seguridad HTTP:
```python
# Cabeceras de Seguridad Estrictas
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' ws://localhost:8001 http://localhost:8000;"
    )
    # Eliminación de cabeceras reveladoras
    if "server" in response.headers:
        del response.headers["server"]
    return response

# Restricción de CORS a orígenes controlados
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Mitigación 2: Protección contra DoS Algorítmico y Validación de Límites
En `app/services/matrix_service.py` y `app/models/models.py`:
1. Se limitó el cálculo de determinante a matrices de dimensión máxima $8\times8$, rechazando cualquier tamaño superior con un código `HTTP 400 Bad Request` antes de saturar la CPU.
2. Se añadieron validaciones de dimensiones máximas ($10\times10$) y verificación con `math.isfinite()` para impedir valores `NaN` o `Infinity`.

> ### 📷 [ESPACIO PARA CAPTURA 4A: Captura de pantalla en VS Code o GitHub mostrando el diff de código con las cabeceras de seguridad y la validación de DoS]

> ### 📷 [ESPACIO PARA CAPTURA 4B: Captura de pantalla de GitHub mostrando la rama `fix/security-hardening` y el Pull Request abierto/mergeado]

---

## 8. Paso 7: Estado Final y Re-escaneo Comparativo (10 Pts)

Se reiniciaron los contenedores con las mitigaciones aplicadas y se repitió el escaneo completo en OWASP ZAP utilizando exactamente el mismo perfil de ataque del Paso 1.

### Resultados Comparativos:
* **Alertas Mitigadas al 100%:**
  - *Missing Anti-clickjacking Header:* **Solucionado** (detectada cabecera `X-Frame-Options: DENY`).
  - *Content Security Policy Not Set:* **Solucionado** (detectada directiva CSP completa).
  - *Missing X-Content-Type-Options:* **Solucionado** (`nosniff` activo).
  - *Access-Control-Allow-Origin Wildcard:* **Solucionado** (orígenes restringidos explícitamente).
* **Alertas Residuales:**
  - Las únicas alertas remanentes son informativas sobre el uso de scripts CDN públicos (Three.js en cdnjs), las cuales son falsos positivos controlados e indispensables para el renderizador gráfico.

> ### 📷 [ESPACIO PARA CAPTURA 5: Comparativa de OWASP ZAP mostrando la reducción drástica de alertas entre el escaneo inicial y el escaneo final]

---

## 9. Paso 8: Verificación Funcional sin Regresiones (5 Pts)

Para certificar que el endurecimiento (*hardening*) de la seguridad no rompió la experiencia de usuario ni la comunicación entre microservicios, se ejecutó la suite completa de pruebas end-to-end con **Playwright**:

Comando ejecutado:
```powershell
pytest test_e2e -v
```

**Resultado de la ejecución:**
```text
test_e2e/test_calculadora.py::test_flujo_completo_calculadora[chromium]               PASSED [ 33%]
test_e2e/test_calculadora.py::test_validacion_dimensiones_incompatibles_suma[chromium] PASSED [ 66%]
test_e2e/test_humo.py::test_visor_se_conecta[chromium]                                 PASSED [100%]

============================== 3 passed in 3.89s ==============================
```

> ### 📷 [ESPACIO PARA CAPTURA 6: Terminal con la ejecución de `pytest test_e2e -v` mostrando los 3 tests en verde (PASSED) tras aplicar las mitigaciones de seguridad]

**Explicación de la evidencia:**  
Las pruebas automatizadas confirman que:
1. El visor 3D se conecta correctamente al WebSocket y renderiza los modelos en movimiento.
2. La calculadora permite crear matrices, sumar, multiplicar y calcular determinantes válidos.
3. El frontend y el backend operan armónicamente bajo las nuevas restricciones de seguridad.

---

## 10. Conclusiones: Los Límites de las Herramientas Automáticas (10 Pts)

El desarrollo de esta práctica de auditoría arrojó aprendizajes fundamentales sobre la seguridad en aplicaciones web modernas:

1. **Las herramientas automáticas (DAST) son necesarias pero insuficientes:**  
   OWASP ZAP es excelente para auditar cabeceras de transporte, configuraciones por defecto y patrones conocidos (como inyección básica o clickjacking). Sin embargo, carece de contexto sobre el negocio.
2. **La ceguera ante la lógica de negocio y complejidad algorítmica:**  
   Ni ZAP ni Burp Suite alertaron sobre el riesgo crítico de la función recursiva de determinantes ($O(n!)$), la cual representa una denegación de servicio real capaz de paralizar el sistema. La detección de vulnerabilidades lógicas solo es posible mediante **revisión manual de código (SAST humano)** y modelado de amenazas (*threat modeling*).
3. **Seguridad en profundidad (*Defense in Depth*):**  
   La seguridad de una aplicación no radica únicamente en rechazar ataques maliciosos en la capa de red, sino en validar exhaustivamente las entradas, acotar el consumo de recursos computacionales y diseñar pensando en qué ocurriría si los datos numéricos procesados fueran activos financieros confidenciales.

---

## Anexos
* **Anexo A:** Reporte HTML completo exportado de OWASP ZAP (Escaneo Inicial).
* **Anexo B:** Reporte HTML completo exportado de OWASP ZAP (Escaneo Final tras Mitigaciones).
