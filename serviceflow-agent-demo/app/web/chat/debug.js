// 调试可视化面板 —— 展示 Agent 证据：意图、路由轨迹、工具调用、知识库命中
// 从 app.js updateDebug / clearDebug 完整迁移

import { animateUpdate } from "./motion.js";

// 缓存的 DOM 引用
const _dom = {
  sessionPill: document.querySelector("#session-pill"),
  conversationId: document.querySelector("#conversation-id"),
  intent: document.querySelector("#intent"),
  confidence: document.querySelector("#confidence"),
  ticket: document.querySelector("#ticket"),
  pendingAction: document.querySelector("#pending-action"),
  slots: document.querySelector("#slots"),
  missingSlots: document.querySelector("#missing-slots"),
  routeTrace: document.querySelector("#route-trace"),
  routeDebug: document.querySelector("#route-debug"),
  toolCalls: document.querySelector("#tool-calls"),
  knowledgeHits: document.querySelector("#knowledge-hits"),
  retrievedDocs: document.querySelector("#retrieved-docs"),
  citations: document.querySelector("#citations"),
  evaluationResult: document.querySelector("#evaluation-result"),
  decisionText: document.querySelector("#decision-text"),
  retrieverStatus: document.querySelector("#retriever-status"),
};

// 当前会话 ID（闭包维护，不暴露全局）
let _conversationId = null;

/** 根据 ChatResponse 更新调试面板所有区域 */
export function updateDebug(data) {
  _conversationId = data.conversation_id || _conversationId;

  // 会话 pill + 指标网格
  _dom.sessionPill.textContent = _conversationId
    ? `User U1001 · ${_conversationId}`
    : "User U1001 · Conversation 未创建";
  _dom.conversationId.textContent = _conversationId || "None";
  _dom.intent.textContent = data.intent || "UNKNOWN";
  _dom.confidence.textContent = Number(data.confidence || 0).toFixed(2);
  _dom.ticket.textContent = data.ticket_id || "None";
  _dom.pendingAction.textContent = data.pending_action || "None";

  // 决策卡片：意图原因 + 当前路径
  _dom.decisionText.textContent = data.reason
    ? `${data.reason}。当前路径：${(data.route_trace || []).join(" -> ")}`
    : "本次响应没有返回意图原因。";

  // 检索状态 chip
  const retrievers = Array.from(
    new Set((data.retrieved_docs || []).map((doc) => doc.retriever).filter(Boolean)),
  );
  _dom.retrieverStatus.textContent = retrievers.length
    ? `检索 ${retrievers.join(" / ")}`
    : "无知识库检索";

  // Route Trace 有序列表
  _dom.routeTrace.innerHTML = "";
  for (const item of data.route_trace || []) {
    const li = document.createElement("li");
    li.textContent = item;
    _dom.routeTrace.append(li);
  }

  // JSON 区域
  _dom.toolCalls.textContent = JSON.stringify(data.tool_calls || [], null, 2);
  _dom.retrievedDocs.textContent = JSON.stringify(data.retrieved_docs || [], null, 2);
  _dom.slots.textContent = JSON.stringify(data.slots || {}, null, 2);
  _dom.missingSlots.textContent = JSON.stringify(data.missing_slots || [], null, 2);
  _dom.routeDebug.textContent = JSON.stringify(data.route_debug || {}, null, 2);
  _dom.citations.textContent = JSON.stringify(data.citations || [], null, 2);
  _dom.evaluationResult.textContent = JSON.stringify(data.evaluation_result || {}, null, 2);

  // Knowledge Hits 列表：提取知识库、来源和分数
  _dom.knowledgeHits.innerHTML = "";
  for (const doc of data.retrieved_docs || []) {
    const li = document.createElement("li");
    const score = Number(doc.score || 0).toFixed(3);
    const title = document.createElement("strong");
    title.textContent = doc.knowledge_base || "unknown";
    const source = document.createElement("span");
    source.textContent = doc.source_file || doc.source || "unknown source";
    const meta = document.createElement("small");
    meta.textContent = `score ${score} · ${doc.retriever || "retriever"}`;
    li.append(title, source, meta);
    _dom.knowledgeHits.append(li);
  }

  // 微动效
  animateUpdate([
    ".decision-card",
    ".metrics div",
    "#route-trace li",
    "#knowledge-hits li",
  ]);
}

/** 重置调试面板到初始状态 */
export function clearDebug() {
  _conversationId = null;
  _dom.conversationId.textContent = "None";
  _dom.intent.textContent = "UNKNOWN";
  _dom.confidence.textContent = "0.00";
  _dom.ticket.textContent = "None";
  _dom.pendingAction.textContent = "None";
  _dom.decisionText.textContent = "发送一个问题后，这里会显示意图识别原因和下一步动作。";
  _dom.retrieverStatus.textContent = "检索待触发";
  _dom.sessionPill.textContent = "User U1001 · Conversation 未创建";
  _dom.routeTrace.innerHTML = "";
  _dom.knowledgeHits.innerHTML = "";
  _dom.slots.textContent = "{}";
  _dom.missingSlots.textContent = "[]";
  _dom.routeDebug.textContent = "{}";
  _dom.toolCalls.textContent = "[]";
  _dom.retrievedDocs.textContent = "[]";
  _dom.citations.textContent = "[]";
  _dom.evaluationResult.textContent = "{}";
  animateUpdate([".decision-card", ".metrics div"]);
}

/** 获取当前会话 ID */
export function getConversationId() {
  return _conversationId;
}

/** 设置当前会话 ID */
export function setConversationId(id) {
  _conversationId = id;
}
