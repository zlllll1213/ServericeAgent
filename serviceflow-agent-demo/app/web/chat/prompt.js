// 预设场景面板 —— 渲染快捷问题按钮
// 从 app.js [data-prompt] 事件绑定迁移

import { sendMessage } from "./core.js";

/** 初始化快捷提示按钮 */
export function initPrompt() {
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      sendMessage(button.dataset.prompt);
    });
  });
}
