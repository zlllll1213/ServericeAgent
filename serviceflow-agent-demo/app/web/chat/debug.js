import { setText } from "../shared/ui-kit.js";

export function createDebugPanel(elements, motion) {
  function update(data, conversationId) {
    // 调试面板展示的是 Agent 证据，不参与业务判断。
    elements.sessionPill.textContent = conversationId ? `User U1001 · ${conversationId}` : "User U1001 · Conversation 未创建";
    setText("#conversation-id", conversationId || "None", elements.root);
    setText("#intent", data.intent || "UNKNOWN", elements.root);
    setText("#confidence", Number(data.confidence || 0).toFixed(2), elements.root);
    setText("#ticket", data.ticket_id || "None", elements.root);
    setText("#pending-action", data.pending_action || "None", elements.root);
    elements.decisionText.textContent = data.reason
      ? `${data.reason}。当前路径：${(data.route_trace || []).join(" -> ")}`
      : "本次响应没有返回意图原因。";

    const retrievers = Array.from(new Set((data.retrieved_docs || []).map((doc) => doc.retriever).filter(Boolean)));
    elements.retrieverStatus.textContent = retrievers.length ? `检索 ${retrievers.join(" / ")}` : "无知识库检索";

    elements.routeTrace.innerHTML = "";
    for (const item of data.route_trace || []) {
      const li = document.createElement("li");
      li.textContent = item;
      elements.routeTrace.append(li);
    }

    elements.toolCalls.textContent = JSON.stringify(data.tool_calls || [], null, 2);
    elements.retrievedDocs.textContent = JSON.stringify(data.retrieved_docs || [], null, 2);
    elements.slots.textContent = JSON.stringify(data.slots || {}, null, 2);
    elements.missingSlots.textContent = JSON.stringify(data.missing_slots || [], null, 2);
    elements.routeDebug.textContent = JSON.stringify(data.route_debug || {}, null, 2);
    elements.citations.textContent = JSON.stringify(data.citations || [], null, 2);
    elements.evaluationResult.textContent = JSON.stringify(data.evaluation_result || {}, null, 2);

    elements.knowledgeHits.innerHTML = "";
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
      elements.knowledgeHits.append(li);
    }

    motion.animateUpdate([".decision-card", ".metrics div", "#route-trace li", "#knowledge-hits li"]);
  }

  function clear() {
    elements.sessionPill.textContent = "User U1001 · Conversation 未创建";
    elements.conversationId.textContent = "None";
    elements.intent.textContent = "UNKNOWN";
    elements.confidence.textContent = "0.00";
    elements.ticket.textContent = "None";
    elements.pendingAction.textContent = "None";
    elements.decisionText.textContent = "发送一个问题后，这里会显示意图识别原因和下一步动作。";
    elements.retrieverStatus.textContent = "检索待触发";
    elements.routeTrace.innerHTML = "";
    elements.knowledgeHits.innerHTML = "";
    elements.slots.textContent = "{}";
    elements.missingSlots.textContent = "[]";
    elements.routeDebug.textContent = "{}";
    elements.toolCalls.textContent = "[]";
    elements.retrievedDocs.textContent = "[]";
    elements.citations.textContent = "[]";
    elements.evaluationResult.textContent = "{}";
    motion.animateUpdate([".decision-card", ".metrics div"]);
  }

  return { update, clear };
}
