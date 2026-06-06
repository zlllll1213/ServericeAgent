const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const errorText = document.querySelector("#error-text");
const intentEl = document.querySelector("#intent");
const confidenceEl = document.querySelector("#confidence");
const ticketEl = document.querySelector("#ticket");
const routeTraceEl = document.querySelector("#route-trace");
const toolCallsEl = document.querySelector("#tool-calls");
const retrievedDocsEl = document.querySelector("#retrieved-docs");
const clearDebug = document.querySelector("#clear-debug");

function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.append(paragraph);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

function updateDebug(data) {
  intentEl.textContent = data.intent || "UNKNOWN";
  confidenceEl.textContent = Number(data.confidence || 0).toFixed(2);
  ticketEl.textContent = data.ticket_id || "None";

  routeTraceEl.innerHTML = "";
  for (const item of data.route_trace || []) {
    const li = document.createElement("li");
    li.textContent = item;
    routeTraceEl.append(li);
  }

  toolCallsEl.textContent = JSON.stringify(data.tool_calls || [], null, 2);
  retrievedDocsEl.textContent = JSON.stringify(data.retrieved_docs || [], null, 2);
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

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmed, user_id: "U1001" }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    appendMessage("assistant", data.answer);
    updateDebug(data);
  } catch (error) {
    errorText.textContent = `请求失败：${error.message}`;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    sendMessage(button.dataset.prompt);
  });
});

clearDebug.addEventListener("click", () => {
  intentEl.textContent = "UNKNOWN";
  confidenceEl.textContent = "0.00";
  ticketEl.textContent = "None";
  routeTraceEl.innerHTML = "";
  toolCallsEl.textContent = "[]";
  retrievedDocsEl.textContent = "[]";
});
