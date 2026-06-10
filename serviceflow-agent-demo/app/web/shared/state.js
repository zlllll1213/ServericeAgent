// 本地状态持久化 —— 封装 localStorage，统一 key 前缀 "sf_"
// 页面刷新后聊天历史和会话 ID 可恢复；localStorage 不可用时降级为内存变量。

const PREFIX = "sf_";

// 内存降级变量（localStorage 不可用时使用）
const _memory = {};

function _storage() {
  try {
    const key = "__sf_test__";
    localStorage.setItem(key, "1");
    localStorage.removeItem(key);
    return localStorage;
  } catch {
    return null;
  }
}

/** 读取持久化值，自动 JSON.parse */
export function getState(key) {
  const storage = _storage();
  if (storage) {
    const raw = storage.getItem(PREFIX + key);
    if (raw == null) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }
  return _memory[PREFIX + key] ?? null;
}

/** 写入持久化值，自动 JSON.stringify */
export function setState(key, value) {
  const storage = _storage();
  if (storage) {
    storage.setItem(PREFIX + key, JSON.stringify(value));
    return;
  }
  _memory[PREFIX + key] = value;
}

/** 移除指定 key */
export function removeState(key) {
  const storage = _storage();
  if (storage) {
    storage.removeItem(PREFIX + key);
    return;
  }
  delete _memory[PREFIX + key];
}
