// 评测报告视图 —— 最新报告内容 + 下载链接 + 历史列表
// 从 admin.js loadEvaluation 完整迁移

import { apiAuthGet } from "../shared/api-client.js";
import { table, escapeHtml } from "../shared/ui-kit.js";

/** 加载评测报告 */
export async function loadEvaluation(token) {
  const [reports, latest] = await Promise.all([
    apiAuthGet("/api/admin/evaluation-reports", token),
    apiAuthGet("/api/admin/evaluation-reports/latest", token),
  ]);

  const rows = reports.map(
    (item) => `<tr>
      <td>${escapeHtml(item.filename)}</td>
      <td>${escapeHtml(item.updated_at)}</td>
      <td>${item.size}</td>
      <td>${escapeHtml(item.path)}</td>
    </tr>`,
  );

  const download = latest.download_url
    ? `<a class="admin-download" href="${latest.download_url}">下载 Markdown 报告</a>`
    : "";

  const viewEl = document.querySelector("#view-evaluation");
  viewEl.innerHTML = `
    <section class="admin-detail">
      <h3>最近一次评测：${escapeHtml(latest.filename || "暂无")}</h3>
      ${download}
      <pre>${escapeHtml(latest.content || "")}</pre>
    </section>
    ${table(["Filename", "Updated", "Size", "Path"], rows)}`;
}
