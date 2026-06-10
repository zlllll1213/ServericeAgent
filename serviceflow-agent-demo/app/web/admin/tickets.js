// 工单管理视图 —— 列表、认领、处理、关闭
// 从 admin.js loadTickets 完整迁移

import { apiAuthGet, apiAuthPost } from "../shared/api-client.js";
import { table, toast } from "../shared/ui-kit.js";

/** 加载工单列表 */
export async function loadTickets(token, agentId) {
  const data = await apiAuthGet("/api/admin/tickets", token);

  const rows = data.map(
    (item) => `<tr>
      <td>${item.ticket_id}</td>
      <td>${item.user_id}</td>
      <td>${item.issue_type}</td>
      <td>${item.priority}</td>
      <td>${item.status}</td>
      <td>${item.assigned_agent_id || "-"}</td>
      <td>${item.created_at}</td>
      <td class="admin-actions">
        <button data-ticket-assign="${item.ticket_id}">认领</button>
        <button data-ticket-resolve="${item.ticket_id}">处理</button>
        <button data-ticket-close="${item.ticket_id}">关闭</button>
      </td>
    </tr>`,
  );

  const viewEl = document.querySelector("#view-tickets");
  viewEl.innerHTML = table(["Ticket", "User", "Issue", "Priority", "Status", "Agent", "Created", "操作"], rows);

  // 认领
  viewEl.querySelectorAll("[data-ticket-assign]").forEach((button) =>
    button.addEventListener("click", async () => {
      try {
        await apiAuthPost(`/api/admin/tickets/${button.dataset.ticketAssign}/assign`, token, { agent_id: agentId });
        loadTickets(token, agentId);
      } catch (error) {
        toast(error.message, "error");
      }
    }),
  );

  // 处理
  viewEl.querySelectorAll("[data-ticket-resolve]").forEach((button) =>
    button.addEventListener("click", async () => {
      const resolution = prompt("请输入工单处理结果", "已联系用户并解决问题。");
      if (!resolution) return;
      try {
        await apiAuthPost(`/api/admin/tickets/${button.dataset.ticketResolve}/resolve`, token, {
          agent_id: agentId,
          resolution,
        });
        loadTickets(token, agentId);
      } catch (error) {
        toast(error.message, "error");
      }
    }),
  );

  // 关闭
  viewEl.querySelectorAll("[data-ticket-close]").forEach((button) =>
    button.addEventListener("click", async () => {
      try {
        await apiAuthPost(`/api/admin/tickets/${button.dataset.ticketClose}/close`, token);
        loadTickets(token, agentId);
      } catch (error) {
        toast(error.message, "error");
      }
    }),
  );
}
