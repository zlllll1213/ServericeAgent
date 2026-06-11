const PREFIX = "sf_";

function keyFor(key) {
  return `${PREFIX}${key}`;
}

function parseJson(value, fallback) {
  if (!value) return fallback;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

export const state = {
  get(key, fallback = null) {
    const value = localStorage.getItem(keyFor(key));
    return parseJson(value, fallback);
  },

  set(key, value) {
    localStorage.setItem(keyFor(key), JSON.stringify(value));
  },

  remove(key) {
    localStorage.removeItem(keyFor(key));
  },

  getConversationId() {
    return localStorage.getItem(keyFor("conversation_id"));
  },

  setConversationId(id) {
    if (id) {
      localStorage.setItem(keyFor("conversation_id"), id);
    }
  },

  getChatHistory() {
    return this.get("chat_history", []);
  },

  appendMessage(role, text) {
    const history = this.getChatHistory();
    history.push({ role, text, createdAt: new Date().toISOString() });
    this.set("chat_history", history.slice(-80));
  },

  clearChat() {
    this.remove("chat_history");
    localStorage.removeItem(keyFor("conversation_id"));
  },

  clear() {
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith(PREFIX)) {
        localStorage.removeItem(key);
      }
    }
  },
};
