// 消息展示组件 —— 创建消息气泡并追加到聊天区
// 所有消息用 textContent 写入，避免用户输入被当成 HTML 执行

import { animateFrom } from "./motion.js";

const _messagesEl = document.querySelector("#messages");

/** 追加一条消息气泡到 DOM */
export function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const label = document.createElement("span");
  label.className = "message-label";
  // 5 种角色的标签映射
  label.textContent =
    {
      user: "User",
      assistant: "Agent",
      system: "System Confirm",
      tool: "Tool Result",
      human: "Human Agent",
    }[role] || "Agent";

  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  article.append(label);
  article.append(paragraph);
  _messagesEl.append(article);
  // 自动滚动到最新消息
  _messagesEl.scrollTop = _messagesEl.scrollHeight;

  animateFrom(article, { y: role === "user" ? 10 : 8 });
}

/** 清空消息区（保留欢迎消息） */
export function clearMessages() {
  _messagesEl.innerHTML = "";
}

/** 获取消息容器 DOM 引用 */
export function getMessagesContainer() {
  return _messagesEl;
}
