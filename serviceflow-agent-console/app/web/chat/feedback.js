import { apiClient } from "../shared/api-client.js";

export function createFeedbackPanel({ root, typeSelect, statusEl, userId = "U1001" }) {
  let conversationId = null;
  let chatLogId = null;

  function setEnabled(enabled) {
    root.querySelectorAll("[data-feedback], select").forEach((node) => {
      node.disabled = !enabled;
    });
  }

  function enable(nextConversationId, nextChatLogId) {
    conversationId = nextConversationId;
    chatLogId = nextChatLogId;
    statusEl.textContent = chatLogId ? "可以提交本次回答反馈。" : "正在同步反馈记录。";
    setEnabled(Boolean(chatLogId));
  }

  function disable(message = "反馈已提交。") {
    statusEl.textContent = message;
    setEnabled(false);
  }

  function init() {
    setEnabled(false);
    root.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-feedback]");
      if (!button) return;
      if (!conversationId || !chatLogId) {
        statusEl.textContent = "请先发送一条问题后再反馈。";
        return;
      }
      const isGood = button.dataset.feedback === "GOOD";
      const type = isGood ? "GOOD" : typeSelect.value;
      button.disabled = true;
      statusEl.textContent = "正在提交反馈...";
      try {
        await apiClient.post(
          "/api/feedback",
          {
            conversation_id: conversationId,
            chat_log_id: chatLogId,
            user_id: userId,
            rating: isGood ? 5 : 2,
            feedback_type: type,
            comment: isGood ? "用户认为回答有帮助" : "用户认为回答没有帮助",
          },
          { auth: false },
        );
        disable("反馈已提交。");
      } catch (error) {
        statusEl.textContent = `反馈提交失败：${error.message}`;
        button.disabled = false;
      }
    });
  }

  return { init, enable, disable };
}
