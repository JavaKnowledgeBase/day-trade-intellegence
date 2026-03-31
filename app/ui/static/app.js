const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const loginButton = document.getElementById("loginButton");
const logoutButton = document.getElementById("logoutButton");
const loginStatus = document.getElementById("loginStatus");
const tradeForm = document.getElementById("tradeForm");

const readinessValue = document.getElementById("readinessValue");
const positionsCount = document.getElementById("positionsCount");
const portfolioSource = document.getElementById("portfolioSource");
const reconciliationCount = document.getElementById("reconciliationCount");
const statusBadge = document.getElementById("statusBadge");

const systemStatus = document.getElementById("systemStatus");
const positionsPanel = document.getElementById("positionsPanel");
const portfolioPanel = document.getElementById("portfolioPanel");
const ordersPanel = document.getElementById("ordersPanel");
const strategyRunsPanel = document.getElementById("strategyRunsPanel");
const reconciliationPanel = document.getElementById("reconciliationPanel");
const tradeResultPanel = document.getElementById("tradeResultPanel");

const protectedPanels = [
  positionsPanel,
  portfolioPanel,
  ordersPanel,
  strategyRunsPanel,
  reconciliationPanel,
  tradeResultPanel,
];

const storedUsername = localStorage.getItem("dti_username");
if (storedUsername) {
  usernameInput.value = storedUsername;
}

loginButton.addEventListener("click", () => {
  login();
});

passwordInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    login();
  }
});

logoutButton.addEventListener("click", () => {
  localStorage.removeItem("dti_access_token");
  localStorage.removeItem("dti_username");
  passwordInput.value = "";
  setLoginStatus("Logged out.", "info");
  resetProtectedPanels();
  updateAuthUi();
  loadPublicOverview();
});

tradeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!hasToken()) {
    setLoginStatus("Log in first to submit a trade.", "warn");
    return;
  }

  const formData = new FormData(tradeForm);
  const payload = {
    symbol: String(formData.get("symbol") || "AAPL").trim(),
    quantity: Number(formData.get("quantity") || 1),
    short_window: Number(formData.get("short_window") || 5),
    long_window: Number(formData.get("long_window") || 20),
    timeframe: String(formData.get("timeframe") || "1Min").trim(),
    dry_run: formData.get("dry_run") === "on",
  };

  const result = await fetchJson("/api/v1/trading/signal", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  render(tradeResultPanel, result);
  await loadOverview();
  await loadPositions();
  await loadOrders();
});

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (!hasToken() && button.getAttribute("data-action") !== "load-overview") {
      setLoginStatus("Log in first to use protected actions.", "warn");
      return;
    }

    const action = button.getAttribute("data-action");
    if (action === "load-overview") await loadOverview();
    if (action === "load-orders") await loadOrders();
    if (action === "load-runs") await loadStrategyRuns();
    if (action === "load-reconciliation") await loadReconciliationRuns();
    if (action === "run-reconciliation") await runReconciliation();
  });
});

function hasToken() {
  return Boolean(localStorage.getItem("dti_access_token"));
}

function authHeaders(useAuth = true) {
  const token = localStorage.getItem("dti_access_token");
  if (!useAuth || !token) return { "Content-Type": "application/json" };
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

function updateAuthUi() {
  const authenticated = hasToken();
  loginButton.disabled = authenticated;
  logoutButton.disabled = !authenticated;
}

function setLoginStatus(message, tone = "info") {
  loginStatus.textContent = message;
  loginStatus.className = `login-status login-status--${tone}`;
}

async function login() {
  const username = usernameInput.value.trim();
  const password = passwordInput.value;

  if (!username || !password) {
    setLoginStatus("Enter both username and password.", "warn");
    return;
  }

  loginButton.disabled = true;
  setLoginStatus("Signing in...", "info");

  try {
    const result = await fetchJson("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
      useAuth: false,
    });

    render(systemStatus, { login: result });
    if (!result.ok || !result.body.access_token) {
      const detail = result.body?.detail || "Login failed.";
      setLoginStatus(detail, "error");
      return;
    }

    localStorage.setItem("dti_access_token", result.body.access_token);
    localStorage.setItem("dti_username", username);
    passwordInput.value = "";
    updateAuthUi();
    setLoginStatus(`Logged in as ${username}.`, "success");
    await loadOverview();
    await loadPositions();
    await loadOrders();
    await loadStrategyRuns();
    await loadReconciliationRuns();
  } finally {
    if (!hasToken()) {
      loginButton.disabled = false;
    }
  }
}

