import { apiClient } from "../shared/api-client.js";
import { escapeHtml, jsonBlock } from "../shared/ui-kit.js";

export async function loadMetrics(container) {
  const [overview, daily] = await Promise.all([
    apiClient.get("/api/admin/metrics/overview"),
    apiClient.get("/api/admin/metrics/daily"),
  ]);
  const cards = [
    ["今日对话数", overview.total_chats_today],
    ["平均响应时间", `${overview.avg_latency_ms} ms`],
    ["P95 响应时间", `${overview.p95_latency_ms} ms`],
    ["工具成功率", overview.tool_success_rate],
    ["RAG 平均延迟", `${overview.rag_avg_latency_ms} ms`],
    ["人工转接率", overview.human_transfer_rate],
    ["差评率", overview.negative_feedback_rate],
    ["错误率", overview.error_rate],
  ].map(([label, value]) => `
    <section class="metric-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </section>`).join("");
  container.innerHTML = `
    <section class="metrics-grid">${cards}</section>
    <section class="admin-grid">
      <section><h3>意图分布</h3>${jsonBlock(overview.intent_distribution)}</section>
      <section><h3>最近 7 天</h3>${jsonBlock(daily)}</section>
    </section>`;
}

