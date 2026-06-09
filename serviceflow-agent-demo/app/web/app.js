const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const errorText = document.querySelector("#error-text");
const sessionPill = document.querySelector("#session-pill");
const conversationIdEl = document.querySelector("#conversation-id");
const intentEl = document.querySelector("#intent");
const confidenceEl = document.querySelector("#confidence");
const ticketEl = document.querySelector("#ticket");
const pendingActionEl = document.querySelector("#pending-action");
const slotsEl = document.querySelector("#slots");
const missingSlotsEl = document.querySelector("#missing-slots");
const routeTraceEl = document.querySelector("#route-trace");
const routeDebugEl = document.querySelector("#route-debug");
const toolCallsEl = document.querySelector("#tool-calls");
const knowledgeHitsEl = document.querySelector("#knowledge-hits");
const retrievedDocsEl = document.querySelector("#retrieved-docs");
const citationsEl = document.querySelector("#citations");
const evaluationResultEl = document.querySelector("#evaluation-result");
const decisionTextEl = document.querySelector("#decision-text");
const retrieverStatusEl = document.querySelector("#retriever-status");
const clearDebug = document.querySelector("#clear-debug");
const sendButton = document.querySelector("#send-button");
const handoffButton = document.querySelector("#handoff-button");
const feedbackType = document.querySelector("#feedback-type");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let gsapReady = false;
let conversationId = null;
let historyCursor = 0;
let lastChatLogId = null;

async function runLocalScript(src) {
  const response = await fetch(src);
  if (!response.ok) {
    throw new Error(`无法加载动效脚本：${src}`);
  }
  const source = await response.text();
  // 当浏览器环境没有执行同步 vendor script 时，执行本地静态文件作为兜底。
  Function(source)();
}

async function ensureMotionRuntime() {
  if (reduceMotion) {
    document.documentElement.dataset.motionRuntime = "reduced";
    return;
  }
  if (!window.gsap) {
    await runLocalScript("/static/vendor/gsap.min.js");
  }
  if (!window.ScrollTrigger) {
    await runLocalScript("/static/vendor/ScrollTrigger.min.js");
  }
  gsapReady = Boolean(window.gsap);
  document.documentElement.dataset.motionRuntime = gsapReady ? "gsap" : "none";
  if (!gsapReady) return;
  gsap.defaults({ duration: 0.18, ease: "power2.out", overwrite: "auto" });
  if (window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);
  }
}

function animateFrom(targets, vars = {}) {
  if (!gsapReady) return;
  gsap.from(targets, {
    autoAlpha: 0,
    y: 8,
    scale: 0.99,
    clearProps: "all",
    ...vars,
  });
}

function animateUpdate(targets) {
  if (!gsapReady) return;
  gsap.fromTo(
    targets,
    { autoAlpha: 0.72, y: 6 },
    { autoAlpha: 1, y: 0, stagger: 0.025, clearProps: "all" },
  );
}

function initMotion() {
  if (!gsapReady) return;
  animateFrom([".topbar", ".chat-panel", ".debug-panel"], { y: 10, stagger: 0.04 });

  // ScrollTrigger 只用于证据卡片进入视口时的轻量提示，内容默认可见。
  if (window.ScrollTrigger) {
    ScrollTrigger.batch(".trace-card", {
      start: "top 92%",
      once: true,
      onEnter: (batch) => animateFrom(batch, { y: 10, stagger: 0.03 }),
    });
  }
}

function appendMessage(role, text) {
  // 所有消息都用 textContent 写入，避免用户输入被当成 HTML 执行。
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = {
    user: "User",
    assistant: "Agent",
    system: "System Confirm",
    tool: "Tool Result",
    human: "Human Agent",
  }[role] || "Agent";
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.append(label);
  article.append(paragraph);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  animateFrom(article, { y: role === "user" ? 10 : 8 });
}

function updateDebug(data) {
  // 调试面板展示的是 Agent 证据，不参与业务判断。
  conversationId = data.conversation_id || conversationId;
  sessionPill.textContent = conversationId ? `User U1001 · ${conversationId}` : "User U1001 · Conversation 未创建";
  conversationIdEl.textContent = conversationId || "None";
  intentEl.textContent = data.intent || "UNKNOWN";
  confidenceEl.textContent = Number(data.confidence || 0).toFixed(2);
  ticketEl.textContent = data.ticket_id || "None";
  pendingActionEl.textContent = data.pending_action || "None";
  decisionTextEl.textContent = data.reason
    ? `${data.reason}。当前路径：${(data.route_trace || []).join(" -> ")}`
    : "本次响应没有返回意图原因。";

  const retrievers = Array.from(new Set((data.retrieved_docs || []).map((doc) => doc.retriever).filter(Boolean)));
  retrieverStatusEl.textContent = retrievers.length ? `检索 ${retrievers.join(" / ")}` : "无知识库检索";

  routeTraceEl.innerHTML = "";
  for (const item of data.route_trace || []) {
    const li = document.createElement("li");
    li.textContent = item;
    routeTraceEl.append(li);
  }

  toolCallsEl.textContent = JSON.stringify(data.tool_calls || [], null, 2);
  retrievedDocsEl.textContent = JSON.stringify(data.retrieved_docs || [], null, 2);
  slotsEl.textContent = JSON.stringify(data.slots || {}, null, 2);
  missingSlotsEl.textContent = JSON.stringify(data.missing_slots || [], null, 2);
  routeDebugEl.textContent = JSON.stringify(data.route_debug || {}, null, 2);
  citationsEl.textContent = JSON.stringify(data.citations || [], null, 2);
  evaluationResultEl.textContent = JSON.stringify(data.evaluation_result || {}, null, 2);

  knowledgeHitsEl.innerHTML = "";
  for (const doc of data.retrieved_docs || []) {
    // Knowledge Hits 把知识库、来源和分数提出来，避免只能读大段 JSON。
    const li = document.createElement("li");
    const score = Number(doc.score || 0).toFixed(3);
    const title = document.createElement("strong");
    title.textContent = doc.knowledge_base || "unknown";
    const source = document.createElement("span");
    source.textContent = doc.source_file || doc.source || "unknown source";
    const meta = document.createElement("small");
    meta.textContent = `score ${score} · ${doc.retriever || "retriever"}`;
    li.append(title, source, meta);
    knowledgeHitsEl.append(li);
  }

  animateUpdate([
    ".decision-card",
    ".metrics div",
    "#route-trace li",
    "#knowledge-hits li",
  ]);
}

