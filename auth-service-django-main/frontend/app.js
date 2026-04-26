const storageKeys = {
  access: "cv_matcher_access_token",
  refresh: "cv_matcher_refresh_token",
  user: "cv_matcher_user",
  activeJobId: "cv_matcher_active_job_id",
  verificationCode: "cv_matcher_verification_code",
};

function getDashboardRoute(user) {
  if (!user) {
    return "login.html";
  }
  return user.role === "RECRUTEUR" ? "dashboard.html" : "candidate-dashboard.html";
}

function getAccessToken() {
  return localStorage.getItem(storageKeys.access);
}

function getStoredUser() {
  const rawValue = localStorage.getItem(storageKeys.user);
  return rawValue ? JSON.parse(rawValue) : null;
}

function persistSession(payload) {
  if (payload.access) {
    localStorage.setItem(storageKeys.access, payload.access);
  }
  if (payload.refresh) {
    localStorage.setItem(storageKeys.refresh, payload.refresh);
  }
  if (payload.user) {
    localStorage.setItem(storageKeys.user, JSON.stringify(payload.user));
  }
}

function redirectToDashboard(user = getStoredUser()) {
  window.location.href = getDashboardRoute(user);
}

function clearSession() {
  Object.values(storageKeys).forEach((key) => localStorage.removeItem(key));
}

async function fetchJson(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof data === "string"
        ? data
        : data.detail || data.message || JSON.stringify(data);
    const error = new Error(detail || "Request failed.");
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
}

function showMessage(elementId, message, type = "info") {
  const element = document.getElementById(elementId);
  if (!element) {
    return;
  }
  element.textContent = message;
  element.className = `message ${type}`;
  element.hidden = false;
}

function hideMessage(elementId) {
  const element = document.getElementById(elementId);
  if (!element) {
    return;
  }
  element.hidden = true;
  element.textContent = "";
}

function getVerificationDeliveryMessage(payload, defaultMessage) {
  if (!payload || payload.email_delivery !== "console") {
    return defaultMessage;
  }

  return "SMTP is not configured, so no real email was sent.";
}

function requireSession() {
  if (!getAccessToken()) {
    window.location.href = "login.html";
  }
}

function logout() {
  clearSession();
  window.location.href = "login.html";
}
