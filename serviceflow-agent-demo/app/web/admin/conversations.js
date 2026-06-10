import { apiClient } from "../shared/api-client.js";
import { actionButton, escapeHtml, jsonBlock, promptAction, renderTable, toast } from "../shared/ui-kit.js";
import { adminContext } from "./context.js";

function conversationRows(items) {
  return items.map((item) => [
    escapeHtml(item.conversation_id),
    escapeHtml(item.user_id),
    escapeHtml(item.current_intent || "-"),
    escapeHtml(item.status),
    escapeHtml(item.handoff_status),
    escapeHtml(item.assigned_agent_id || "-"),
    escapeHtml(item.last_message_preview || "-"),
    escapeHtml(item.updated_at),
    `<div class="admin-actions">
      ${actionButton("查看", "detail", item.conversation_id)}
      ${actionButton("认领", "assign", item.conversation_id)}
      ${actionButton("回复", "reply", item.conversation_id)}
      ${actionButton("关闭", "resolve", item.conversation_id)}
    </div>`,
  ]);
}

function historyHtml(history = []) {
  if (!history.length) {
    return `<section class="empty-state"><p>暂无聊天记录。</p></section>`;
  }
  return history.map((message) => `
    <p class="admin-message-line">
      <strong>${escapeHtml(message.sender || message.role || "unknown")}</strong>
      <span>${escapeHtml(message.content || "")}</span>
    </p>`).join("");
}

async function renderDetail(container, conversationId) {
  const detail = container.querySelector("#conversation-detail");
  detail.innerHTML = `<div class="loading-state">加载会话详情</div>`;
  const data = await apiClient.get(`/api/admin/conversations/${conversationId}`);
  detail.innerHTML = `
    <h3>会话详情 ${escapeHtml(data.conversation_id)}</h3>
    <div class="admin-grid">
      <section><h4>聊天记录</h4>${historyHtml(data.history)}</section>
      <section><h4>Slots</h4>${jsonBlock(data.slots)}</section>
      <section><h4>Route Trace</h4>${jsonBlock(data.route_trace)}</section>
      <section><h4>Tool Calls</h4>${jsonBlock(data.tool_calls)}</section>
      <section><h4>Retrieved Docs</h4>${jsonBlock(data.retrieved_docs)}</section>
      <section><h4>Citations</h4>${jsonBlock(data.citations)}</section>
      <section><h4>Evaluation</h4>${jsonBlock(data.evaluation_result)}</section>
      <section><h4>Chat Logs</h4>${jsonBlock(data.chat_logs)}</section>
    </div>`;
}

async function assignConversation(conversationId) {
  const { agentId } = adminContext();
  await apiClient.post(`/api/admin/conversations/${conversationId}/assign`, { agent_id: agentId });
  toast("已认领会话。", "success");
}

async function replyConversation(conversationId) {
  const { agentId } = adminContext();
  const message = await promptAction({
    title: "人工回复",
    label: "回复内容",
    defaultValue: "您好，我是人工客服，请问您遇到了什么问题？",
    multiline: true,
  });
  if (!message) return false;
  await apiClient.post(`/api/admin/conversations/${conversationId}/reply`, { agent_id: agentId, message });
  toast("人工回复已发送。", "success");
  return true;
}

async function resolveConversation(conversationId) {
  const { agentId } = adminContext();
  const resolution = await promptAction({
    title: "关闭会话",
    label: "处理结果",
    defaultValue: "已处理完成。",
    multiline: true,
    confirmLabel: "关闭会话",
  });
  if (!resolution) return false;
  await apiClient.post(`/api/admin/conversations/${conversationId}/resolve`, { agent_id: agentId, resolution });
  toast("会话已关闭。", "success");
  return true;
}

export async function loadConversations(container) {
  const data = await apiClient.get("/api/admin/conversations?page_size=50");
  container.innerHTML = `
    ${renderTable(
      ["Conversation", "User", "Intent", "Status", "Handoff", "Agent", "Preview", "Updated", "操作"],
      conversationRows(data),
      { emptyMessage: "暂无会话。", emptyAction: `<a class="empty-action" href="/">打开客服演示</a>` },
    )}
    <section class="admin-detail" id="conversation-detail"></section>`;

  container.onclick = async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || !container.contains(button)) return;
    const conversationId = button.dataset.value;
    const action = button.dataset.action;
    try {
      if (action === "detail") await renderDetail(container, conversationId);
      if (action === "assign") {
        await assignConversation(conversationId);
        await loadConversations(container);
      }
      if (action === "reply" && await replyConversation(conversationId)) await loadConversations(container);
      if (action === "resolve" && await resolveConversation(conversationId)) await loadConversations(container);
    } catch (error) {
      toast(`操作失败：${error.message}`, "error");
    }
  };
}
