import { sessionManager } from "./session-manager.js";

export function checkAuth() {
  const token = sessionManager.getToken();
  if (!token || sessionManager.isExpired()) {
    sessionManager.clearToken();
    const next = encodeURIComponent(`${location.pathname}${location.search}${location.hash}`);
    location.href = `/login?next=${next}`;
    return false;
  }
  return true;
}

export function logout() {
  sessionManager.clearToken();
  location.href = "/login";
}
