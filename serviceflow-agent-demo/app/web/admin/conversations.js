// 会话管理视图 —— 列表、详情、认领、人工回复、关闭
// 从 admin.js loadConversations / bindConversationActions 完整迁移

import { apiAuthGet, apiAuthPost } from "../shared/api-client.js";
import { table, jsonBlock, escapeHtml, toast } from "../shared/ui-kit.js";

/** 加载会话列表 */
export async function loadConversations(token, agentId) {
  const data = await apiAuthGet("/api/admin/conversations?page_size=50", token);

  const rows = data.map(
    (item) => `<tr>
      <td>${escapeHtml(item.conversation_id)}</td>
      <td>${escapeHtml(item.user_id)}</td>
      <td>${escapeHtml(item.current_intent || "")}</td>
      <td>${escapeHtml(item.status)}</td>
      <td>${escapeHtml(item.handoff_status)}</td>
      <td>${escapeHtml(item.assigned_agent_id || "-")}</td>
      <td>${escapeHtml(item.updated_at)}</td>
      <td class="admin-actions">
        <button data-detail="${escapeHtml(item.conversation_id)}">查看详情</button>
        <button data-assign="${escapeHtml(item.conversation_id)}">认领</button>
        <button data-reply="${escapeHtml(item.conversation_id)}">人工回复</button>
        <button data-resolve="${escapeHtml(item.conversation_id)}">关闭会话</button>
      </td>
    </tr>`,
  );

  const viewEl = document.querySelector("#view-conversations");
  viewEl.innerHTML =
    table(["Conversation", "User", "Intent", "Status", "Handoff", "Agent", "Updated", "操作"], rows) +
    `<section class="admin-detail" id="conversation-detail"></section>`;

  _bindActions(token, agentId);
}

/** 绑定行操作按钮（事件委托） */
function _bindActions(token, agentId) {
  const viewEl = document.querySelector("#view-conversations");

  // 查看详情
  viewEl.querySelectorAll("[data-detail]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const data = await apiAuthGet(`/api/admin/conversations/${button.dataset.detail}`, token);
        const detail = document.querySelector("#conversation-detail");
        detail.innerHTML = `
          <h3>会话详情 ${escapeHtml(data.conversation_id || "")}</h3>
          <div class="admin-grid">
            <section><h4>聊天记录</h4>${(data.history || []).map((m) => `<p><strong>${escapeHtml(m.sender || m.role)}</strong>：${escapeHtml(m.content)}</p>`).join("")}</section>
            <section><h4>Slots</h4>${jsonBlock(data.slots)}</section>
            <section><h4>Route Trace</h4>${jsonBlock(data.route_trace)}</section>
            <section><h4>Tool Calls</h4>${jsonBlock(data.tool_calls)}</section>
            <section><h4>Retrieved Docs</h4>${jsonBlock(data.retrieved_docs)}</section>
            <section><h4>Citations</h4>${jsonBlock(data.citations)}</section>
            <section><h4>Evaluation</h4>${jsonBlock(data.evaluation_result)}</section>
          </div>`;
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });

  // 认领会话
  viewEl.querySelectorAll("[data-assign]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await apiAuthPost(`/api/admin/conversations/${button.dataset.assign}/assign`, token, { agent_id: agentId });
        loadConversations(token, agentId);
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });

  // 人工回复
  viewEl.querySelectorAll("[data-reply]").forEach((button) => {
    button.addEventListener("click", async () => {
      const message = prompt("请输入人工客服回复", "您好，我是人工客服，请问您遇到了什么问题？");
      if (!message) return;
      try {
        await apiAuthPost(`/api/admin/conversations/${button.dataset.reply}/reply`, token, {
          agent_id: agentId,
          message,
        });
        loadConversations(token, agentId);
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });

  // 关闭会话
  viewEl.querySelectorAll("[data-resolve]").forEach((button) => {
    button.addEventListener("click", async () => {
      const resolution = prompt("请输入会话处理结果", "已处理完成。");
      if (!resolution) return;
      try {
        await apiAuthPost(`/api/admin/conversations/${button.dataset.resolve}/resolve`, token, {
          agent_id: agentId,
          resolution,
        });
        loadConversations(token, agentId);
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });
}
