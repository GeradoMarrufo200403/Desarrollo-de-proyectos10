        // URL de la API de modelo-3D: si la página la sirve FastAPI (/view) se usa el mismo servidor;
        // si el HTML se abre aparte (doble clic, Live Server), se usa localhost:8000
        const API_HOST = location.pathname.startsWith('/view') ? location.host : 'localhost:8000';

        // 1. Inicialización de la Escena 3D
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);

        camera.position.set(0, 0, 20);

        // Grupo contenedor cuya matriz será controlada por FastAPI (calculada por la calculadora de matrices)
        const modelGroup = new THREE.Group();
        modelGroup.matrixAutoUpdate = false; // Importante: deshabilitamos auto-update para usar la matriz de la API
        scene.add(modelGroup);

        // Escala por figura: el toroide del CSV es más grande (radio 15) que la esfera y el cubo
        const ESCALAS = { esfera: 1, cubo: 1, toroide: 0.6 };
        const figuraEl = document.getElementById('figura');

        // 2. Cargar los puntos de la figura seleccionada desde FastAPI
        async function cargarFigura(nombre) {
            try {
                const response = await fetch(`http://${API_HOST}/api/figura/${nombre}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const data = await response.json();
                document.getElementById('point-count').textContent = data.total_puntos;

                // Quitar la figura anterior
                modelGroup.clear();

                // Aplanar coordenadas [[x,y,z], ...] -> [x,y,z, x,y,z, ...]
                const vertices = new Float32Array(data.vertices.flat());

                const geometry = new THREE.BufferGeometry();
                geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));

                // Estilo de la nube de puntos
                const material = new THREE.PointsMaterial({ color: 0x8E1EA2, size: 0.08 });
                modelGroup.add(new THREE.Points(geometry, material));
            } catch (err) {
                console.error("Error al cargar la figura:", err);
                document.getElementById('point-count').textContent = 'error al cargar';
            }
        }

        figuraEl.addEventListener('change', () => cargarFigura(figuraEl.value));
        cargarFigura(figuraEl.value);

        // 3. Conexión WebSocket para enviar parámetros y recibir la Matriz 4x4
        const ws = new WebSocket(`ws://${API_HOST}/ws/transform`);
        const statusEl = document.getElementById('ws-status');
        let esperando = false; // una petición a la vez, para no acumular mensajes

        ws.onopen = () => {
            statusEl.textContent = "Conectado";
            statusEl.style.color = "#00ff88";
        };

        ws.onerror = () => {
            statusEl.textContent = "Error de conexión";
            statusEl.style.color = "#ff4444";
        };

        ws.onmessage = (event) => {
            esperando = false;
            const data = JSON.parse(event.data);
            if (data.matrix) {
                // Aplicar la matriz 4x4 calculada por la calculadora de matrices directamente al objeto 3D
                modelGroup.matrix.fromArray(data.matrix);
                modelGroup.matrixWorldNeedsUpdate = true;
            } else if (data.status === 'error') {
                statusEl.textContent = data.detail;
                statusEl.style.color = "#ff4444";
            }
        };

        // 4. Bucle de Animación y Envío de Parámetros
        let angle = 0;
        function animate() {
            requestAnimationFrame(animate);

            // Si el WebSocket está abierto, enviamos ángulos/traslaciones continuas
            if (ws.readyState === WebSocket.OPEN && !esperando) {
                angle += 0.4;
                esperando = true;
                ws.send(JSON.stringify({
                    tx: Math.sin(angle * 0.02) * 0.5,
                    ty: 0,
                    tz: 0,
                    rx: angle,
                    ry: angle * 0.5,
                    rz: 0,
                    escala: ESCALAS[figuraEl.value]
                }));
            }

            renderer.render(scene, camera);
        }

        animate();

        // Ajustar renderizador al cambiar tamaño de la ventana
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
