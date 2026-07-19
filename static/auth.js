const accessGate = document.getElementById("access-gate");
const accessForm = document.getElementById("access-form");
const accessCodeInput = document.getElementById("access-code");
const accessMessage = document.getElementById("access-message");

let appUnlocked = false;

async function checkAuthenticated() {
  const response = await fetch("/api/acceso");
  const data = await response.json();
  return data.authenticated;
}

function unlockApp() {
  appUnlocked = true;
  if (accessGate) {
    accessGate.classList.add("hidden");
  }
  document.querySelectorAll(".app-locked").forEach((element) => {
    element.classList.remove("app-locked");
  });
  document.dispatchEvent(new CustomEvent("app-unlocked"));
}

function showAccessGate(message = "") {
  if (!accessGate) {
    return;
  }
  accessGate.classList.remove("hidden");
  const hint = accessGate.querySelector(".scan-hint");
  if (hint && message) {
    hint.textContent = message;
  }
  if (accessMessage) {
    accessMessage.hidden = true;
  }
  if (accessCodeInput) {
    accessCodeInput.value = "";
    accessCodeInput.focus();
  }
}

async function submitAccessCode(codigo) {
  const response = await fetch("/api/acceso", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ codigo }),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || "Código incorrecto.");
  }
  unlockApp();
  return true;
}

async function ensureAppAccess() {
  if (appUnlocked || (await checkAuthenticated())) {
    unlockApp();
    return true;
  }
  showAccessGate();
  return false;
}

if (accessForm) {
  accessForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await submitAccessCode(accessCodeInput.value.trim());
    } catch (error) {
      if (accessMessage) {
        accessMessage.hidden = false;
        accessMessage.textContent = error.message;
      }
    }
  });
}

window.Auth = {
  checkAuthenticated,
  ensureAppAccess,
  unlockApp,
  showAccessGate,
  isUnlocked: () => appUnlocked,
};
