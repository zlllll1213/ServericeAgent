// 用户反馈组件 —— 点赞/点踩 + 反馈类型下拉
// 从 app.js [data-feedback] 事件迁移

import { apiPost } from "../shared/api-client.js";
import { getConversationId } from "./debug.js";
import { getLastChatLogId } from "./core.js";

const _errorText = document.querySelector("#error-text");
const _feedbackType = document.querySelector("#feedback-type");

/** 初始化反馈按钮事件 */
export function initFeedback() {
  document.querySelectorAll("[data-feedback]").forEach((button) => {
    button.addEventListener("click", async () => {
      const conversationId = getConversationId();
      const lastChatLogId = getLastChatLogId();

      if (!conversationId || !lastChatLogId) {
        _errorText.textContent = "请先发送一条问题后再反馈。";
        return;
      }

      const isGood = button.dataset.feedback === "GOOD";
      const type = isGood ? "GOOD" : _feedbackType.value;

      try {
        await apiPost("/api/feedback", {
          conversation_id: conversationId,
          chat_log_id: lastChatLogId,
          user_id: "U1001",
          rating: isGood ? 5 : 2,
          feedback_type: type,
          comment: isGood ? "用户认为回答有帮助" : "用户认为回答没有帮助",
        });
        _errorText.textContent = "反馈已提交。";
      } catch (error) {
        _errorText.textContent = `反馈提交失败：${error.message}`;
      }
    });
  });
}
