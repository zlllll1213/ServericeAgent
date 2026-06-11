import { state } from "../shared/state.js";
import { toast } from "../shared/ui-kit.js";
import { createChatCore } from "./core.js";
import { createChatUI } from "./ui.js";
import { promptPanel } from "./prompt.js";
import { createFeedbackPanel } from "./feedback.js";
import { createDebugPanel } from "./debug.js";
import { motion } from "./motion.js";

const elements = {
  form: document.querySelector("#chat-form"),
  input: document.querySelector("#message-input"),
  messages: document.querySelector("#messages"),
  errorText: document.querySelector("#error-text"),
  sendButton: document.querySelector("#send-button"),
  promptRow: document.querySelector("#prompt-row"),
  feedbackArea: document.querySelector("#feedback-area"),
  feedbackType: document.querySelector("#feedback-type"),
  feedbackStatus: document.querySelector("#feedback-status"),
  clearDebug: document.querySelector("#clear-debug"),
  root: document,
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

await motion.init().catch((error) => {
  document.documentElement.dataset.motionRuntime = "unavailable";
  console.warn(error.message);
});

const chatUI = createChatUI({ messages: elements.messages, motion });
const chatCore = createChatCore();
const debugPanel = createDebugPanel(elements, motion);
const feedbackPanel = createFeedbackPanel({
  root: elements.feedbackArea,
  typeSelect: elements.feedbackType,
  statusEl: elements.feedbackStatus,
});

function setSending(isSending) {
  elements.form.setAttribute("aria-busy", String(isSending));
  elements.sendButton.disabled = isSending;
  elements.sendButton.textContent = isSending ? "处理中" : "发送问题";
  if (motion.isReady()) {
    window.gsap.fromTo(elements.sendButton, { scale: 0.98 }, { scale: 1, clearProps: "transform" });
  }
}

async function sendMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) {
    elements.errorText.textContent = "请输入一个问题。";
    return;
  }
  elements.errorText.textContent = "";
  chatUI.append("user", trimmed);
  elements.input.value = "";
  chatUI.showTyping();
  setSending(true);
  feedbackPanel.disable("等待新的回答。");
  try {
    const result = await chatCore.send(trimmed);
    chatUI.hideTyping();
    chatUI.append(result.role, result.text);
    elements.sessionPill.textContent = `User U1001 · ${chatCore.getConversationId()}`;
    debugPanel.update(result.data, chatCore.getConversationId());
    feedbackPanel.enable(chatCore.getConversationId(), result.lastChatLogId);
  } catch (error) {
    chatUI.hideTyping();
    elements.errorText.textContent = `请求失败：${error.message}`;
    toast(`请求失败：${error.message}`, "error");
  } finally {
    setSending(false);
  }
}

chatCore.onHumanMessage((message) => {
  chatUI.append(message.role, message.text);
});

chatCore.onError((error) => {
  console.warn(error.message);
});

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(elements.input.value);
});

elements.clearDebug.addEventListener("click", () => debugPanel.clear());

promptPanel.init(elements.promptRow, sendMessage);
feedbackPanel.init();
chatUI.restoreHistory(state.getChatHistory());
if (chatCore.getConversationId()) {
  elements.sessionPill.textContent = `User U1001 · ${chatCore.getConversationId()}`;
  chatCore.syncConversationHistory(false).catch(() => {});
}
chatCore.startPolling();
motion.initPage();
