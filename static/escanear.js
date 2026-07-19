const scanResult = document.getElementById("scan-result");
const scanUbtText = document.getElementById("scan-ubt-text");
const scanCodeText = document.getElementById("scan-code-text");
const scanMessage = document.getElementById("scan-message");
const form = document.getElementById("repair-form");
const ubtField = document.getElementById("ubt-field");
const ubtDisplay = document.getElementById("ubt-display");
const tecnicoField = document.getElementById("tecnico-field");
const saveBtn = document.getElementById("save-btn");
const partsList = document.getElementById("parts-list");
const addPartBtn = document.getElementById("add-part");
const formMessage = document.getElementById("form-message");
const dailyDate = document.getElementById("daily-date");
const dailySummary = document.getElementById("daily-summary");
const dailyList = document.getElementById("daily-list");
const dailySubtitle = document.getElementById("daily-subtitle");
const partTemplate = document.getElementById("part-row-template");
const startCameraBtn = document.getElementById("start-camera");
const stopCameraBtn = document.getElementById("stop-camera");

let selectedUbt = null;
let pendingUbt = null;
let pendingUbtCode = null;
let html5QrCode = null;
let cameraActive = false;
const TECHNICIAN_KEY = "reparaciones-ubt-tecnico";

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

function showScanMessage(text) {
  scanMessage.hidden = false;
  scanMessage.textContent = text;
  scanMessage.className = "form-message error";
}

function hideScanMessage() {
  scanMessage.hidden = true;
}

function showFormMessage(text, type) {
  formMessage.hidden = false;
  formMessage.textContent = text;
  formMessage.className = `form-message ${type}`;
}

function hideFormMessage() {
  formMessage.hidden = true;
}

function addPartRow(name = "", qty = 1) {
  const node = partTemplate.content.cloneNode(true);
  const row = node.querySelector(".part-row");
  row.querySelector('[name="part-name"]').value = name;
  row.querySelector('[name="part-qty"]').value = qty;
  row.querySelector("button").addEventListener("click", () => row.remove());
  partsList.appendChild(node);
}

function collectParts() {
  return [...partsList.querySelectorAll(".part-row")]
    .map((row) => ({
      nombre: row.querySelector('[name="part-name"]').value.trim(),
      cantidad: Number(row.querySelector('[name="part-qty"]').value),
    }))
    .filter((part) => part.nombre);
}

async function stopCamera() {
  if (!html5QrCode || !cameraActive) {
    return;
  }
  try {
    await html5QrCode.stop();
    await html5QrCode.clear();
  } catch (error) {
    console.warn(error);
  }
  cameraActive = false;
  startCameraBtn.classList.remove("hidden");
  stopCameraBtn.classList.add("hidden");
}

function showScannedUbt(ubt, code) {
  scanUbtText.textContent = `UBT ${ubt}`;
  scanCodeText.textContent = code;
  scanResult.classList.remove("hidden");
  hideScanMessage();
}

function setSelectedUbt(ubt, code) {
  selectedUbt = ubt;
  ubtField.value = ubt;
  ubtDisplay.value = `UBT ${ubt}`;
  showScannedUbt(ubt, code);
  saveBtn.disabled = false;
  dailySubtitle.textContent = `Reparaciones de UBT ${ubt} · ${dailyDate.value}`;
  form.descripcion.focus();
  loadDailyLog();
}

async function requestAccessAfterScan(ubt, code) {
  pendingUbt = ubt;
  pendingUbtCode = code;
  showScannedUbt(ubt, code);

  if (Auth.isUnlocked() || (await Auth.checkAuthenticated())) {
    Auth.unlockApp();
    applyPendingUbt();
    return;
  }

  Auth.showAccessGate(`UBT ${ubt} identificada. Ingresa el código para abrir la app.`);
}

function applyPendingUbt() {
  if (!pendingUbt) {
    return;
  }
  setSelectedUbt(pendingUbt, pendingUbtCode);
  pendingUbt = null;
  pendingUbtCode = null;
}

async function processScan(code) {
  const response = await fetch("/api/escanear", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ codigo: code }),
  });
  const result = await response.json();
  if (!response.ok) {
    showScanMessage(result.error || "Código no reconocido.");
    return;
  }
  await stopCamera();
  await requestAccessAfterScan(result.ubt, result.codigo);
}

function renderDailySummary(data) {
  if (!selectedUbt) {
    dailySummary.innerHTML = '<div class="empty-state compact">Escanea una UBT para ver su registro diario.</div>';
    return;
  }

  dailySummary.innerHTML = `
    <div class="daily-total">
      <strong>${data.total}</strong>
      <span>reparaciones hoy en UBT ${selectedUbt}</span>
    </div>
    <p class="daily-time">Tiempo estimado total: <strong>${formatTiempo(data.tiempo_total_minutos)}</strong></p>
  `;
}

