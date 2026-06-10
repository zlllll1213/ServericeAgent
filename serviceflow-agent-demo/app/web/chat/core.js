// 消息收发引擎 —— 聊天核心逻辑：发送、接收、轮询人工消息
// 从 app.js sendMessage / syncConversationHistory / refreshLastChatLogId 完整迁移

import { apiPost, apiGet } from "../shared/api-client.js";
import { getState, setState } from "../shared/state.js";
import { appendMessage } from "./ui.js";
import { updateDebug, getConversationId, setConversationId } from "./debug.js";

const STATE_KEY = "chat_conversation_id";

// DOM 引用
const _form = document.querySelector("#chat-form");
const _input = document.querySelector("#message-input");
const _errorText = document.querySelector("#error-text");
const _sendButton = document.querySelector("#send-button");
const _handoffButton = document.querySelector("#handoff-button");

let _lastChatLogId = null;
let _historyCursor = 0;
let _pollTimer = null;
let _conversationId = getState(STATE_KEY) || null;

// 恢复保存的 conversationId
if (_conversationId) {
  setConversationId(_conversationId);
}

/** 根据响应数据判断消息气泡角色 */
function _messageRoleForResponse(data) {
  const callNames = new Set((data.tool_calls || []).map((call) => call.name));
  if (callNames.has("create_return_request") || callNames.has("create_ticket")) {
    return "tool";
  }
  if (data.pending_action || (data.awaiting_user_input && (data.missing_slots || []).length > 0)) {
    return "system";
  }
  return "assistant";
}

/** 设置发送状态（防重复提交） */
function _setSending(isSending) {
  _form.setAttribute("aria-busy", String(isSending));
  _sendButton.disabled = isSending;
  _sendButton.textContent = isSending ? "处理中" : "发送问题";
  // 按钮微动效由 motion 模块处理
}

/** 获取最新的 chat_log_id（用于反馈提交） */
async function _refreshLastChatLogId() {
  const cid = getConversationId();
  if (!cid) return;
  try {
    const logs = await apiGet(`/api/conversations/${cid}/logs`);
    _lastChatLogId = logs.length ? logs[logs.length - 1].id : _lastChatLogId;
  } catch {
    // 静默失败
  }
}

/** 同步会话历史，展示人工坐席的新消息 */
async function _syncConversationHistory(appendNew = true) {
  const cid = getConversationId();
  if (!cid) return;
  try {
    const conversation = await apiGet(`/api/conversations/${cid}`);
    const history = conversation.history || [];
    if (!appendNew) {
      _historyCursor = history.length;
      return;
    }
    // 只展示人工坐席（human_agent）的新消息
    for (const item of history.slice(_historyCursor)) {
      if (item.sender === "human_agent") {
        appendMessage("human", item.content);
      }
    }
    _historyCursor = history.length;
  } catch {
    // 静默失败
  }
}

/** 发送消息 */
export async function sendMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) {
    _errorText.textContent = "请输入一个问题。";
    return;
  }

  _errorText.textContent = "";
  appendMessage("user", trimmed);
  _input.value = "";
  _setSending(true);

  try {
    // 所有问题统一进入 LangGraph chat API，路由和工具由后端处理
    const data = await apiPost("/api/chat", {
      message: trimmed,
      user_id: "U1001",
      conversation_id: getConversationId(),
    });

    // 根据响应更新会话 ID
    if (data.conversation_id) {
      setConversationId(data.conversation_id);
      setState(STATE_KEY, data.conversation_id);
    }

    // 展示回答 + 更新调试面板
    appendMessage(_messageRoleForResponse(data), data.answer);
    updateDebug(data);

    // 同步历史和最新的 chat_log_id
    await _syncConversationHistory(false);
    await _refreshLastChatLogId();
  } catch (error) {
    _errorText.textContent = `请求失败：${error.message}`;
  } finally {
    _setSending(false);
  }
}

/** 启动人工消息轮询（每 3 秒） */
export function startPolling() {
  if (_pollTimer) return;
  _pollTimer = setInterval(() => {
    _syncConversationHistory(true).catch(() => {});
  }, 3000);
}

/** 停止轮询 */
export function stopPolling() {
  if (_pollTimer) {
    clearInterval(_pollTimer);
    _pollTimer = null;
  }
}

/** 获取最新 chat_log_id（供反馈模块使用） */
export function getLastChatLogId() {
  return _lastChatLogId;
}

/** 重置会话 */
export function reset() {
  _conversationId = null;
  _historyCursor = 0;
  _lastChatLogId = null;
  setConversationId(null);
  setState(STATE_KEY, null);
}

/** 初始化 —— 绑定事件 */
export function initCore() {
  // 聊天表单提交
  _form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(_input.value);
  });

  // 转人工按钮
  _handoffButton.addEventListener("click", () => {
    sendMessage("我要找人工客服");
  });

  // 启动轮询
  startPolling();
}
