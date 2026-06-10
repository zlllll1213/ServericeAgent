import { apiClient } from "../shared/api-client.js";
import { actionButton, escapeHtml, jsonBlock, renderTable, toast } from "../shared/ui-kit.js";

export async function loadLogs(container) {
  const data = await apiClient.get("/api/admin/chat-logs");
  const rows = data.map((item) => [
    escapeHtml(item.trace_id || "-"),
    escapeHtml(item.conversation_id),
    escapeHtml(item.user_message),
    escapeHtml(item.final_answer),
    escapeHtml(item.intent),
    escapeHtml(Number(item.confidence || 0).toFixed(2)),
    jsonBlock(item.route_trace),
    jsonBlock(item.tool_calls),
    jsonBlock(item.evaluation_result),
    escapeHtml(item.created_at),
  ]);
  container.innerHTML = renderTable(
    ["Trace", "Conversation", "User Message", "Answer", "Intent", "Confidence", "Route", "Tools", "Evaluation", "Created"],
    rows,
    { emptyMessage: "暂无 Agent 日志。", emptyAction: `<a class="empty-action" href="/">发送一条测试问题</a>` },
  );
}

function traceRows(items) {
  return items.map((item) => [
    actionButton(item.trace_id, "detail", item.trace_id, { class: "link-button" }),
    escapeHtml(item.conversation_id || "-"),
    escapeHtml(item.node_name),
    escapeHtml(item.success ? "success" : "failed"),
    escapeHtml(Number(item.latency_ms || 0).toFixed(2)),
    escapeHtml(item.created_at),
  ]);
}

async function renderTraceDetail(container, traceId) {
  const detail = container.querySelector("#trace-detail");
  detail.innerHTML = `<div class="loading-state">加载 Trace 链路</div>`;
  const chain = await apiClient.get(`/api/admin/traces/${traceId}`);
  detail.innerHTML = `
    <h3>Trace ${escapeHtml(chain.trace_id)}</h3>
    <div class="trace-chain">
      ${chain.nodes.map((node) => `
        <section class="decision-card">
          <h4>${escapeHtml(node.node_name)} · ${escapeHtml(node.latency_ms)} ms · ${escapeHtml(node.success ? "success" : "failed")}</h4>
          ${node.error_message ? `<p class="error-text">${escapeHtml(node.error_message)}</p>` : ""}
          <div class="admin-grid">
            <section><h5>Input</h5>${jsonBlock(node.input_state)}</section>
            <section><h5>Output</h5>${jsonBlock(node.output_state)}</section>
          </div>
        </section>`).join("")}
    </div>`;
}

export async function loadTraces(container) {
  const data = await apiClient.get("/api/admin/traces?page_size=80");
  container.innerHTML = `
    ${renderTable(
      ["Trace", "Conversation", "Node", "Success", "Latency(ms)", "Created"],
      traceRows(data),
      { emptyMessage: "暂无 Trace 记录。", emptyAction: `<a class="empty-action" href="/">触发一次 Agent 工作流</a>` },
    )}
    <section class="admin-detail" id="trace-detail"></section>`;
  container.onclick = async (event) => {
    const button = event.target.closest("[data-action='detail']");
    if (!button || !container.contains(button)) return;
    try {
      await renderTraceDetail(container, button.dataset.value);
    } catch (error) {
      toast(`Trace 加载失败：${error.message}`, "error");
    }
  };
}
