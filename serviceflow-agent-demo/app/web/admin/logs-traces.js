// 日志与追踪视图 —— 聊天日志列表 + Agent Trace 列表 + 节点链路详情
// 从 admin.js loadLogs / loadTraces 完整迁移

import { apiAuthGet } from "../shared/api-client.js";
import { table, jsonBlock, escapeHtml, toast } from "../shared/ui-kit.js";

/** 加载聊天日志列表 */
export async function loadLogs(token) {
  const data = await apiAuthGet("/api/admin/chat-logs", token);

  const rows = data.map(
    (item) => `<tr>
      <td>${escapeHtml(item.trace_id || "-")}</td>
      <td>${escapeHtml(item.conversation_id)}</td>
      <td>${escapeHtml(item.user_message)}</td>
      <td>${escapeHtml(item.final_answer)}</td>
      <td>${escapeHtml(item.intent)}</td>
      <td>${Number(item.confidence).toFixed(2)}</td>
      <td>${jsonBlock(item.route_trace)}</td>
      <td>${jsonBlock(item.tool_calls)}</td>
      <td>${jsonBlock(item.evaluation_result)}</td>
      <td>${escapeHtml(item.created_at)}</td>
    </tr>`,
  );

  const viewEl = document.querySelector("#view-logs");
  viewEl.innerHTML = table(
    ["Trace", "Conversation", "User Message", "Answer", "Intent", "Confidence", "Route", "Tools", "Evaluation", "Created"],
    rows,
  );
}

/** 加载 Agent Trace 列表 */
export async function loadTraces(token) {
  const data = await apiAuthGet("/api/admin/traces?page_size=80", token);

  const rows = data.map(
    (item) => `<tr>
      <td><button class="link-button" data-trace-detail="${escapeHtml(item.trace_id)}">${escapeHtml(item.trace_id)}</button></td>
      <td>${escapeHtml(item.conversation_id || "-")}</td>
      <td>${escapeHtml(item.node_name)}</td>
      <td>${item.success ? "success" : "failed"}</td>
      <td>${Number(item.latency_ms || 0).toFixed(2)}</td>
      <td>${escapeHtml(item.created_at)}</td>
    </tr>`,
  );

  const viewEl = document.querySelector("#view-traces");
  viewEl.innerHTML =
    table(["Trace", "Conversation", "Node", "Success", "Latency(ms)", "Created"], rows) +
    `<section class="admin-detail" id="trace-detail"></section>`;

  // Trace 详情展开
  viewEl.querySelectorAll("[data-trace-detail]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const chain = await apiAuthGet(`/api/admin/traces/${button.dataset.traceDetail}`, token);
        const detail = document.querySelector("#trace-detail");
        detail.innerHTML = `
          <h3>Trace ${escapeHtml(chain.trace_id)}</h3>
          <div class="trace-chain">
            ${chain.nodes
              .map(
                (node) => `
              <section class="decision-card">
                <h4>${escapeHtml(node.node_name)} · ${node.latency_ms} ms · ${node.success ? "success" : "failed"}</h4>
                ${node.error_message ? `<p class="error-text">${escapeHtml(node.error_message)}</p>` : ""}
                <div class="admin-grid">
                  <section><h5>Input</h5>${jsonBlock(node.input_state)}</section>
                  <section><h5>Output</h5>${jsonBlock(node.output_state)}</section>
                </div>
              </section>`,
              )
              .join("")}
          </div>`;
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });
}
