// 质量反馈视图 —— 汇总卡片 + 反馈详情表
// 从 admin.js loadFeedback 完整迁移

import { apiAuthGet } from "../shared/api-client.js";
import { table, jsonBlock, escapeHtml } from "../shared/ui-kit.js";

/** 加载反馈数据 */
export async function loadFeedback(token) {
  const [items, summary] = await Promise.all([
    apiAuthGet("/api/admin/feedback", token),
    apiAuthGet("/api/admin/evaluation-summary", token),
  ]);

  const rows = items.map(
    (item) => `<tr>
      <td>${escapeHtml(item.conversation_id)}</td>
      <td>${item.chat_log_id}</td>
      <td>${item.rating}</td>
      <td>${escapeHtml(item.feedback_type)}</td>
      <td>${escapeHtml(item.comment || "")}</td>
      <td>${escapeHtml(item.created_at)}</td>
    </tr>`,
  );

  const viewEl = document.querySelector("#view-feedback");
  viewEl.innerHTML =
    `<section class="decision-card">${jsonBlock(summary)}</section>` +
    table(["Conversation", "Log", "Rating", "Type", "Comment", "Created"], rows);
}
