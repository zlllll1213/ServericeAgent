const role = new URLSearchParams(location.search).get("role") || "agent";
const agentId = role === "admin" ? "A1001" : "S1001";
const tokenStorageKey = `serviceflow_admin_token_${role}`;
const titleEl = document.querySelector("#admin-title");
const roleEl = document.querySelector("#admin-role");
const views = {
  conversations: document.querySelector("#view-conversations"),
  tickets: document.querySelector("#view-tickets"),
  knowledge: document.querySelector("#view-knowledge"),
  logs: document.querySelector("#view-logs"),
  traces: document.querySelector("#view-traces"),
  metrics: document.querySelector("#view-metrics"),
  evaluation: document.querySelector("#view-evaluation"),
  feedback: document.querySelector("#view-feedback"),
};
let currentView = "conversations";
roleEl.textContent = role;

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    currentView = button.dataset.view;
    document.querySelectorAll("[data-view]").forEach((item) => item.classList.toggle("active", item === button));
    Object.entries(views).forEach(([name, node]) => node.classList.toggle("hidden", name !== currentView));
    titleEl.textContent = button.textContent;
    loadCurrentView();
  });
});

document.querySelector("#admin-refresh").addEventListener("click", () => loadCurrentView());

async function ensureAccessToken() {
  const cached = sessionStorage.getItem(tokenStorageKey);
  if (cached) return cached;

  const defaultUsername = role === "admin" ? "admin" : "service_agent";
  const username = window.prompt("请输入后台账号", defaultUsername);
  const password = window.prompt("请输入后台密码");
  if (!username || !password) throw new Error("缺少后台登录信息");

  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error(`登录失败：HTTP ${response.status}`);
  const data = await response.json();
  sessionStorage.setItem(tokenStorageKey, data.access_token);
  roleEl.textContent = data.role || role;
  return data.access_token;
}

async function requestJson(url, options = {}) {
  const token = await ensureAccessToken();
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(options.headers || {}) },
  });
  if (response.status === 401) {
    // token 过期或被替换时清理本地缓存，下一次请求重新登录。
    sessionStorage.removeItem(tokenStorageKey);
  }
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function table(headers, rows) {
  return `<div class="admin-table-wrap"><table class="admin-table"><thead><tr>${headers.map((item) => `<th>${item}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
}

