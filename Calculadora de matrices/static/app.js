const API_URL = "http://localhost:8000";

let matricesCache = [];

function getMatrixName(id) {
    return String.fromCharCode(64 + id); // 1->A, 2->B, etc.
}

function showAlert(message) {
    const banner = document.getElementById("alert-banner");
    const msg = document.getElementById("alert-message");
    msg.textContent = message;
    banner.classList.remove("hidden");
    setTimeout(() => banner.classList.add("hidden"), 3000);
}

function generarInputsMatriz() {
    const rows = parseInt(document.getElementById("rows").value);
    const cols = parseInt(document.getElementById("cols").value);
    const container = document.getElementById("matrix-inputs");
    container.innerHTML = "";

    for (let i = 0; i < rows; i++) {
        const rowDiv = document.createElement("div");
        rowDiv.className = "matrix-row";
        for (let j = 0; j < cols; j++) {
            const input = document.createElement("input");
            input.type = "number";
            input.value = "0";
            input.step = "any";
            input.dataset.row = i;
            input.dataset.col = j;
            rowDiv.appendChild(input);
        }
        container.appendChild(rowDiv);
    }
}

async function crearMatriz() {
    const inputs = document.querySelectorAll("#matrix-inputs input");
    if (inputs.length === 0) {
        alert("Primero configura la matriz");
        return;
    }
    
    const rows = parseInt(document.getElementById("rows").value);
    const cols = parseInt(document.getElementById("cols").value);
    
    let datos = Array.from({length: rows}, () => Array(cols).fill(0));
    
    inputs.forEach(input => {
        const r = parseInt(input.dataset.row);
        const c = parseInt(input.dataset.col);
        datos[r][c] = parseFloat(input.value);
    });

    try {
        const res = await fetch(`${API_URL}/matrices`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ datos })
        });
        
        if (res.ok) {
            const data = await res.json();
            showAlert(`Matriz '${getMatrixName(data.id)}' creada exitosamente.`);
            cargarMatrices();
        } else {
            const err = await res.json();
            alert("Error: " + err.detail);
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
}

async function cargarMatrices() {
    try {
        const res = await fetch(`${API_URL}/matrices`);
        const matrices = await res.json();
        matricesCache = matrices;
        renderMatricesList();
        updateSelects();
    } catch (e) {
        console.error(e);
    }
}

function renderMatrixHTML(datos) {
    let html = `<div class="matrix-brackets">`;
    datos.forEach(row => {
        html += `<div class="matrix-row-display">`;
        row.forEach(val => {
            html += `<span>${val}</span>`;
        });
        html += `</div>`;
    });
    html += `</div>`;
    return html;
}

function renderMatricesList() {
    const list = document.getElementById("matrices-list");
    list.innerHTML = "";
    
    matricesCache.forEach(m => {
        const div = document.createElement("div");
        div.className = "matrix-display";
        
        const title = document.createElement("div");
        title.className = "matrix-title";
        title.innerHTML = `ID ${m.id}: ${getMatrixName(m.id)}`;
        
        div.appendChild(title);
        div.innerHTML += renderMatrixHTML(m.datos);
        
        list.appendChild(div);
    });
}

function updateSelects() {
    const selects = document.querySelectorAll(".matrix-select");
    selects.forEach(select => {
        const currentVal = select.value;
        select.innerHTML = "";
        matricesCache.forEach(m => {
            const option = document.createElement("option");
            option.value = m.id;
            option.textContent = `ID ${m.id} (${getMatrixName(m.id)})`;
            select.appendChild(option);
        });
        if (currentVal) select.value = currentVal;
    });
}

async function sumarMatrices() {
    const id1 = document.getElementById("sum-m1").value;
    const id2 = document.getElementById("sum-m2").value;
    if (!id1 || !id2) return;

    try {
        const res = await fetch(`${API_URL}/operaciones/sumar?id1=${id1}&id2=${id2}`, { method: "POST" });
        const data = await res.json();
        const box = document.getElementById("sum-result");
        box.classList.remove("hidden");
        if (res.ok) {
            box.innerHTML = `<strong>${getMatrixName(id1)} + ${getMatrixName(id2)} =</strong><br><br>` + renderMatrixHTML(data.resultado);
        } else {
            box.innerHTML = `<span style="color:red">Error: ${data.detail}</span>`;
        }
    } catch (e) { console.error(e); }
}

async function multiplicarMatrices() {
    const id1 = document.getElementById("mul-m1").value;
    const id2 = document.getElementById("mul-m2").value;
    if (!id1 || !id2) return;

    try {
        const res = await fetch(`${API_URL}/operaciones/multiplicar?id1=${id1}&id2=${id2}`, { method: "POST" });
        const data = await res.json();
        const box = document.getElementById("mul-result");
        box.classList.remove("hidden");
        if (res.ok) {
            box.innerHTML = `<strong>${getMatrixName(id1)} × ${getMatrixName(id2)} =</strong><br><br>` + renderMatrixHTML(data.resultado);
        } else {
            box.innerHTML = `<span style="color:red">Error: ${data.detail}</span>`;
        }
    } catch (e) { console.error(e); }
}

async function calcularDeterminante() {
    const id = document.getElementById("unit-m").value;
    if (!id) return;

    try {
        const res = await fetch(`${API_URL}/matrices/${id}/determinante`);
        const data = await res.json();
        const box = document.getElementById("det-result");
        box.classList.remove("hidden");
        document.getElementById("trans-result").classList.add("hidden");
        if (res.ok) {
            box.innerHTML = `<strong>det(${getMatrixName(id)}) = </strong> ${data.determinante}`;
        } else {
            box.innerHTML = `<span style="color:red">Error: ${data.detail}</span>`;
        }
    } catch (e) { console.error(e); }
}

async function calcularTranspuesta() {
    const id = document.getElementById("unit-m").value;
    if (!id) return;

    try {
        const res = await fetch(`${API_URL}/matrices/${id}/transpuesta`);
        const data = await res.json();
        const box = document.getElementById("trans-result");
        box.classList.remove("hidden");
        document.getElementById("det-result").classList.add("hidden");
        if (res.ok) {
            box.innerHTML = `<strong>${getMatrixName(id)}^T =</strong><br><br>` + renderMatrixHTML(data.resultado);
        } else {
            box.innerHTML = `<span style="color:red">Error: ${data.detail}</span>`;
        }
    } catch (e) { console.error(e); }
}

// Inicialización al cargar la página
generarInputsMatriz();
cargarMatrices();