function renderDailyList(repairs) {
  if (!selectedUbt) {
    dailyList.innerHTML = '<div class="empty-state">Escanea el código QR de la máquina para comenzar.</div>';
    return;
  }

  if (!repairs.length) {
    dailyList.innerHTML = `<div class="empty-state">Sin reparaciones hoy en UBT ${selectedUbt}.</div>`;
    return;
  }

  dailyList.innerHTML = repairs
    .map(
      (repair) => `
        <article class="repair-card highlight">
          <header>
            <h3>UBT ${repair.ubt}</h3>
            <div class="repair-meta">${repair.created_at} · ${repair.tecnico} · ${formatTiempo(repair.tiempo_estimado_minutos)}</div>
          </header>
          <p class="machine-tag">${repair.maquina_label || "Sin máquina"}</p>
          <p>${repair.descripcion}</p>
          ${
            repair.repuestos.length
              ? `<div class="parts-tags">${repair.repuestos
                  .map((part) => `<span>${part.nombre} × ${part.cantidad}</span>`)
                  .join("")}</div>`
              : '<div class="repair-meta">Sin repuestos</div>'
          }
        </article>
      `
    )
    .join("");
}

async function loadDailyLog() {
  const fecha = dailyDate.value;
  if (!selectedUbt || !Auth.isUnlocked()) {
    renderDailySummary({ total: 0 });
    renderDailyList([]);
    return;
  }

  const [summaryResponse, listResponse] = await Promise.all([
    fetch(`/api/resumen/hoy?fecha=${fecha}&ubt=${selectedUbt}`),
    fetch(`/api/reparaciones/hoy?fecha=${fecha}&ubt=${selectedUbt}`),
  ]);

  const summaryData = await summaryResponse.json();
  const listData = await listResponse.json();

  renderDailySummary(summaryData);
  renderDailyList(listData.reparaciones);
}

async function startCamera() {
  if (!window.Html5Qrcode) {
    showScanMessage("No se pudo cargar el escáner de cámara.");
    return;
  }

  hideScanMessage();
  html5QrCode = new Html5Qrcode("camera-reader");

  try {
    await html5QrCode.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      async (decodedText) => {
        await processScan(decodedText);
      },
      () => {}
    );
    cameraActive = true;
    startCameraBtn.classList.add("hidden");
    stopCameraBtn.classList.remove("hidden");
  } catch (error) {
    showScanMessage("No se pudo acceder a la cámara. Permite el acceso o escanea el QR con la app de cámara del celular.");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideFormMessage();

  if (!Auth.isUnlocked()) {
    await Auth.ensureAppAccess();
    return;
  }

  if (!selectedUbt) {
    showFormMessage("Escanea primero el código QR de la máquina.", "error");
    return;
  }

  const tiempoEstimadoMinutos = getTiempoEstimadoMinutos();
  if (tiempoEstimadoMinutos < 1) {
    showFormMessage("El tiempo estimado debe ser mayor a cero.", "error");
    return;
  }

  const payload = {
    ubt: selectedUbt,
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
    showFormMessage(result.error || "No se pudo guardar la reparación.", "error");
    return;
  }

  localStorage.setItem(TECHNICIAN_KEY, payload.tecnico);
  showFormMessage("Reparación guardada en el registro diario.", "success");
  form.descripcion.value = "";
  partsList.innerHTML = "";
  addPartRow();
  await loadDailyLog();
});

addPartBtn.addEventListener("click", () => addPartRow());
dailyDate.addEventListener("change", loadDailyLog);
startCameraBtn.addEventListener("click", startCamera);
stopCameraBtn.addEventListener("click", stopCamera);

const savedTechnician = localStorage.getItem(TECHNICIAN_KEY);
if (savedTechnician) {
  tecnicoField.value = savedTechnician;
}

addPartRow();
loadDailyLog();

async function initApp() {
  if (await Auth.checkAuthenticated()) {
    Auth.unlockApp();
    if (window.INITIAL_UBT) {
      setSelectedUbt(window.INITIAL_UBT, `UBT${window.INITIAL_UBT}`);
    }
    return;
  }

  if (window.INITIAL_UBT) {
    await requestAccessAfterScan(window.INITIAL_UBT, `UBT${window.INITIAL_UBT}`);
  }
}

initApp();

document.addEventListener("app-unlocked", () => {
  applyPendingUbt();
});
