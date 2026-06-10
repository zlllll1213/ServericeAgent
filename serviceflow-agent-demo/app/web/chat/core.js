import { apiClient } from "../shared/api-client.js";
import { state } from "../shared/state.js";

function roleForResponse(data) {
  const callNames = new Set((data.tool_calls || []).map((call) => call.name));
  if (callNames.has("create_return_request") || callNames.has("create_ticket")) {
    return "tool";
  }
  if (data.pending_action || (data.awaiting_user_input && (data.missing_slots || []).length > 0)) {
    return "system";
  }
  return "assistant";
}

export function createChatCore({ userId = "U1001" } = {}) {
  let conversationId = state.getConversationId();
  let historyCursor = 0;
  let sending = false;
  let pollingId = null;
  const messageCallbacks = new Set();
  const humanCallbacks = new Set();
  const errorCallbacks = new Set();

  function emit(callbacks, payload) {
    callbacks.forEach((callback) => callback(payload));
  }

  async function refreshLastChatLogId() {
    if (!conversationId) return null;
    const logs = await apiClient.get(`/api/conversations/${conversationId}/logs`, { auth: false });
    return logs.length ? logs[logs.length - 1].id : null;
  }

  async function send(text) {
    const trimmed = text.trim();
    if (!trimmed) {
      throw new Error("请输入一个问题。");
    }
    if (sending) {
      throw new Error("上一条问题仍在处理中。");
    }
    sending = true;
    try {
      const data = await apiClient.post(
        "/api/chat",
        { message: trimmed, user_id: userId, conversation_id: conversationId },
        { auth: false },
      );
      conversationId = data.conversation_id || conversationId;
      state.setConversationId(conversationId);
      const lastChatLogId = await refreshLastChatLogId();
      historyCursor = await currentHistoryLength();
      const message = { role: roleForResponse(data), text: data.answer, data, lastChatLogId };
      emit(messageCallbacks, message);
      return message;
    } catch (error) {
      emit(errorCallbacks, error);
      throw error;
    } finally {
      sending = false;
    }
  }

  async function currentHistoryLength() {
    if (!conversationId) return 0;
    const conversation = await apiClient.get(`/api/conversations/${conversationId}`, { auth: false });
    return (conversation.history || []).length;
  }

  async function syncConversationHistory(appendNew = true) {
    if (!conversationId) return;
    const conversation = await apiClient.get(`/api/conversations/${conversationId}`, { auth: false });
    const history = conversation.history || [];
    if (!appendNew) {
      historyCursor = history.length;
      return;
    }
    for (const item of history.slice(historyCursor)) {
      if (item.sender === "human_agent") {
        emit(humanCallbacks, { role: "human", text: item.content });
      }
    }
    historyCursor = history.length;
  }

  function startPolling() {
    stopPolling();
    pollingId = window.setInterval(() => {
      syncConversationHistory(true).catch((error) => emit(errorCallbacks, error));
    }, 3000);
  }

  function stopPolling() {
    if (pollingId) {
      window.clearInterval(pollingId);
      pollingId = null;
    }
  }

  function reset() {
    conversationId = null;
    historyCursor = 0;
    state.clearChat();
  }

  return {
    send,
    startPolling,
    stopPolling,
    syncConversationHistory,
    getConversationId: () => conversationId,
    reset,
    onMessage: (callback) => messageCallbacks.add(callback),
    onHumanMessage: (callback) => humanCallbacks.add(callback),
    onError: (callback) => errorCallbacks.add(callback),
  };
}
