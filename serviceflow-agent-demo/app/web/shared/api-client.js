// 统一 HTTP 客户端 —— 封装 fetch，自动注入 token，统一错误处理
// 聊天 API 无需认证，管理 API 需 Bearer token

import { clearToken } from "./session-manager.js";

const DEFAULT_TIMEOUT = 15_000;

/** 带超时的 fetch 封装 */
async function _fetch(url, options = {}, timeout = DEFAULT_TIMEOUT) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timer);
  }
}

/** 解析响应，非 2xx 抛出带中文描述的 Error */
async function _parseResponse(response) {
  if (!response.ok) {
    // 尝试从响应体中提取服务端错误信息
    let message = `请求失败（HTTP ${response.status}）`;
    try {
      const body = await response.json();
      if (body.message) message = body.message;
    } catch {
      // 解析失败使用默认消息
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

/** 公开 GET（无需认证） */
export async function apiGet(url, options = {}) {
  const response = await _fetch(url, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  return _parseResponse(response);
}

/** 公开 POST（无需认证） */
export async function apiPost(url, body, options = {}) {
  const response = await _fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    body: JSON.stringify(body),
  });
  return _parseResponse(response);
}

/** 管理后台 GET（需要 Bearer token） */
export async function apiAuthGet(url, token, options = {}) {
  try {
    const response = await _fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(options.headers || {}),
      },
    });
    return _parseResponse(response);
  } catch (error) {
    // 401 时清除本地 token，触发重新登录
    if (error.status === 401) clearToken();
    throw error;
  }
}

/** 管理后台 POST（需要 Bearer token） */
export async function apiAuthPost(url, token, body, options = {}) {
  try {
    const response = await _fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(options.headers || {}),
      },
      body: JSON.stringify(body),
    });
    return _parseResponse(response);
  } catch (error) {
    if (error.status === 401) clearToken();
    throw error;
  }
}

/** 登录专用 —— POST /api/auth/login，使用 username 字段（非 user_id） */
export async function apiLogin(username, password) {
  return apiPost("/api/auth/login", { username, password });
}
