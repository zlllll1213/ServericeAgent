// 通用 UI 工具组件 —— 跨页面复用的 HTML 生成和轻量交互
// 所有 DOM 操作使用 textContent 或经过 escapeHtml 处理，确保 XSS 安全

/** XSS 安全字符串转义：& < > " ' */
export function escapeHtml(value) {
  return String(value).replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char]),
  );
}

/** 生成管理后台表格 HTML */
export function table(headers, rows) {
  return `<div class="admin-table-wrap"><table class="admin-table"><thead><tr>${headers
    .map((item) => `<th>${item}</th>`)
    .join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
}

/** 格式化 JSON 的 <pre> HTML */
export function jsonBlock(value) {
  return `<pre>${escapeHtml(JSON.stringify(value || {}, null, 2))}</pre>`;
}

/** 右上角轻量 toast 通知 */
export function toast(message, type = "info") {
  const el = document.createElement("div");
  el.className = `sf-toast sf-toast-${type}`;
  el.textContent = message;
  el.setAttribute("role", "status");
  el.setAttribute("aria-live", "polite");
  document.body.appendChild(el);
  // 入场动画后自动移除
  requestAnimationFrame(() => {
    el.classList.add("sf-toast-show");
    setTimeout(() => {
      el.classList.remove("sf-toast-show");
      setTimeout(() => el.remove(), 300);
    }, 2500);
  });
}
