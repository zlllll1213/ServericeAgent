import { apiClient } from "../shared/api-client.js";
import { actionButton, confirmAction, escapeHtml, promptAction, renderTable, toast } from "../shared/ui-kit.js";
import { adminContext } from "./context.js";

function ticketRows(items) {
  return items.map((item) => [
    escapeHtml(item.ticket_id),
    escapeHtml(item.user_id),
    escapeHtml(item.issue_type),
    escapeHtml(item.priority),
    escapeHtml(item.status),
    escapeHtml(item.assigned_agent_id || "-"),
    escapeHtml(item.created_at),
    `<div class="admin-actions">
      ${actionButton("认领", "assign", item.ticket_id)}
      ${actionButton("处理", "resolve", item.ticket_id)}
      ${actionButton("关闭", "close", item.ticket_id)}
    </div>`,
  ]);
}

async function assignTicket(ticketId) {
  await apiClient.post(`/api/admin/tickets/${ticketId}/assign`, { agent_id: adminContext().agentId });
  toast("已认领工单。", "success");
}

async function resolveTicket(ticketId) {
  const resolution = await promptAction({
    title: "处理工单",
    label: "处理结果",
    defaultValue: "已联系用户并解决问题。",
    multiline: true,
  });
  if (!resolution) return false;
  await apiClient.post(`/api/admin/tickets/${ticketId}/resolve`, { agent_id: adminContext().agentId, resolution });
  toast("工单已处理。", "success");
  return true;
}

async function closeTicket(ticketId) {
  const confirmed = await confirmAction("关闭后该工单会进入 CLOSED 状态。", {
    title: "关闭工单",
    confirmLabel: "关闭",
    destructive: true,
  });
  if (!confirmed) return false;
  await apiClient.post(`/api/admin/tickets/${ticketId}/close`, {});
  toast("工单已关闭。", "success");
  return true;
}

export async function loadTickets(container) {
  const data = await apiClient.get("/api/admin/tickets");
  container.innerHTML = renderTable(
    ["Ticket", "User", "Issue", "Priority", "Status", "Agent", "Created", "操作"],
    ticketRows(data),
    { emptyMessage: "暂无工单。", emptyAction: `<a class="empty-action" href="/">触发一次转人工场景</a>` },
  );
  container.onclick = async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || !container.contains(button)) return;
    try {
      if (button.dataset.action === "assign") await assignTicket(button.dataset.value);
      if (button.dataset.action === "resolve" && !await resolveTicket(button.dataset.value)) return;
      if (button.dataset.action === "close" && !await closeTicket(button.dataset.value)) return;
      await loadTickets(container);
    } catch (error) {
      toast(`操作失败：${error.message}`, "error");
    }
  };
}
