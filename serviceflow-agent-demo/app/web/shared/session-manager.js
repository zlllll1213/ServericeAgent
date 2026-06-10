// Token 生命周期管理 —— sessionStorage（默认）或 localStorage（"记住我"）
// JWT 格式: header.body.signature，base64url 编码

const SESSION_KEY = "sf_session";

/** 从 sessionStorage / localStorage 读取完整会话数据 */
function _load() {
  // 先尝试 sessionStorage，再尝试 localStorage（"记住我"场景）
  const raw = sessionStorage.getItem(SESSION_KEY) || localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/** 写入会话数据到指定存储 */
function _save(data, remember) {
  const json = JSON.stringify(data);
  if (remember) {
    localStorage.setItem(SESSION_KEY, json);
    sessionStorage.removeItem(SESSION_KEY);
  } else {
    sessionStorage.setItem(SESSION_KEY, json);
    localStorage.removeItem(SESSION_KEY);
  }
}

/** 解析 JWT payload（base64url decode 第二部分） */
function _parseJwt(token) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    // base64url → base64 标准格式
    let body = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    // 补齐 padding
    while (body.length % 4 !== 0) body += "=";
    return JSON.parse(atob(body));
  } catch {
    return null;
  }
}

/** 获取当前 token */
export function getToken() {
  const data = _load();
  return data?.token ?? null;
}

/** 存储 token */
export function setToken(token, role, userId, remember = false) {
  _save({ token, role, userId }, remember);
}

/** 清除 token（同时清除 sessionStorage 和 localStorage） */
export function clearToken() {
  sessionStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(SESSION_KEY);
}

/** 获取当前角色 */
export function getRole() {
  const data = _load();
  return data?.role ?? null;
}

/** 获取当前 user_id */
export function getUserId() {
  const data = _load();
  return data?.userId ?? null;
}

/** 检查 token 是否已过期（30 秒缓冲） */
export function isExpired() {
  const token = getToken();
  if (!token) return true;
  const payload = _parseJwt(token);
  if (!payload || !payload.exp) return true;
  return payload.exp * 1000 < Date.now() - 30_000;
}
