# Ecosistema de Álgebra Lineal y Modelado 3D — `Desarrollo de proyectos10`

**Autor:** Gerardo Marrufo (`@GeradoMarrufo200403`)  
**Materia:** Implementación e Integración de IA y Automatización de Procesos — 10º Cuatrimestre  

---

## 🏗️ Arquitectura General del Sistema

Este repositorio integra dos microservicios desacoplados en Python (**FastAPI**) junto con su suite de pruebas automatizadas y flujo de agente de IA en **n8n**:

```text
Desarrollo de proyectos10/
├── Calculadora de matrices/        # Microservicio Matemático (Puerto 8000) - Arquitectura en Capas
│   ├── app/
│   │   ├── api/routers/            # Routers modulares: matrices.py, operations.py, figuras.py
│   │   ├── models/                 # Esquemas y validadores Pydantic (models.py)
│   │   ├── repositories/           # Persistencia en memoria (matrix_repo.py)
│   │   ├── services/               # Motor algebraico y paramétrico 3D (matrix_service.py)
│   │   └── main.py                 # Punto de entrada FastAPI + Middleware de Seguridad OWASP
│   └── static/                     # Frontend "Gestor de Matrices - Estilo Excel" (index.html, app.js, styles.css)
│
├── Modelador3D_matrices/           # Microservicio de Renderizado WebGL / Three.js (Puerto 8001)
│   ├── modelos_3d/                 # Nubes de puntos CSV (dona.csv, esfera.csv, piramide.csv)
│   ├── index.html                  # Interfaz "Matrix API Transform" (Diseño Glassmorphism Neón)
│   └── main.py                     # API de modelos CSV y relevo por WebSocket (/ws/transform)
│
├── test_e2e/                       # Suite de pruebas automatizadas (Pytest + Playwright)
├── docker-compose.yaml             # Orquestador unificado de ambos microservicios
├── pyproject.toml                  # Configuración de Ruff (linter) y Pytest
└── requirements-dev.txt            # Dependencias para pruebas locales y análisis estático
```

---

## 🚀 Instrucciones para Inicializar y Probar el Proyecto

### 1. Levantar ambos servicios con Docker Compose
Desde la carpeta raíz del repositorio ejecuta:

```bash
docker compose up --build -d
```

Una vez levantados los contenedores, verifica los servicios en tu navegador:

| Servicio | Puerto Local | Enlace Directo | Descripción |
| :--- | :---: | :--- | :--- |
| **Calculadora de Matrices (UI Estilo Excel)** | `8000` | http://localhost:8000 | Creación de matrices, suma, multiplicación, determinante y transpuesta. |
| **Documentación OpenAPI / Swagger** | `8000` | http://localhost:8000/docs | Especificación interactiva de los routers `/matrices`, `/operaciones` y `/figuras`. |
| **Visor 3D Glassmorphism (`Modelador3D_matrices`)** | `8001` | http://localhost:8001/view | Motor 3D con selector de figuras (`🍩 Dona`, `🔮 Esfera`, `🔺 Pirámide`, `☕ Dona→Taza`). |

---

## ☕ Nueva Funcionalidad (PR `feat/morph-dona-taza`): Deformación Topológica Dona → Taza

1. **En el Microservicio `Calculadora de matrices` (`Puerto 8000`):**
   * **`POST /operaciones/morph-3d`** (y alias `POST /calc/morph`): Calcula la interpolación lineal punto a punto $P(u,v,t) = (1-t)\cdot D(u,v) + t\cdot T(u,v)$ para $t \in [0, 1]$ y `resolucion` $\in [4, 100]$, devolviendo los vértices 3D, el estado topológico y una tabla `resumen_markdown` con la caja envolvente (*bounding box*) lista para **n8n**.
   * **Router modular `app/api/routers/figuras.py`:**
     * `POST /figuras`: Guarda o actualiza (idempotente por nombre) una configuración de figura con validación contra nombres vacíos o etiquetas HTML/XSS.
     * `GET /figuras` y `GET /figuras/{id}`: Consulta las figuras almacenadas.
     * `DELETE /figuras/{id}`: Elimina una figura por su identificador.

2. **En el Visor 3D `Modelador3D_matrices` (`http://localhost:8001/view`):**
   * Nuevo botón **`☕ Dona→Taza`** en el panel *Glassmorphism* que despliega el control deslizante **Morph Topológico (Dona → Taza)** (`0%` a `100%`), interpola dinámicamente el color neón de la nube de puntos (`#00ffaa` $\rightarrow$ `#ff3399`) y permite guardar la figura con nombre personalizado a través del WebSocket `/ws/transform`.

---

## 🧪 Ejecución de Pruebas y Análisis Estático (Calidad)

Para instalar las herramientas de desarrollo y correr las pruebas localmente:

```bash
pip install -r requirements-dev.txt

# 1. Ejecutar pruebas de morph, regresión de seguridad OWASP y visor (sin requerir navegador)
pytest test_e2e/test_morph.py test_e2e/test_regresion_seguridad.py test_e2e/test_vision.py -v

# 2. Ejecutar pruebas E2E de navegador con Playwright (con los contenedores corriendo)
playwright install chromium
pytest test_e2e/test_calculadora.py test_e2e/test_humo.py -v

# 3. Ejecutar análisis estático con Ruff
ruff check "Calculadora de matrices" "Modelador3D_matrices" "test_e2e"
```
