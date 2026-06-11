export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]
  ));
}

export function jsonBlock(value) {
  return `<pre>${escapeHtml(JSON.stringify(value ?? {}, null, 2))}</pre>`;
}

export function renderTable(headers, rows, {
  emptyMessage = "暂无数据。",
  emptyAction = "",
  rowClass = "",
  columnClasses = [],
} = {}) {
  if (!rows.length) {
    return `<section class="empty-state"><p>${escapeHtml(emptyMessage)}</p>${emptyAction}</section>`;
  }
  // 表格默认安全转义，列级 class 只用于控制演示中长 ID、状态、时间等字段的可读性。
  const cellClass = (index) => columnClasses[index] ? ` class="${escapeHtml(columnClasses[index])}"` : "";
  const headerHtml = headers.map((item, index) => `<th${cellClass(index)}>${escapeHtml(item)}</th>`).join("");
  const bodyHtml = rows.map((row) => (
    `<tr class="${escapeHtml(rowClass)}">${row.map((cell, index) => `<td${cellClass(index)}>${cell}</td>`).join("")}</tr>`
  )).join("");
  return `<div class="admin-table-wrap"><table class="admin-table"><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`;
}

export function actionButton(label, action, value, extra = {}) {
  const attrs = Object.entries({ "data-action": action, "data-value": value, ...extra })
    .map(([key, attrValue]) => `${escapeHtml(key)}="${escapeHtml(attrValue)}"`)
    .join(" ");
  return `<button type="button" ${attrs}>${escapeHtml(label)}</button>`;
}

export function setLoading(container, show, message = "加载中") {
  container.setAttribute("aria-busy", String(show));
  container.classList.toggle("is-loading", show);
  let loader = container.querySelector(":scope > .loading-state");
  if (show && !loader) {
    loader = document.createElement("div");
    loader.className = "loading-state";
    loader.textContent = message;
    container.prepend(loader);
  } else if (!show && loader) {
    loader.remove();
  }
}

export function toast(message, type = "info") {
  let region = document.querySelector("#toast-region");
  if (!region) {
    region = document.createElement("div");
    region.id = "toast-region";
    region.className = "toast-region";
    region.setAttribute("aria-live", "polite");
    document.body.append(region);
  }
  const item = document.createElement("p");
  item.className = `toast toast-${type}`;
  item.textContent = message;
  region.append(item);
  window.setTimeout(() => item.remove(), 3200);
}

function ensureDialog() {
  let dialog = document.querySelector("#sf-dialog");
  if (!dialog) {
    dialog = document.createElement("dialog");
    dialog.id = "sf-dialog";
    dialog.className = "sf-dialog";
    document.body.append(dialog);
  }
  return dialog;
}

export function confirmAction(message, { title = "确认操作", confirmLabel = "确认", cancelLabel = "取消", destructive = false } = {}) {
  const dialog = ensureDialog();
  dialog.innerHTML = `
    <form method="dialog" class="dialog-card">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(message)}</p>
      <div class="dialog-actions">
        <button type="button" value="cancel" data-dialog-cancel>${escapeHtml(cancelLabel)}</button>
        <button type="submit" value="confirm" class="${destructive ? "danger-action" : "primary-action"}">${escapeHtml(confirmLabel)}</button>
      </div>
    </form>`;
  return new Promise((resolve) => {
    const cancel = dialog.querySelector("[data-dialog-cancel]");
    cancel.addEventListener("click", () => {
      dialog.close("cancel");
    }, { once: true });
    dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), { once: true });
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      resolve(window.confirm(message));
    }
  });
}

export function promptAction({ title, label, defaultValue = "", multiline = false, confirmLabel = "提交" }) {
  const dialog = ensureDialog();
  const field = multiline
    ? `<textarea id="dialog-input" rows="4">${escapeHtml(defaultValue)}</textarea>`
    : `<input id="dialog-input" value="${escapeHtml(defaultValue)}" />`;
  dialog.innerHTML = `
    <form method="dialog" class="dialog-card">
      <h2>${escapeHtml(title)}</h2>
      <label for="dialog-input">${escapeHtml(label)}</label>
      ${field}
      <p class="dialog-error" role="status"></p>
      <div class="dialog-actions">
        <button type="button" data-dialog-cancel>取消</button>
        <button type="submit" value="confirm" class="primary-action">${escapeHtml(confirmLabel)}</button>
      </div>
    </form>`;
  return new Promise((resolve) => {
    const input = dialog.querySelector("#dialog-input");
    const error = dialog.querySelector(".dialog-error");
    dialog.querySelector("[data-dialog-cancel]").addEventListener("click", () => dialog.close("cancel"), { once: true });
    dialog.querySelector("form").addEventListener("submit", (event) => {
      if (!input.value.trim()) {
        event.preventDefault();
        error.textContent = "请输入内容。";
      }
    });
    dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm" ? input.value.trim() : null), { once: true });
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
      input.focus();
    } else {
      resolve(null);
    }
  });
}

export function setText(selector, text, root = document) {
  const node = root.querySelector(selector);
  if (node) node.textContent = text;
}
