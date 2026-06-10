import { sessionManager } from "./session-manager.js";

export class ApiError extends Error {
  constructor(message, { status = 0, errorCode = "REQUEST_FAILED", requestId = null, details = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errorCode = errorCode;
    this.requestId = requestId;
    this.details = details;
  }
}

function redirectToLogin() {
  if (!location.pathname.endsWith("/login")) {
    const next = encodeURIComponent(`${location.pathname}${location.search}${location.hash}`);
    location.href = `/login?next=${next}`;
  }
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return response.text();
  }
  return response.json();
}

async function request(method, url, { body, headers = {}, timeout = 15000, auth = true } = {}) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeout);
  const requestHeaders = { ...headers };
  if (body !== undefined && !(body instanceof FormData)) {
    requestHeaders["Content-Type"] = requestHeaders["Content-Type"] || "application/json";
  }
  if (auth) {
    const token = sessionManager.getToken();
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url, {
      method,
      headers: requestHeaders,
      body: body === undefined || body instanceof FormData ? body : JSON.stringify(body),
      signal: controller.signal,
    });
    const payload = await parseResponse(response);
    if (response.status === 401 && auth) {
      // 后台 token 失效时统一清理本地状态，避免各视图重复处理认证分支。
      sessionManager.clearToken();
      redirectToLogin();
    }
    if (!response.ok) {
      throw new ApiError(payload?.message || payload?.detail || `HTTP ${response.status}`, {
        status: response.status,
        errorCode: payload?.error_code || "REQUEST_FAILED",
        requestId: payload?.request_id || null,
        details: payload,
      });
    }
    return payload;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new ApiError("请求超时，请稍后重试。", { errorCode: "REQUEST_TIMEOUT" });
    }
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message || "请求失败", { details: error });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export const apiClient = {
  get(url, options) {
    return request("GET", url, options);
  },
  post(url, body, options = {}) {
    return request("POST", url, { ...options, body });
  },
  put(url, body, options = {}) {
    return request("PUT", url, { ...options, body });
  },
  delete(url, options) {
    return request("DELETE", url, options);
  },
};
