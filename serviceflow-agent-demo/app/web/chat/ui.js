import { state } from "../shared/state.js";

const labels = {
  user: "User",
  assistant: "Agent",
  system: "System Confirm",
  tool: "Tool Result",
  human: "Human Agent",
};

export function createChatUI({ messages, motion }) {
  function append(role, text, { persist = true } = {}) {
    // 所有消息都用 textContent 写入，避免用户输入被当成 HTML 执行。
    const article = document.createElement("article");
    article.className = `message ${role}`;
    const label = document.createElement("span");
    label.className = "message-label";
    label.textContent = labels[role] || "Agent";
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    article.append(label, paragraph);
    messages.append(article);
    messages.scrollTop = messages.scrollHeight;
    if (persist) {
      state.appendMessage(role, text);
    }
    motion.animateIn(article, { y: role === "user" ? 10 : 8 });
  }

  function clear() {
    messages.innerHTML = "";
  }

  function restoreHistory(history) {
    clear();
    if (!history.length) {
      append("assistant", "你好，我可以查询订单、申请退货、回答技术和售后政策问题，也可以在投诉场景创建人工工单。", { persist: false });
      return;
    }
    for (const item of history) {
      append(item.role, item.text, { persist: false });
    }
  }

  function showTyping() {
    if (messages.querySelector(".typing-indicator")) return;
    const item = document.createElement("article");
    item.className = "message assistant typing-indicator";
    item.innerHTML = '<span class="message-label">Agent</span><p>正在处理请求...</p>';
    messages.append(item);
    messages.scrollTop = messages.scrollHeight;
  }

  function hideTyping() {
    messages.querySelector(".typing-indicator")?.remove();
  }

  return {
    append,
    clear,
    restoreHistory,
    showTyping,
    hideTyping,
  };
}
