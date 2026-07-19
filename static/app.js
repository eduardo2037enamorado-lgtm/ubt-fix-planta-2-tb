const form = document.getElementById("repair-form");
const partsList = document.getElementById("parts-list");
const addPartBtn = document.getElementById("add-part");
const repairsList = document.getElementById("repairs-list");
const filterUbt = document.getElementById("filter-ubt");
const formMessage = document.getElementById("form-message");
const summary = document.getElementById("summary");
const partTemplate = document.getElementById("part-row-template");

function formatTiempo(minutos) {
  if (!minutos) {
    return "Sin tiempo";
  }
  const horas = Math.floor(minutos / 60);
  const mins = minutos % 60;
  if (horas && mins) {
    return `${horas}h ${mins}min`;
  }
  if (horas) {
    return `${horas}h`;
  }
  return `${mins} min`;
}

function getTiempoEstimadoMinutos() {
  const horas = Number(form.horas.value) || 0;
  const minutos = Number(form.minutos.value) || 0;
  return horas * 60 + minutos;
}

function setTodayDate() {
  const fechaInput = form.querySelector('[name="fecha"]');
  fechaInput.value = new Date().toISOString().slice(0, 10);
}

function addPartRow(name = "", qty = 1) {
  const node = partTemplate.content.cloneNode(true);
  const row = node.querySelector(".part-row");
  row.querySelector('[name="part-name"]').value = name;
  row.querySelector('[name="part-qty"]').value = qty;
  row.querySelector("button").addEventListener("click", () => row.remove());
  partsList.appendChild(node);
}

function showMessage(text, type) {
  formMessage.hidden = false;
  formMessage.textContent = text;
  formMessage.className = `form-message ${type}`;
}

function collectParts() {
  return [...partsList.querySelectorAll(".part-row")]
    .map((row) => ({
      nombre: row.querySelector('[name="part-name"]').value.trim(),
      cantidad: Number(row.querySelector('[name="part-qty"]').value),
    }))
    .filter((part) => part.nombre);
}

async function loadSummary() {
  const response = await fetch("/api/resumen");
  const data = await response.json();
  summary.innerHTML = Object.entries(data)
    .map(
      ([ubt, total]) => `
        <div class="summary-item">
          <strong>${total}</strong>
          <span>UBT ${ubt}</span>
        </div>
      `
    )
    .join("");
}

function renderRepairs(repairs) {
  if (!repairs.length) {
    repairsList.innerHTML = '<div class="empty-state">No hay reparaciones registradas.</div>';
    return;
  }

  repairsList.innerHTML = repairs
    .map(
      (repair) => `
        <article class="repair-card">
          <header>
            <h3>UBT ${repair.ubt}</h3>
            <div class="repair-meta">${repair.fecha} · ${repair.tecnico} · ${formatTiempo(repair.tiempo_estimado_minutos)}</div>
          </header>
          <p class="machine-tag">${repair.maquina_label || "Sin máquina"}</p>
          <p>${repair.descripcion}</p>
          ${
            repair.repuestos.length
              ? `<div class="parts-tags">${repair.repuestos
                  .map((part) => `<span>${part.nombre} × ${part.cantidad}</span>`)
                  .join("")}</div>`
              : '<div class="repair-meta">Sin repuestos registrados</div>'
          }
        </article>
      `
    )
    .join("");
}

async function loadRepairs() {
  const ubt = filterUbt.value;
  const url = ubt ? `/api/reparaciones?ubt=${ubt}` : "/api/reparaciones";
  const response = await fetch(url);
  const data = await response.json();
  renderRepairs(data.reparaciones);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formMessage.hidden = true;

  const tiempoEstimadoMinutos = getTiempoEstimadoMinutos();
  if (tiempoEstimadoMinutos < 1) {
    showMessage("El tiempo estimado debe ser mayor a cero.", "error");
    return;
  }

  const payload = {
    ubt: form.ubt.value,
    fecha: form.fecha.value,
    descripcion: form.descripcion.value.trim(),
    tecnico: form.tecnico.value.trim(),
    maquina: form.maquina.value,
    tiempo_estimado_minutos: tiempoEstimadoMinutos,
    repuestos: collectParts(),
  };

  const response = await fetch("/api/reparaciones", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const result = await response.json();
  if (!response.ok) {
    showMessage(result.error || "No se pudo guardar la reparación.", "error");
    return;
  }

  showMessage("Reparación guardada correctamente.", "success");
  form.descripcion.value = "";
  form.maquina.value = "";
  partsList.innerHTML = "";
  addPartRow();
  await Promise.all([loadRepairs(), loadSummary()]);
});

addPartBtn.addEventListener("click", () => addPartRow());
filterUbt.addEventListener("change", loadRepairs);

setTodayDate();
addPartRow();
loadSummary();
loadRepairs();
