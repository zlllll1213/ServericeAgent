export function createHashRouter(routes, { defaultRoute }) {
  let currentView = "";

  function routeFromHash() {
    const name = location.hash.replace(/^#/, "");
    return routes[name] ? name : defaultRoute;
  }

  async function navigate(viewName) {
    const target = routes[viewName] ? viewName : defaultRoute;
    if (location.hash.replace(/^#/, "") !== target) {
      location.hash = target;
      return;
    }
    await render(target);
  }

  async function render(viewName = routeFromHash()) {
    currentView = routes[viewName] ? viewName : defaultRoute;
    await routes[currentView]();
  }

  function init() {
    window.addEventListener("hashchange", () => render().catch(console.error));
    if (!location.hash) {
      location.hash = defaultRoute;
      return;
    }
    render().catch(console.error);
  }

  return {
    init,
    navigate,
    getCurrentView: () => currentView,
  };
}
