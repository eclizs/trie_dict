import { initAccountControls } from "../features/account.js";
import { initEntryActions } from "../features/entry-actions.js";
import { initModeTabs } from "../features/mode-tabs.js";
import { initSearchWorkspace } from "../features/search-workspace.js";

document.addEventListener("DOMContentLoaded", () => {
  initAccountControls();
  initModeTabs();
  initSearchWorkspace();
  initEntryActions();
});