async function fetchJson(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...authHeaders(options.useAuth !== false),
        ...(options.headers || {}),
      },
    });

    let body;
    try {
      body = await response.json();
    } catch {
      body = { detail: "Non-JSON response" };
    }

    return { ok: response.ok, status: response.status, body };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      body: { detail: error instanceof Error ? error.message : "Network error" },
    };
  }
}

function render(panel, data) {
  panel.textContent = JSON.stringify(data, null, 2);
}

function resetProtectedPanels() {
  render(positionsPanel, { detail: "Log in to view positions." });
  render(portfolioPanel, { detail: "Log in to view portfolio data." });
  render(ordersPanel, { detail: "Log in to view orders." });
  render(strategyRunsPanel, { detail: "Log in to view strategy runs." });
  render(reconciliationPanel, { detail: "Log in to view reconciliation history." });
  render(tradeResultPanel, { detail: "Log in to submit a signal." });
  positionsCount.textContent = "0";
  portfolioSource.textContent = "Unknown";
  reconciliationCount.textContent = "0";
}

async function loadPublicOverview() {
  const root = await fetchJson("/api/v1/", { useAuth: false });
  const ready = await fetchJson("/api/v1/ready", { useAuth: false });

  render(systemStatus, { root, readiness: ready, currentUser: { detail: "Log in required." } });

  const isReady = ready.ok && ready.body.ready;
  readinessValue.textContent = isReady ? "Ready" : "Attention";
  statusBadge.textContent = isReady ? "Ready" : "Attention";
  statusBadge.className = `badge ${isReady ? "badge--ok" : "badge--warn"}`;
}

async function loadOverview() {
  if (!hasToken()) {
    await loadPublicOverview();
    return;
  }

  const root = await fetchJson("/api/v1/", { useAuth: false });
  const ready = await fetchJson("/api/v1/ready", { useAuth: false });
  const me = await fetchJson("/api/v1/auth/me");
  const admin = await fetchJson("/api/v1/admin/system/status");
  const portfolio = await fetchJson("/api/v1/portfolio/summary");

  render(systemStatus, { root, readiness: ready, currentUser: me, adminStatus: admin });
  render(portfolioPanel, portfolio);

  const isReady = ready.ok && ready.body.ready;
  readinessValue.textContent = isReady ? "Ready" : "Attention";
  portfolioSource.textContent = portfolio.body?.source || "Unknown";
  statusBadge.textContent = isReady ? "Ready" : "Attention";
  statusBadge.className = `badge ${isReady ? "badge--ok" : "badge--warn"}`;
}

async function loadPositions() {
  if (!hasToken()) return;
  const positions = await fetchJson("/api/v1/trading/positions");
  render(positionsPanel, positions);
  positionsCount.textContent = String(positions.body?.total ?? 0);
}

async function loadOrders() {
  if (!hasToken()) return;
  const orders = await fetchJson("/api/v1/trading/orders");
  render(ordersPanel, orders);
}

async function loadStrategyRuns() {
  if (!hasToken()) return;
  const runs = await fetchJson("/api/v1/trading/strategy-runs");
  render(strategyRunsPanel, runs);
}

async function loadReconciliationRuns() {
  if (!hasToken()) return;
  const runs = await fetchJson("/api/v1/reconciliation/runs");
  render(reconciliationPanel, runs);
  reconciliationCount.textContent = String(runs.body?.total ?? 0);
}

async function runReconciliation() {
  if (!hasToken()) return;
  const result = await fetchJson("/api/v1/reconciliation/run?live=false", { method: "POST" });
  render(reconciliationPanel, result);
  await loadOverview();
  await loadReconciliationRuns();
}

protectedPanels.forEach((panel) => {
  panel.dataset.initialized = "true";
});
updateAuthUi();
resetProtectedPanels();
loadPublicOverview();
if (hasToken()) {
  setLoginStatus(`Session restored for ${usernameInput.value.trim() || "saved user"}.`, "success");
  updateAuthUi();
  loadOverview();
  loadPositions();
  loadOrders();
  loadStrategyRuns();
  loadReconciliationRuns();
}
