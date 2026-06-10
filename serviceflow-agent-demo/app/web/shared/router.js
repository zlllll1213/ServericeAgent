// 简易视图路由 —— 基于 location.hash 的管理后台视图切换
// 支持浏览器前进/后退按钮，替代 display:none 方案

import { toast } from "./ui-kit.js";

let _routes = {};
let _currentView = "conversations";

/** 根据 hash 获取当前视图名称 */
function _hashView() {
  const hash = location.hash.replace(/^#/, "");
  return hash && _routes[hash] ? hash : "conversations";
}

/** 更新导航按钮 active 状态 */
function _updateNav(viewName) {
  document.querySelectorAll("[data-view]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });
  // 更新标题
  const titleEl = document.querySelector("#admin-title");
  if (titleEl) {
    const activeBtn = document.querySelector(`[data-view="${viewName}"]`);
    if (activeBtn) titleEl.textContent = activeBtn.textContent;
  }
}

/** 隐藏所有视图，显示当前视图 */
function _showView(viewName) {
  document.querySelectorAll(".admin-view").forEach((el) => {
    el.classList.toggle("hidden", el.id !== `view-${viewName}`);
  });
}

/** 加载当前视图（路由 handler 触发） */
async function _loadView(viewName) {
  const handler = _routes[viewName];
  if (!handler) return;
  _currentView = viewName;
  _showView(viewName);
  _updateNav(viewName);
  try {
    await handler();
  } catch (error) {
    toast(error.message, "error");
    // 错误信息也展示在视图区
    const viewEl = document.querySelector(`#view-${viewName}`);
    if (viewEl) {
      viewEl.innerHTML = `<p class="error-text">加载失败：${error.message}</p>`;
    }
  }
}

/** 初始化路由 —— 注册视图 handler + 绑定 hashchange */
export function initRouter(routes) {
  _routes = routes;

  // 监听 hash 变化
  window.addEventListener("hashchange", () => {
    _loadView(_hashView());
  });

  // 初次加载（根据当前 hash 或默认值）
  const initialView = _hashView();
  // 确保 hash 反映当前视图
  if (!location.hash || location.hash === "#") {
    location.replace(`#${initialView}`);
    return; // replace 会触发 hashchange
  }
  _loadView(initialView);
}

/** 编程式导航 */
export function navigateTo(hash) {
  location.hash = hash;
}

/** 获取当前视图名称 */
export function getCurrentView() {
  return _currentView;
}
