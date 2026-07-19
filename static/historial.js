const filterUbt = document.getElementById("filter-ubt");
const filterTecnico = document.getElementById("filter-tecnico");
const filterMaquina = document.getElementById("filter-maquina");
const filterFecha = document.getElementById("filter-fecha");
const historySummary = document.getElementById("history-summary");
const historyList = document.getElementById("history-list");

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

function buildQuery() {
  const params = new URLSearchParams();
  if (filterUbt.value) {
    params.set("ubt", filterUbt.value);
  }
  if (filterTecnico.value) {
    params.set("tecnico", filterTecnico.value);
  }
  if (filterMaquina.value) {
    params.set("maquina", filterMaquina.value);
  }
  if (filterFecha.value) {
    params.set("fecha", filterFecha.value);
  }
  return params.toString();
}

function renderSummary(total) {
  historySummary.innerHTML = `
    <div class="history-total">
      <strong>${total}</strong>
      <span>reparaciones registradas</span>
    </div>
  `;
}

function renderList(repairs) {
  if (!repairs.length) {
    historyList.innerHTML = '<div class="empty-state">No hay reparaciones con los filtros seleccionados.</div>';
    return;
  }

  historyList.innerHTML = repairs
    .map(
      (repair) => `
        <article class="history-item">
          <div class="history-item-top">
            <div>
              <h3>UBT ${repair.ubt}</h3>
              <p class="repair-meta">${repair.fecha} · ${repair.created_at}</p>
            </div>
            <span class="history-time">${formatTiempo(repair.tiempo_estimado_minutos)}</span>
          </div>
          <div class="history-tags">
            <span class="technician-tag">${repair.tecnico}</span>
            <span class="machine-tag">${repair.maquina_label || "Sin máquina"}</span>
          </div>
          <p class="history-description">${repair.descripcion}</p>
          ${
            repair.repuestos.length
              ? `<div class="parts-tags">${repair.repuestos
                  .map((part) => `<span>${part.nombre} × ${part.cantidad}</span>`)
                  .join("")}</div>`
              : '<p class="repair-meta">Sin repuestos</p>'
          }
        </article>
      `
    )
    .join("");
}

async function loadHistory() {
  if (!Auth.isUnlocked()) {
    return;
  }

  const query = buildQuery();
  const response = await fetch(`/api/reparaciones${query ? `?${query}` : ""}`);
  const data = await response.json();
  renderSummary(data.total);
  renderList(data.reparaciones);
}

[filterUbt, filterTecnico, filterMaquina, filterFecha].forEach((element) => {
  element.addEventListener("change", loadHistory);
});

async function initHistory() {
  const authenticated = await Auth.checkAuthenticated();
  if (authenticated) {
    Auth.unlockApp();
    await loadHistory();
    return;
  }
  Auth.showAccessGate();
}

initHistory();

document.addEventListener("app-unlocked", loadHistory);
