const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const loginButton = document.getElementById("loginButton");
const logoutButton = document.getElementById("logoutButton");
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

const storedUsername = localStorage.getItem("dti_username");
const storedToken = localStorage.getItem("dti_access_token");
if (storedUsername) usernameInput.value = storedUsername;

loginButton.addEventListener("click", async () => {
  const result = await fetchJson("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username: usernameInput.value.trim(), password: passwordInput.value }),
    useAuth: false,
  });
  render(systemStatus, { login: result });
  if (result.ok && result.body.access_token) {
    localStorage.setItem("dti_access_token", result.body.access_token);
    localStorage.setItem("dti_username", usernameInput.value.trim());
    await loadOverview();
  }
});

logoutButton.addEventListener("click", () => {
  localStorage.removeItem("dti_access_token");
  localStorage.removeItem("dti_username");
  passwordInput.value = "";
});

tradeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
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
    const action = button.getAttribute("data-action");
    if (action === "load-overview") await loadOverview();
    if (action === "load-orders") await loadOrders();
    if (action === "load-runs") await loadStrategyRuns();
    if (action === "load-reconciliation") await loadReconciliationRuns();
    if (action === "run-reconciliation") await runReconciliation();
  });
});

function authHeaders(useAuth = true) {
  const token = localStorage.getItem("dti_access_token");
  if (!useAuth || !token) return { "Content-Type": "application/json" };
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function fetchJson(url, options = {}) {
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
}

function render(panel, data) {
  panel.textContent = JSON.stringify(data, null, 2);
}

async function loadOverview() {
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
  const positions = await fetchJson("/api/v1/trading/positions");
  render(positionsPanel, positions);
  positionsCount.textContent = String(positions.body?.total ?? 0);
}

async function loadOrders() {
  const orders = await fetchJson("/api/v1/trading/orders");
  render(ordersPanel, orders);
}

async function loadStrategyRuns() {
  const runs = await fetchJson("/api/v1/trading/strategy-runs");
  render(strategyRunsPanel, runs);
}

async function loadReconciliationRuns() {
  const runs = await fetchJson("/api/v1/reconciliation/runs");
  render(reconciliationPanel, runs);
  reconciliationCount.textContent = String(runs.body?.total ?? 0);
}

async function runReconciliation() {
  const result = await fetchJson("/api/v1/reconciliation/run?live=false", { method: "POST" });
  render(reconciliationPanel, result);
  await loadOverview();
  await loadReconciliationRuns();
}

loadOverview();
loadPositions();
loadOrders();
loadStrategyRuns();
loadReconciliationRuns();
