// 动画系统 —— GSAP/ScrollTrigger 懒加载 + 用户动效偏好尊重
// 从 app.js 动画部分完整迁移，GSAP 加载失败时静默降级

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

let gsapReady = false;

/** 动态加载 vendor 脚本，使用 Function() 注入全局 gsap/ScrollTrigger */
async function _runLocalScript(src) {
  const response = await fetch(src);
  if (!response.ok) {
    throw new Error(`无法加载动效脚本：${src}`);
  }
  const source = await response.text();
  // 当浏览器没有同步执行 vendor script 时，执行本地静态文件作为兜底
  Function(source)();
}

/** 初始化动画运行时 —— 懒加载 GSAP + ScrollTrigger */
export async function ensureMotionRuntime() {
  if (reduceMotion) {
    document.documentElement.dataset.motionRuntime = "reduced";
    return;
  }
  if (!window.gsap) {
    await _runLocalScript("/static/vendor/gsap.min.js");
  }
  if (!window.ScrollTrigger) {
    await _runLocalScript("/static/vendor/ScrollTrigger.min.js");
  }
  gsapReady = Boolean(window.gsap);
  document.documentElement.dataset.motionRuntime = gsapReady ? "gsap" : "none";
  if (!gsapReady) return;
  gsap.defaults({ duration: 0.18, ease: "power2.out", overwrite: "auto" });
  if (window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);
  }
}

/** 入场动画 —— 元素从下往上淡入 */
export function animateFrom(targets, vars = {}) {
  if (!gsapReady) return;
  gsap.from(targets, {
    autoAlpha: 0,
    y: 8,
    scale: 0.99,
    clearProps: "all",
    ...vars,
  });
}

/** 更新动画 —— 闪烁/高亮效果 */
export function animateUpdate(targets) {
  if (!gsapReady) return;
  gsap.fromTo(
    targets,
    { autoAlpha: 0.72, y: 6 },
    { autoAlpha: 1, y: 0, stagger: 0.025, clearProps: "all" },
  );
}

/** 页面初始动画 + ScrollTrigger 批量注册 */
export function initMotion() {
  if (!gsapReady) return;
  animateFrom([".topbar", ".chat-panel", ".debug-panel"], { y: 10, stagger: 0.04 });

  // ScrollTrigger 只用于证据卡片进入视口时的轻量提示，内容默认可见
  if (window.ScrollTrigger) {
    ScrollTrigger.batch(".trace-card", {
      start: "top 92%",
      once: true,
      onEnter: (batch) => animateFrom(batch, { y: 10, stagger: 0.03 }),
    });
  }
}

/** 检查动画运行时是否就绪 */
export function isMotionReady() {
  return gsapReady;
}
