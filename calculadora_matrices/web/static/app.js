        let currentRows = 2;
        let currentCols = 2;
        let currentMode = 'grid'; // 'grid' | 'text'
        let currentOp = 'sumar'; // 'sumar' | 'multiplicar' | 'transponer' | 'determinante'
        let matricesGuardadas = [];

        window.addEventListener('DOMContentLoaded', () => {
            renderGrid();
            cargarMatrices();
            updateOpUI();
        });

        function setMode(mode) {
            currentMode = mode;
            document.getElementById('tabGrid').classList.toggle('active', mode === 'grid');
            document.getElementById('tabText').classList.toggle('active', mode === 'text');
            document.getElementById('gridEditorView').style.display = mode === 'grid' ? 'flex' : 'none';
            document.getElementById('gridDimensions').style.display = mode === 'grid' ? 'flex' : 'none';
            document.getElementById('textEditorView').style.display = mode === 'text' ? 'flex' : 'none';

            if (mode === 'text') {
                const data = extraerDatosGrid();
                document.getElementById('quickTextInput').value = data.map(r => r.join(' ')).join('\n');
            }
        }

        function setOperation(op) {
            currentOp = op;
            ['sumar', 'multiplicar', 'transponer', 'determinante'].forEach(o => {
                const btn = document.getElementById('op' + o.charAt(0).toUpperCase() + o.slice(1));
                if (btn) btn.classList.toggle('active', o === op);
            });
            updateOpUI();
        }

        function updateOpUI() {
            const containerM2 = document.getElementById('containerM2');
            const opSymbol = document.getElementById('opSymbol');
            const labelM1 = document.getElementById('labelM1');
            const btnEjecutar = document.getElementById('btnEjecutarOp');

            if (currentOp === 'sumar') {
                containerM2.style.display = 'flex';
                opSymbol.style.display = 'block';
                opSymbol.textContent = '+';
                labelM1.textContent = 'Matriz 1 (A)';
                btnEjecutar.innerHTML = '<span>➕ Calcular Suma</span>';
            } else if (currentOp === 'multiplicar') {
                containerM2.style.display = 'flex';
                opSymbol.style.display = 'block';
                opSymbol.textContent = '×';
                labelM1.textContent = 'Matriz 1 (A)';
                btnEjecutar.innerHTML = '<span>✖️ Calcular Multiplicación</span>';
            } else if (currentOp === 'transponer') {
                containerM2.style.display = 'none';
                opSymbol.style.display = 'none';
                labelM1.textContent = 'Matriz (A)';
                btnEjecutar.innerHTML = '<span>🔄 Obtener Transpuesta</span>';
            } else if (currentOp === 'determinante') {
                containerM2.style.display = 'none';
                opSymbol.style.display = 'none';
                labelM1.textContent = 'Matriz Cuadrada (A)';
                btnEjecutar.innerHTML = '<span>🎯 Calcular Determinante</span>';
            }
        }

        function changeDim(type, delta) {
            if (type === 'rows') {
                currentRows = Math.max(1, Math.min(6, currentRows + delta));
                document.getElementById('rowsCount').textContent = currentRows;
            } else {
                currentCols = Math.max(1, Math.min(6, currentCols + delta));
                document.getElementById('colsCount').textContent = currentCols;
            }
            renderGrid();
        }

        function renderGrid() {
            const container = document.getElementById('matrixGrid');
            container.style.gridTemplateColumns = `repeat(${currentCols}, 1fr)`;
            container.innerHTML = '';

            for (let r = 0; r < currentRows; r++) {
                for (let c = 0; c < currentCols; c++) {
                    const input = document.createElement('input');
                    input.type = 'number';
                    input.step = 'any';
                    input.className = 'matrix-cell';
                    input.dataset.row = r;
                    input.dataset.col = c;
                    input.placeholder = '0';
                    input.value = '0';

                    input.addEventListener('keydown', (e) => handleKeyNav(e, r, c));
                    container.appendChild(input);
                }
            }
        }

        function handleKeyNav(e, r, c) {
            let targetR = r;
            let targetC = c;

            if (e.key === 'ArrowRight' && c < currentCols - 1) targetC++;
            else if (e.key === 'ArrowLeft' && c > 0) targetC--;
            else if (e.key === 'ArrowDown' && r < currentRows - 1) targetR++;
            else if (e.key === 'ArrowUp' && r > 0) targetR--;
            else if (e.key === 'Enter') {
                if (c < currentCols - 1) targetC++;
                else if (r < currentRows - 1) { targetR++; targetC = 0; }
            } else return;

            const nextCell = document.querySelector(`.matrix-cell[data-row="${targetR}"][data-col="${targetC}"]`);
            if (nextCell) {
                e.preventDefault();
                nextCell.focus();
                nextCell.select();
            }
        }

        function extraerDatosGrid() {
            const matrix = [];
            for (let r = 0; r < currentRows; r++) {
                const row = [];
                for (let c = 0; c < currentCols; c++) {
                    const cell = document.querySelector(`.matrix-cell[data-row="${r}"][data-col="${c}"]`);
                    const val = parseFloat(cell.value);
                    row.push(isNaN(val) ? 0 : val);
                }
                matrix.push(row);
            }
            return matrix;
        }

        function extraerDatosTexto() {
            const raw = document.getElementById('quickTextInput').value.trim();
            if (!raw) throw new Error('El campo de texto no puede estar vacío');

            const lineas = raw.split('\n').map(l => l.trim()).filter(l => l.length > 0);
            if (lineas.length === 0) throw new Error('Ingresa al menos una fila con números');

            const matrix = lineas.map(linea => {
                const nums = linea.split(/[\s,]+/).filter(n => n.length > 0).map(n => {
                    const num = parseFloat(n);
                    if (isNaN(num)) throw new Error(`"${n}" no es un número válido`);
                    return num;
                });
                return nums;
            });

            const primerLargo = matrix[0].length;
            if (primerLargo === 0) throw new Error('Las filas no pueden estar vacías');
            for (let i = 1; i < matrix.length; i++) {
                if (matrix[i].length !== primerLargo) {
                    throw new Error(`Fila ${i + 1} tiene ${matrix[i].length} números, pero la primera tiene ${primerLargo}. Todas deben ser iguales.`);
                }
            }

            return matrix;
        }

        function fillRandom() {
            document.querySelectorAll('.matrix-cell').forEach(cell => {
                cell.value = Math.floor(Math.random() * 19) - 9;
            });
        }

        function clearGrid() {
            document.querySelectorAll('.matrix-cell').forEach(cell => {
                cell.value = '0';
            });
        }

        async function guardarMatriz() {
            const nombre = document.getElementById('matrixName').value.trim() || 'A';
            let datos;

            try {
                if (currentMode === 'grid') {
                    datos = extraerDatosGrid();
                } else {
                    datos = extraerDatosTexto();
                }
            } catch (err) {
                mostrarToast(err.message, 'error');
                return;
            }

            try {
                const r = await fetch('/matrices', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombre, datos })
                });

                const res = await r.json();

                if (!r.ok) {
                    const errorDetail = res.detail ? (Array.isArray(res.detail) ? res.detail[0].msg : res.detail) : 'Error al crear matriz';
                    mostrarToast(errorDetail, 'error');
                    return;
                }

                mostrarToast(`¡Matriz "${res.nombre}" (ID: ${res.id}) guardada con éxito!`, 'success');
                
                const nextChar = String.fromCharCode(nombre.charCodeAt(0) + 1);
                if (/^[A-Z]$/.test(nextChar)) {
                    document.getElementById('matrixName').value = nextChar;
                }

                cargarMatrices();
            } catch (err) {
                mostrarToast('Error de conexión: ' + err.message, 'error');
            }
        }

        async function cargarMatrices() {
            const listEl = document.getElementById('matrixList');
            const countEl = document.getElementById('matricesCount');
            const selectM1 = document.getElementById('selectM1');
            const selectM2 = document.getElementById('selectM2');

            try {
                const r = await fetch('/matrices');
                if (!r.ok) throw new Error('Error al obtener matrices');
                
                matricesGuardadas = await r.json();
                countEl.textContent = matricesGuardadas.length;

                const prevM1 = selectM1.value;
                const prevM2 = selectM2.value;

                selectM1.innerHTML = '<option value="">Seleccionar matriz 1...</option>';
                selectM2.innerHTML = '<option value="">Seleccionar matriz 2...</option>';

                if (matricesGuardadas.length === 0) {
                    listEl.innerHTML = '<p class="empty-placeholder" style="text-align: center; margin-top: 40px;">No hay matrices creadas aún. Crea tu primera matriz a la izquierda.</p>';
                    return;
                }

                listEl.innerHTML = '';
                matricesGuardadas.forEach(m => {
                    const rows = m.datos.length;
                    const cols = m.datos[0]?.length || 0;

                    const opt1 = document.createElement('option');
                    opt1.value = m.id;
                    opt1.textContent = `[ID ${m.id}] ${m.nombre} (${rows}×${cols})`;
                    selectM1.appendChild(opt1);

                    const opt2 = document.createElement('option');
                    opt2.value = m.id;
                    opt2.textContent = `[ID ${m.id}] ${m.nombre} (${rows}×${cols})`;
                    selectM2.appendChild(opt2);

                    const item = document.createElement('div');
                    item.className = 'matrix-item';
                    item.innerHTML = `
                        <div class="matrix-info">
                            <span class="matrix-badge-id">#${m.id}</span>
                            <div>
                                <div class="matrix-name">${escapeHtml(m.nombre)}</div>
                                <div class="matrix-size">${rows} × ${cols}</div>
                            </div>
                        </div>
                        <div>
                            ${renderMiniMatrixHTML(m.datos)}
                        </div>
                    `;
                    listEl.appendChild(item);
                });

                selectM1.value = prevM1;
                selectM2.value = prevM2;

            } catch (err) {
                listEl.innerHTML = `<p class="empty-placeholder" style="color: #fca5a5; text-align: center;">Error al cargar matrices: ${err.message}</p>`;
            }
        }

        function renderMiniMatrixHTML(datos) {
            if (!datos || datos.length === 0) return '';
            const rowsHTML = datos.map(row => 
                `<div class="mini-row">${row.map(val => `<span style="min-width: 22px; text-align: center;">${val}</span>`).join('')}</div>`
            ).join('');
            return `<div class="mini-matrix">${rowsHTML}</div>`;
        }

        async function ejecutarOperacion() {
            const id1 = document.getElementById('selectM1').value;
            const id2 = document.getElementById('selectM2').value;
            const resContainer = document.getElementById('resultContainer');

            if (!id1) {
                mostrarToast('Por favor selecciona la matriz para operar', 'error');
                return;
            }

            if ((currentOp === 'sumar' || currentOp === 'multiplicar') && !id2) {
                mostrarToast('Por favor selecciona ambas matrices para la operación', 'error');
                return;
            }

            const m1 = matricesGuardadas.find(m => m.id == id1);
            const m2 = matricesGuardadas.find(m => m.id == id2);

            let endpoint = '';
            if (currentOp === 'sumar') endpoint = `/operaciones/sumar?id1=${id1}&id2=${id2}`;
            else if (currentOp === 'multiplicar') endpoint = `/operaciones/multiplicar?id1=${id1}&id2=${id2}`;
            else if (currentOp === 'transponer') endpoint = `/operaciones/transponer?id=${id1}`;
            else if (currentOp === 'determinante') endpoint = `/operaciones/determinante?id=${id1}`;

            try {
                const r = await fetch(endpoint, { method: 'POST' });
                const res = await r.json();

                if (!r.ok) {
                    const detail = res.detail || 'Error en la operación';
                    mostrarToast(detail, 'error');
                    resContainer.innerHTML = `<p class="empty-placeholder" style="color: #fca5a5;">❌ ${escapeHtml(detail)}</p>`;
                    return;
                }

                mostrarToast('¡Operación realizada con éxito!', 'success');

                if (currentOp === 'sumar' || currentOp === 'multiplicar') {
                    const sign = currentOp === 'sumar' ? '+' : '×';
                    resContainer.innerHTML = `
                        <div class="result-display">
                            <div style="text-align: center;">
                                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">${escapeHtml(m1.nombre)} (#${m1.id})</div>
                                ${renderMiniMatrixHTML(m1.datos)}
                            </div>
                            <div class="op-sign">${sign}</div>
                            <div style="text-align: center;">
                                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">${escapeHtml(m2.nombre)} (#${m2.id})</div>
                                ${renderMiniMatrixHTML(m2.datos)}
                            </div>
                            <div class="op-sign">=</div>
                            <div style="text-align: center;">
                                <div style="font-size: 0.8rem; color: #6ee7b7; font-weight: bold; margin-bottom: 4px;">Resultado (${res.resultado.length}×${res.resultado[0]?.length || 0})</div>
                                ${renderMiniMatrixHTML(res.resultado)}
                            </div>
                        </div>
                    `;
                } else if (currentOp === 'transponer') {
                    resContainer.innerHTML = `
                        <div class="result-display">
                            <div style="text-align: center;">
                                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">${escapeHtml(m1.nombre)} (${m1.datos.length}×${m1.datos[0]?.length || 0})</div>
                                ${renderMiniMatrixHTML(m1.datos)}
                            </div>
                            <div class="op-sign">ᵀ =</div>
                            <div style="text-align: center;">
                                <div style="font-size: 0.8rem; color: #6ee7b7; font-weight: bold; margin-bottom: 4px;">Transpuesta (${res.resultado.length}×${res.resultado[0]?.length || 0})</div>
                                ${renderMiniMatrixHTML(res.resultado)}
                            </div>
                        </div>
                    `;
                } else if (currentOp === 'determinante') {
                    resContainer.innerHTML = `
                        <div class="result-display">
                            <div style="text-align: center;">
                                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">|${escapeHtml(m1.nombre)}|</div>
                                ${renderMiniMatrixHTML(m1.datos)}
                            </div>
                            <div class="op-sign">=</div>
                            <div style="text-align: center;">
                                <div style="font-size: 0.8rem; color: #38bdf8; font-weight: bold; margin-bottom: 6px;">Determinante det(A)</div>
                                <div class="scalar-result">${res.resultado}</div>
                            </div>
                        </div>
                    `;
                }

            } catch (err) {
                mostrarToast('Error al conectar con el servidor: ' + err.message, 'error');
            }
        }

        function mostrarToast(msg, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.className = `toast toast-${type} show`;
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3500);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

// Los manejadores ya no están en línea (onclick=...): la CSP prohíbe script inline.
// Se delegan por data-action, solo para funciones de esta lista.
const ACCIONES = { cargarMatrices, changeDim, clearGrid, ejecutarOperacion, fillRandom, guardarMatriz, setMode, setOperation };
document.addEventListener('click', (ev) => {
    const el = ev.target.closest('[data-action]');
    if (!el) return;
    const fn = ACCIONES[el.dataset.action];
    if (fn) fn(...JSON.parse(el.dataset.args || '[]'));
});

