import { apiClient } from "../shared/api-client.js";
import { escapeHtml, jsonBlock, renderTable } from "../shared/ui-kit.js";

export async function loadFeedback(container) {
  const [items, summary] = await Promise.all([
    apiClient.get("/api/admin/feedback"),
    apiClient.get("/api/admin/evaluation-summary"),
  ]);
  const rows = items.map((item) => [
    escapeHtml(item.conversation_id),
    escapeHtml(item.chat_log_id),
    escapeHtml(item.rating),
    escapeHtml(item.feedback_type),
    escapeHtml(item.comment || ""),
    escapeHtml(item.created_at),
  ]);
  container.innerHTML = `
    <section class="decision-card">${jsonBlock(summary)}</section>
    ${renderTable(
      ["Conversation", "Log", "Rating", "Type", "Comment", "Created"],
      rows,
      { emptyMessage: "暂无质量反馈。", emptyAction: `<a class="empty-action" href="/">完成一次回答反馈</a>` },
    )}`;
}

