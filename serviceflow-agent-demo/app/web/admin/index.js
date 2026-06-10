import { checkAuth, logout } from "../shared/auth-guard.js";
import { createHashRouter } from "../shared/router.js";
import { sessionManager } from "../shared/session-manager.js";
import { escapeHtml, setLoading, toast } from "../shared/ui-kit.js";
import { loadConversations } from "./conversations.js";
import { loadTickets } from "./tickets.js";
import { loadKnowledge } from "./knowledge.js";
import { loadLogs, loadTraces } from "./logs-traces.js";
import { loadMetrics } from "./metrics.js";
import { loadEvaluation } from "./evaluation.js";
import { loadFeedback } from "./feedback.js";

if (!checkAuth()) {
  throw new Error("redirecting to login");
}

const viewTitles = {
  conversations: "会话列表",
  tickets: "工单管理",
  knowledge: "知识库管理",
  logs: "Agent 日志",
  traces: "Agent Trace",
  metrics: "Metrics 看板",
  evaluation: "Evaluation 报告",
  feedback: "质量反馈",
};

const loaders = {
  conversations: loadConversations,
  tickets: loadTickets,
  knowledge: loadKnowledge,
  logs: loadLogs,
  traces: loadTraces,
  metrics: loadMetrics,
  evaluation: loadEvaluation,
  feedback: loadFeedback,
};

const views = Object.fromEntries(Object.keys(loaders).map((name) => [name, document.querySelector(`#view-${name}`)]));
const titleEl = document.querySelector("#admin-title");
const roleEl = document.querySelector("#admin-role");
const userEl = document.querySelector("#admin-user");
const refreshButton = document.querySelector("#admin-refresh");
const logoutButton = document.querySelector("#admin-logout");

roleEl.textContent = sessionManager.getRole() || "agent";
userEl.textContent = `${sessionManager.getUsername() || "user"} · ${sessionManager.getUserId() || "-"}`;

function activateView(name) {
  const viewName = loaders[name] ? name : "conversations";
  titleEl.textContent = viewTitles[viewName];
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewName);
  });
  Object.entries(views).forEach(([key, node]) => node.classList.toggle("hidden", key !== viewName));
  return viewName;
}

async function renderView(name) {
  const viewName = activateView(name);
  const container = views[viewName];
  setLoading(container, true, "加载后台数据");
  try {
    // 每个后台视图只在激活时取数，保证 hash 前进后退不会留下旧视图的异步渲染。
    await loaders[viewName](container);
  } catch (error) {
    container.innerHTML = `<p class="error-text">加载失败：${escapeHtml(error.message)}</p>`;
    toast(`加载失败：${error.message}`, "error");
  } finally {
    setLoading(container, false);
  }
}

const router = createHashRouter(
  Object.fromEntries(Object.keys(loaders).map((name) => [name, () => renderView(name)])),
  { defaultRoute: "conversations" },
);

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    router.navigate(button.dataset.view);
  });
});

refreshButton.addEventListener("click", () => {
  renderView(router.getCurrentView() || "conversations");
});

logoutButton.addEventListener("click", logout);

router.init();
