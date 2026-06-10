// 指标看板视图 —— 系统概览卡片 + 意图分布 + 近 7 日趋势
// 从 admin.js loadMetrics 完整迁移

import { apiAuthGet } from "../shared/api-client.js";
import { jsonBlock } from "../shared/ui-kit.js";

/** 加载 Metrics 概览 + 每日趋势 */
export async function loadMetrics(token) {
  const [overview, daily] = await Promise.all([
    apiAuthGet("/api/admin/metrics/overview", token),
    apiAuthGet("/api/admin/metrics/daily", token),
  ]);

  const cards = [
    ["今日对话数", overview.total_chats_today],
    ["平均响应时间", `${overview.avg_latency_ms} ms`],
    ["P95 响应时间", `${overview.p95_latency_ms} ms`],
    ["工具成功率", overview.tool_success_rate],
    ["人工转接率", overview.human_transfer_rate],
    ["差评率", overview.negative_feedback_rate],
    ["错误率", overview.error_rate],
  ]
    .map(
      ([label, value]) =>
        `<section class="metric-card"><span>${label}</span><strong>${value}</strong></section>`,
    )
    .join("");

  const viewEl = document.querySelector("#view-metrics");
  viewEl.innerHTML = `
    <section class="metrics-grid">${cards}</section>
    <section class="admin-grid">
      <section><h3>意图分布</h3>${jsonBlock(overview.intent_distribution)}</section>
      <section><h3>最近 7 天</h3>${jsonBlock(daily)}</section>
    </section>`;
}
