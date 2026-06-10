const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let gsapReady = false;

async function runLocalScript(src) {
  const response = await fetch(src);
  if (!response.ok) {
    throw new Error(`无法加载动效脚本：${src}`);
  }
  const source = await response.text();
  // vendor 文件仍由浏览器直接加载；这里作为 module 环境下的兜底。
  Function(source)();
}

export const motion = {
  async init() {
    if (reduceMotion) {
      document.documentElement.dataset.motionRuntime = "reduced";
      return false;
    }
    if (!window.gsap) {
      await runLocalScript("/static/vendor/gsap.min.js");
    }
    if (!window.ScrollTrigger) {
      await runLocalScript("/static/vendor/ScrollTrigger.min.js");
    }
    gsapReady = Boolean(window.gsap);
    document.documentElement.dataset.motionRuntime = gsapReady ? "gsap" : "none";
    if (!gsapReady) return false;
    window.gsap.defaults({ duration: 0.18, ease: "power2.out", overwrite: "auto" });
    if (window.ScrollTrigger) {
      window.gsap.registerPlugin(window.ScrollTrigger);
    }
    return true;
  },

  isReady() {
    return gsapReady;
  },

  animateIn(targets, vars = {}) {
    if (!gsapReady) return;
    window.gsap.from(targets, {
      autoAlpha: 0,
      y: 8,
      scale: 0.99,
      clearProps: "all",
      ...vars,
    });
  },

  animateUpdate(targets) {
    if (!gsapReady) return;
    window.gsap.fromTo(
      targets,
      { autoAlpha: 0.72, y: 6 },
      { autoAlpha: 1, y: 0, stagger: 0.025, clearProps: "all" },
    );
  },

  initPage() {
    if (!gsapReady) return;
    this.animateIn([".topbar", ".chat-panel", ".debug-panel"], { y: 10, stagger: 0.04 });
    if (window.ScrollTrigger) {
      window.ScrollTrigger.batch(".trace-card", {
        start: "top 92%",
        once: true,
        onEnter: (batch) => this.animateIn(batch, { y: 10, stagger: 0.03 }),
      });
    }
  },
};