function jsonBlock(value) {
  return `<pre>${escapeHtml(JSON.stringify(value || {}, null, 2))}</pre>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}

async function loadConversations() {
  const data = await requestJson("/api/admin/conversations?page_size=50");
  const rows = data.map(
    (item) => `<tr>
      <td>${item.conversation_id}</td>
      <td>${item.user_id}</td>
      <td>${item.current_intent || ""}</td>
      <td>${item.status}</td>
      <td>${item.handoff_status}</td>
      <td>${item.assigned_agent_id || "-"}</td>
      <td>${item.updated_at}</td>
      <td class="admin-actions">
        <button data-detail="${item.conversation_id}">查看详情</button>
        <button data-assign="${item.conversation_id}">认领</button>
        <button data-reply="${item.conversation_id}">人工回复</button>
        <button data-resolve="${item.conversation_id}">关闭会话</button>
      </td>
    </tr>`,
  );
  views.conversations.innerHTML = table(["Conversation", "User", "Intent", "Status", "Handoff", "Agent", "Updated", "操作"], rows)
    + `<section class="admin-detail" id="conversation-detail"></section>`;
  bindConversationActions();
}

function bindConversationActions() {
  views.conversations.querySelectorAll("[data-detail]").forEach((button) => {
    button.addEventListener("click", async () => {
      const data = await requestJson(`/api/admin/conversations/${button.dataset.detail}`);
      document.querySelector("#conversation-detail").innerHTML = `
        <h3>会话详情 ${data.conversation_id}</h3>
        <div class="admin-grid">
          <section><h4>聊天记录</h4>${(data.history || []).map((m) => `<p><strong>${m.sender || m.role}</strong>：${escapeHtml(m.content)}</p>`).join("")}</section>
          <section><h4>Slots</h4>${jsonBlock(data.slots)}</section>
          <section><h4>Route Trace</h4>${jsonBlock(data.route_trace)}</section>
          <section><h4>Tool Calls</h4>${jsonBlock(data.tool_calls)}</section>
          <section><h4>Retrieved Docs</h4>${jsonBlock(data.retrieved_docs)}</section>
          <section><h4>Citations</h4>${jsonBlock(data.citations)}</section>
          <section><h4>Evaluation</h4>${jsonBlock(data.evaluation_result)}</section>
        </div>`;
    });
  });
  views.conversations.querySelectorAll("[data-assign]").forEach((button) => {
    button.addEventListener("click", async () => {
      await requestJson(`/api/admin/conversations/${button.dataset.assign}/assign`, { method: "POST", body: JSON.stringify({ agent_id: agentId }) });
      loadConversations();
    });
  });
  views.conversations.querySelectorAll("[data-reply]").forEach((button) => {
    button.addEventListener("click", async () => {
      const message = prompt("请输入人工客服回复", "您好，我是人工客服，请问您遇到了什么问题？");
      if (!message) return;
      await requestJson(`/api/admin/conversations/${button.dataset.reply}/reply`, { method: "POST", body: JSON.stringify({ agent_id: agentId, message }) });
      loadConversations();
    });
  });
  views.conversations.querySelectorAll("[data-resolve]").forEach((button) => {
    button.addEventListener("click", async () => {
      const resolution = prompt("请输入会话处理结果", "已处理完成。");
      if (!resolution) return;
      await requestJson(`/api/admin/conversations/${button.dataset.resolve}/resolve`, { method: "POST", body: JSON.stringify({ agent_id: agentId, resolution }) });
      loadConversations();
    });
  });
}

async function loadTickets() {
  const data = await requestJson("/api/admin/tickets");
  const rows = data.map(
    (item) => `<tr>
      <td>${item.ticket_id}</td><td>${item.user_id}</td><td>${item.issue_type}</td><td>${item.priority}</td><td>${item.status}</td><td>${item.assigned_agent_id || "-"}</td><td>${item.created_at}</td>
      <td class="admin-actions"><button data-ticket-assign="${item.ticket_id}">认领</button><button data-ticket-resolve="${item.ticket_id}">处理</button><button data-ticket-close="${item.ticket_id}">关闭</button></td>
    </tr>`,
  );
  views.tickets.innerHTML = table(["Ticket", "User", "Issue", "Priority", "Status", "Agent", "Created", "操作"], rows);
  views.tickets.querySelectorAll("[data-ticket-assign]").forEach((button) => button.addEventListener("click", async () => {
    await requestJson(`/api/admin/tickets/${button.dataset.ticketAssign}/assign`, { method: "POST", body: JSON.stringify({ agent_id: agentId }) });
    loadTickets();
  }));
  views.tickets.querySelectorAll("[data-ticket-resolve]").forEach((button) => button.addEventListener("click", async () => {
    const resolution = prompt("请输入工单处理结果", "已联系用户并解决问题。");
    if (!resolution) return;
    await requestJson(`/api/admin/tickets/${button.dataset.ticketResolve}/resolve`, { method: "POST", body: JSON.stringify({ agent_id: agentId, resolution }) });
    loadTickets();
  }));
  views.tickets.querySelectorAll("[data-ticket-close]").forEach((button) => button.addEventListener("click", async () => {
    await requestJson(`/api/admin/tickets/${button.dataset.ticketClose}/close`, { method: "POST" });
    loadTickets();
  }));
}

async function loadKnowledge() {
  const data = await requestJson("/api/admin/knowledge-documents");
  const rows = data.map((item) => `<tr><td>${item.title}</td><td>${item.knowledge_base}</td><td>${item.status}</td><td>${item.version}</td><td>${item.updated_at}</td><td class="admin-actions"><button data-publish="${item.doc_id}">发布</button><button data-archive="${item.doc_id}">归档</button></td></tr>`);
  views.knowledge.innerHTML = `
    <section class="admin-form">
      <input id="knowledge-title" placeholder="标题" />
      <select id="knowledge-base"><option value="tech">tech</option><option value="policy">policy</option><option value="product">product</option></select>
      <textarea id="knowledge-content" placeholder="这里是文档正文"></textarea>
      <button id="knowledge-create">新建文档</button>
      <button id="knowledge-reindex">重建索引</button>
    </section>
    ${table(["Title", "KB", "Status", "Version", "Updated", "操作"], rows)}`;
  document.querySelector("#knowledge-create").addEventListener("click", async () => {
    await requestJson("/api/admin/knowledge-documents", {
      method: "POST",
      body: JSON.stringify({
        title: document.querySelector("#knowledge-title").value,
        knowledge_base: document.querySelector("#knowledge-base").value,
        content: document.querySelector("#knowledge-content").value,
      }),
    });
    loadKnowledge();
  });
  document.querySelector("#knowledge-reindex").addEventListener("click", () => requestJson("/api/admin/knowledge-documents/reindex", { method: "POST" }));
  views.knowledge.querySelectorAll("[data-publish]").forEach((button) => button.addEventListener("click", async () => {
    await requestJson(`/api/admin/knowledge-documents/${button.dataset.publish}/publish`, { method: "POST" });
    loadKnowledge();
  }));
  views.knowledge.querySelectorAll("[data-archive]").forEach((button) => button.addEventListener("click", async () => {
    await requestJson(`/api/admin/knowledge-documents/${button.dataset.archive}/archive`, { method: "POST" });
    loadKnowledge();
  }));
}

async function loadLogs() {
  const data = await requestJson("/api/admin/chat-logs");
  const rows = data.map((item) => `<tr><td>${item.trace_id || "-"}</td><td>${item.conversation_id}</td><td>${escapeHtml(item.user_message)}</td><td>${escapeHtml(item.final_answer)}</td><td>${item.intent}</td><td>${Number(item.confidence).toFixed(2)}</td><td>${jsonBlock(item.route_trace)}</td><td>${jsonBlock(item.tool_calls)}</td><td>${jsonBlock(item.evaluation_result)}</td><td>${item.created_at}</td></tr>`);
  views.logs.innerHTML = table(["Trace", "Conversation", "User Message", "Answer", "Intent", "Confidence", "Route", "Tools", "Evaluation", "Created"], rows);
}

async function loadTraces() {
  const data = await requestJson("/api/admin/traces?page_size=80");
  const rows = data.map((item) => `<tr>
    <td><button class="link-button" data-trace-detail="${item.trace_id}">${item.trace_id}</button></td>
    <td>${item.conversation_id || "-"}</td>
    <td>${item.node_name}</td>
    <td>${item.success ? "success" : "failed"}</td>
    <td>${Number(item.latency_ms || 0).toFixed(2)}</td>
    <td>${item.created_at}</td>
  </tr>`);
  views.traces.innerHTML = table(["Trace", "Conversation", "Node", "Success", "Latency(ms)", "Created"], rows)
    + `<section class="admin-detail" id="trace-detail"></section>`;
  views.traces.querySelectorAll("[data-trace-detail]").forEach((button) => {
    button.addEventListener("click", async () => {
      const chain = await requestJson(`/api/admin/traces/${button.dataset.traceDetail}`);
      document.querySelector("#trace-detail").innerHTML = `
        <h3>Trace ${chain.trace_id}</h3>
        <div class="trace-chain">
          ${chain.nodes.map((node) => `
            <section class="decision-card">
              <h4>${node.node_name} · ${node.latency_ms} ms · ${node.success ? "success" : "failed"}</h4>
              ${node.error_message ? `<p class="error-text">${escapeHtml(node.error_message)}</p>` : ""}
              <div class="admin-grid">
                <section><h5>Input</h5>${jsonBlock(node.input_state)}</section>
                <section><h5>Output</h5>${jsonBlock(node.output_state)}</section>
              </div>
            </section>`).join("")}
        </div>`;
    });
  });
}

async function loadMetrics() {
  const [overview, daily] = await Promise.all([requestJson("/api/admin/metrics/overview"), requestJson("/api/admin/metrics/daily")]);
  const cards = [
    ["今日对话数", overview.total_chats_today],
    ["平均响应时间", `${overview.avg_latency_ms} ms`],
    ["P95 响应时间", `${overview.p95_latency_ms} ms`],
    ["工具成功率", overview.tool_success_rate],
    ["人工转接率", overview.human_transfer_rate],
    ["差评率", overview.negative_feedback_rate],
    ["错误率", overview.error_rate],
  ].map(([label, value]) => `<section class="metric-card"><span>${label}</span><strong>${value}</strong></section>`).join("");
  views.metrics.innerHTML = `
    <section class="metrics-grid">${cards}</section>
    <section class="admin-grid">
      <section><h3>意图分布</h3>${jsonBlock(overview.intent_distribution)}</section>
      <section><h3>最近 7 天</h3>${jsonBlock(daily)}</section>
    </section>`;
}

async function loadEvaluation() {
  const [reports, latest] = await Promise.all([requestJson("/api/admin/evaluation-reports"), requestJson("/api/admin/evaluation-reports/latest")]);
  const rows = reports.map((item) => `<tr><td>${item.filename}</td><td>${item.updated_at}</td><td>${item.size}</td><td>${item.path}</td></tr>`);
  const download = latest.download_url ? `<a class="admin-download" href="${latest.download_url}">下载 Markdown 报告</a>` : "";
  views.evaluation.innerHTML = `
    <section class="admin-detail">
      <h3>最近一次评测：${latest.filename || "暂无"}</h3>
      ${download}
      <pre>${escapeHtml(latest.content)}</pre>
    </section>
    ${table(["Filename", "Updated", "Size", "Path"], rows)}`;
}

async function loadFeedback() {
  const [items, summary] = await Promise.all([requestJson("/api/admin/feedback"), requestJson("/api/admin/evaluation-summary")]);
  const rows = items.map((item) => `<tr><td>${item.conversation_id}</td><td>${item.chat_log_id}</td><td>${item.rating}</td><td>${item.feedback_type}</td><td>${escapeHtml(item.comment || "")}</td><td>${item.created_at}</td></tr>`);
  views.feedback.innerHTML = `<section class="decision-card">${jsonBlock(summary)}</section>` + table(["Conversation", "Log", "Rating", "Type", "Comment", "Created"], rows);
}

function loadCurrentView() {
  return {
    conversations: loadConversations,
    tickets: loadTickets,
    knowledge: loadKnowledge,
    logs: loadLogs,
    traces: loadTraces,
    metrics: loadMetrics,
    evaluation: loadEvaluation,
    feedback: loadFeedback,
  }[currentView]().catch((error) => {
    views[currentView].innerHTML = `<p class="error-text">加载失败：${error.message}</p>`;
  });
}

loadCurrentView();
