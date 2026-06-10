// 路由守卫 —— 检查认证状态，无 token 或已过期时跳转登录页

import { getToken, getRole, getUserId, clearToken, isExpired } from "./session-manager.js";

/** 检查认证状态，无效则自动跳转 /login */
export function requireAuth() {
  const token = getToken();
  if (!token || isExpired()) {
    clearToken();
    location.href = "/login";
    return null;
  }
  return {
    token,
    role: getRole(),
    userId: getUserId(),
  };
}

/** 清除 token 并跳转登录页 */
export function logout() {
  clearToken();
  location.href = "/login";
}
