export function initModeTabs() {
  const modeButtons = document.querySelectorAll(".mode-btn");
  const guideSections = document.querySelectorAll(".feature-guide-section[data-guide-mode]");
  const panels = {
    search: document.getElementById("panel-search"),
    add: document.getElementById("panel-add"),
    delete: document.getElementById("panel-delete"),
  };

  const selectMode = (mode) => {
    modeButtons.forEach((candidate) => {
      const isActive = candidate.dataset.mode === mode;
      candidate.classList.toggle("is-active", isActive);
      candidate.setAttribute("aria-selected", String(isActive));
    });

    Object.entries(panels).forEach(([panelMode, panel]) => {
      panel?.classList.toggle("is-active", panelMode === mode);
    });

    guideSections.forEach((section) => {
      const isActive = section.dataset.guideMode === mode;
      section.hidden = !isActive;
      section.classList.toggle("is-active", isActive);
    });
  };

  modeButtons.forEach((button) => {
    button.addEventListener("click", () => selectMode(button.dataset.mode));
  });

  const initialMode = document.querySelector(".mode-btn.is-active")?.dataset.mode;
  selectMode(initialMode || "search");
}
