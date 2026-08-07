export function initModeTabs() {
  const modeButtons = document.querySelectorAll(".mode-btn");
  const panels = {
    search: document.getElementById("panel-search"),
    add: document.getElementById("panel-add"),
    delete: document.getElementById("panel-delete"),
  };

  modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      modeButtons.forEach((candidate) => {
        candidate.classList.remove("is-active");
        candidate.setAttribute("aria-selected", "false");
      });

      Object.values(panels).forEach((panel) => {
        panel?.classList.remove("is-active");
      });

      button.classList.add("is-active");
      button.setAttribute("aria-selected", "true");
      panels[button.dataset.mode]?.classList.add("is-active");
    });
  });
}
