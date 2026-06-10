// 聊天页入口 —— 组装所有聊天模块，作为 <script type="module"> 的入口点
// 使用 top-level await 等待动画运行时初始化

import { ensureMotionRuntime, initMotion } from "./motion.js";
import { initCore } from "./core.js";
import { initPrompt } from "./prompt.js";
import { initFeedback } from "./feedback.js";
import { clearDebug } from "./debug.js";

// 初始化动画运行时（GSAP 懒加载 + 降级）
try {
  await ensureMotionRuntime();
  initMotion();
} catch (error) {
  document.documentElement.dataset.motionRuntime = "unavailable";
  console.warn("动画初始化失败：", error.message);
}

// 初始化核心引擎（绑定事件 + 启动人工消息轮询）
initCore();

// 绑定预设场景按钮
initPrompt();

// 绑定反馈按钮
initFeedback();

// 绑定调试面板清空按钮
document.querySelector("#clear-debug").addEventListener("click", clearDebug);
