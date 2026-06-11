const SESSION_KEY = "sf_auth_token";
const PERSIST_KEY = "sf_auth_token_persist";
const logoutCallbacks = new Set();

function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
  return JSON.parse(decodeURIComponent(escape(window.atob(padded))));
}

function readTokenRecord() {
  const persisted = localStorage.getItem(PERSIST_KEY);
  if (persisted) {
    return { token: persisted, persistent: true };
  }
  const session = sessionStorage.getItem(SESSION_KEY);
  return { token: session, persistent: false };
}

function getPayload() {
  const token = sessionManager.getToken();
  if (!token) return null;
  try {
    const [, body] = token.split(".");
    return body ? decodeBase64Url(body) : null;
  } catch {
    return null;
  }
}

export const sessionManager = {
  getToken() {
    return readTokenRecord().token;
  },

  setToken(token, options = false) {
    const remember = typeof options === "object" ? Boolean(options.remember) : Boolean(options);
    sessionStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(PERSIST_KEY);
    if (remember) {
      localStorage.setItem(PERSIST_KEY, token);
    } else {
      sessionStorage.setItem(SESSION_KEY, token);
    }
  },

  clearToken() {
    sessionStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(PERSIST_KEY);
    logoutCallbacks.forEach((callback) => callback());
  },

  getPayload,

  getRole() {
    return getPayload()?.role || null;
  },

  getUserId() {
    return getPayload()?.user_id || null;
  },

  getUsername() {
    return getPayload()?.username || null;
  },

  isExpired(skewSeconds = 0) {
    const payload = getPayload();
    if (!payload?.exp) return true;
    return payload.exp <= Math.floor(Date.now() / 1000) + skewSeconds;
  },

  isPersistent() {
    return readTokenRecord().persistent;
  },

  onLogout(callback) {
    logoutCallbacks.add(callback);
    return () => logoutCallbacks.delete(callback);
  },
};
