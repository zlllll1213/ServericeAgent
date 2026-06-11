import { apiClient } from "./shared/api-client.js";
import { sessionManager } from "./shared/session-manager.js";
import { toast } from "./shared/ui-kit.js";

const form = document.querySelector("#login-form");
const usernameInput = document.querySelector("#login-username");
const passwordInput = document.querySelector("#login-password");
const rememberInput = document.querySelector("#remember-me");
const submitButton = document.querySelector("#login-submit");
const errorText = document.querySelector("#login-error");

function nextPath() {
  const next = new URLSearchParams(window.location.search).get("next");
  return next && next.startsWith("/") ? next : "/admin";
}

function setSubmitting(isSubmitting) {
  form.setAttribute("aria-busy", String(isSubmitting));
  submitButton.disabled = isSubmitting;
  submitButton.textContent = isSubmitting ? "登录中" : "登录后台";
}

if (sessionManager.getToken() && !sessionManager.isExpired()) {
  window.location.assign(nextPath());
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorText.textContent = "";
  setSubmitting(true);
  try {
    // 登录只调用后端现有合约；持久化位置由“记住我”决定，避免引入不存在的刷新 token 流程。
    const data = await apiClient.post(
      "/api/auth/login",
      { username: usernameInput.value.trim(), password: passwordInput.value },
      { auth: false },
    );
    sessionManager.setToken(data.access_token, { remember: rememberInput.checked });
    window.location.assign(nextPath());
  } catch (error) {
    errorText.textContent = `登录失败：${error.message}`;
    toast(`登录失败：${error.message}`, "error");
  } finally {
    setSubmitting(false);
  }
});
