import { apiClient } from "../shared/api-client.js";
import { escapeHtml, renderTable } from "../shared/ui-kit.js";

export async function loadEvaluation(container) {
  const [reports, latest] = await Promise.all([
    apiClient.get("/api/admin/evaluation-reports"),
    apiClient.get("/api/admin/evaluation-reports/latest"),
  ]);
  const rows = reports.map((item) => [
    escapeHtml(item.filename),
    escapeHtml(item.updated_at),
    escapeHtml(item.size),
    escapeHtml(item.path),
  ]);
  const download = latest.download_url
    ? `<a class="admin-download" href="${escapeHtml(latest.download_url)}">下载 Markdown 报告</a>`
    : "";
  container.innerHTML = `
    <section class="admin-detail">
      <h3>最近一次评测：${escapeHtml(latest.filename || "暂无")}</h3>
      ${download}
      <pre>${escapeHtml(latest.content)}</pre>
    </section>
    ${renderTable(
      ["Filename", "Updated", "Size", "Path"],
      rows,
      { emptyMessage: "暂无评测报告。", emptyAction: `<span>执行 make eval 后这里会显示报告。</span>` },
    )}`;
}