function setSending(isSending) {
  form.setAttribute("aria-busy", String(isSending));
  sendButton.disabled = isSending;
  sendButton.textContent = isSending ? "处理中" : "发送问题";
  if (gsapReady) {
    gsap.fromTo(sendButton, { scale: 0.98 }, { scale: 1, clearProps: "transform" });
  }
}

async function sendMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) {
    errorText.textContent = "请输入一个问题。";
    return;
  }

  errorText.textContent = "";
  appendMessage("user", trimmed);
  input.value = "";
  setSending(true);

  try {
    // 前端只调用统一 chat API，路由和工具调用全部交给后端 LangGraph。
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmed, user_id: "U1001", conversation_id: conversationId }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    appendMessage(messageRoleForResponse(data), data.answer);
    updateDebug(data);
    await syncConversationHistory(false);
    await refreshLastChatLogId();
  } catch (error) {
    errorText.textContent = `请求失败：${error.message}`;
  } finally {
    setSending(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

handoffButton.addEventListener("click", () => {
  sendMessage("我要找人工客服");
});

document.querySelectorAll("[data-feedback]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (!conversationId || !lastChatLogId) {
      errorText.textContent = "请先发送一条问题后再反馈。";
      return;
    }
    const isGood = button.dataset.feedback === "GOOD";
    const type = isGood ? "GOOD" : feedbackType.value;
    const response = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: conversationId,
        chat_log_id: lastChatLogId,
        user_id: "U1001",
        rating: isGood ? 5 : 2,
        feedback_type: type,
        comment: isGood ? "用户认为回答有帮助" : "用户认为回答没有帮助",
      }),
    });
    errorText.textContent = response.ok ? "反馈已提交。" : "反馈提交失败。";
  });
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    sendMessage(button.dataset.prompt);
  });
});

clearDebug.addEventListener("click", () => {
  conversationIdEl.textContent = "None";
  intentEl.textContent = "UNKNOWN";
  confidenceEl.textContent = "0.00";
  ticketEl.textContent = "None";
  pendingActionEl.textContent = "None";
  decisionTextEl.textContent = "发送一个问题后，这里会显示意图识别原因和下一步动作。";
  retrieverStatusEl.textContent = "检索待触发";
  routeTraceEl.innerHTML = "";
  knowledgeHitsEl.innerHTML = "";
  slotsEl.textContent = "{}";
  missingSlotsEl.textContent = "[]";
  routeDebugEl.textContent = "{}";
  toolCallsEl.textContent = "[]";
  retrievedDocsEl.textContent = "[]";
  citationsEl.textContent = "[]";
  evaluationResultEl.textContent = "{}";
  animateUpdate([".decision-card", ".metrics div"]);
});

function messageRoleForResponse(data) {
  const callNames = new Set((data.tool_calls || []).map((call) => call.name));
  if (callNames.has("create_return_request") || callNames.has("create_ticket")) {
    return "tool";
  }
  if (data.pending_action || (data.awaiting_user_input && (data.missing_slots || []).length > 0)) {
    return "system";
  }
  return "assistant";
}

async function refreshLastChatLogId() {
  if (!conversationId) return;
  const response = await fetch(`/api/conversations/${conversationId}/logs`);
  if (!response.ok) return;
  const logs = await response.json();
  lastChatLogId = logs.length ? logs[logs.length - 1].id : lastChatLogId;
}

async function syncConversationHistory(appendNew = true) {
  if (!conversationId) return;
  const response = await fetch(`/api/conversations/${conversationId}`);
  if (!response.ok) return;
  const conversation = await response.json();
  const history = conversation.history || [];
  if (!appendNew) {
    historyCursor = history.length;
    return;
  }
  for (const item of history.slice(historyCursor)) {
    if (item.sender === "human_agent") {
      appendMessage("human", item.content);
    }
  }
  historyCursor = history.length;
}

setInterval(() => {
  syncConversationHistory(true).catch(() => {});
}, 3000);

ensureMotionRuntime()
  .then(initMotion)
  .catch((error) => {
    document.documentElement.dataset.motionRuntime = "unavailable";
    console.warn(error.message);
  });
