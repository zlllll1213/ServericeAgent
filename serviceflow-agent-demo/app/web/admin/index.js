// 管理后台入口 —— 认证守卫 + 路由初始化 + 视图切换
// 从 admin.js 入口逻辑整合，不再依赖 URL query 获取 role

import { requireAuth, logout } from "../shared/auth-guard.js";
import { initRouter } from "../shared/router.js";
import { loadConversations } from "./conversations.js";
import { loadTickets } from "./tickets.js";
import { loadKnowledge } from "./knowledge.js";
import { loadLogs, loadTraces } from "./logs-traces.js";
import { loadMetrics } from "./metrics.js";
import { loadEvaluation } from "./evaluation.js";
import { loadFeedback } from "./feedback.js";

// 1. 认证守卫 —— 无 token 或已过期时自动跳转 /login
const auth = requireAuth();
if (!auth) throw new Error("未认证"); // requireAuth 已执行跳转，此行仅在极端情况下触发

const { token, role, userId } = auth;

// 2. 显示当前角色
const roleEl = document.querySelector("#admin-role");
if (roleEl) roleEl.textContent = role;

// 3. 绑定导航按钮点击（切换 active class + 导航）
document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    // 通过设置 hash 触发路由，不在此处手动切换视图
    location.hash = button.dataset.view;
  });
});

// 4. 绑定刷新按钮
document.querySelector("#admin-refresh").addEventListener("click", () => {
  // 触发 hashchange 重新加载当前视图
  window.dispatchEvent(new HashChangeEvent("hashchange"));
});

// 5. 初始化 hash 路由
initRouter({
  conversations: () => loadConversations(token, userId),
  tickets: () => loadTickets(token, userId),
  knowledge: () => loadKnowledge(token),
  logs: () => loadLogs(token),
  traces: () => loadTraces(token),
  metrics: () => loadMetrics(token),
  evaluation: () => loadEvaluation(token),
  feedback: () => loadFeedback(token),
});
