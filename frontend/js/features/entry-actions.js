import {
  deleteAllEntries,
  deleteEntry,
  insertEntry,
  searchEntries,
  uploadEntries,
} from "../core/api.js";
import {
  closeDropdown,
  formatError,
  renderMessage,
  renderResults,
  setStatus,
  updateHighlight,
} from "../core/ui.js";

export function initEntryActions() {
  const addInput = document.getElementById("add-input");
  const fileInput = document.getElementById("file");
  const columnInput = document.getElementById("csv-header-input");
  const addButton = document.getElementById("add-btn");
  const uploadButton = document.getElementById("upload-btn");
  const addStatus = document.getElementById("add-status");
  const uploadStatus = document.getElementById("upload-status");
  const deleteInput = document.getElementById("delete-input");
  const deleteButton = document.getElementById("delete-btn");
  const deleteAllButton = document.getElementById("delete-all-btn");
  const deleteStatus = document.getElementById("delete-status");
  const deleteResults = document.getElementById("results-list-delete");
  const confirmationDialog = document.getElementById("delete-all-dialog");
  const confirmDeleteAllButton = document.getElementById("confirm-delete-all-btn");
  const cancelDeleteAllButton = document.getElementById("cancel-delete-all-btn");
  const dialogStatus = document.getElementById("delete-all-dialog-status");
  const resultsList = document.getElementById("results-list-delete");
  const deleteBox = document.querySelector(".delete-box");

  let debounceTimer;
  let highlightedIndex = -1;

  const deleteAllErrorMessage = (error) => {
    if (error.status === 404) {
      return "The delete-all endpoint is unavailable. Restart the server and try again.";
    }

    return formatError(error.detail, "Could not delete all entries.");
  };

  uploadButton?.addEventListener("click", async () => {
    if (!fileInput?.files?.length) {
      setStatus(uploadStatus, "Select a file first.", "err");
      return;
    }

    uploadButton.disabled = true;
    setStatus(uploadStatus, "Importing entries…");

    try {
      const data = await uploadEntries(
        fileInput.files[0],
        columnInput?.value.trim() || ""
      );
      const insertedCount = data.inserted?.length || 0;
      const failures = Array.isArray(data.failed) ? data.failed : [];
      const failureDetails = failures
        .map((item) => `${item.word}: ${item.reason}`)
        .join("\n");
      const summary = `${insertedCount} inserted, ${failures.length} failed.`;

      setStatus(
        uploadStatus,
        failureDetails ? `${summary}\n${failureDetails}` : summary,
        failures.length ? "err" : "ok"
      );
    } catch (error) {
      setStatus(
        uploadStatus,
        formatError(error.detail, "Could not import the file."),
        "err"
      );
    } finally {
      uploadButton.disabled = false;
    }
  });

  addButton?.addEventListener("click", async () => {
    const word = addInput?.value.trim();
    if (!word) {
      setStatus(addStatus, "Type a word first.", "err");
      return;
    }

    addButton.disabled = true;

    try {
      const data = await insertEntry(word);
      setStatus(addStatus, data.message || `Added "${word}".`, "ok");
      addInput.value = "";
    } catch (error) {
      setStatus(
        addStatus,
        formatError(error.detail, `Could not add "${word}".`),
        "err"
      );
    } finally {
      addButton.disabled = false;
    }
  });

  const searchForDeletion = async (prefix) => {
    try {
      const data = await searchEntries(prefix);
      renderResults(data.words || [], deleteResults, deleteInput, (word) => {
        deleteInput.value = word;
      });
    } catch {
      renderMessage("No matches found", deleteInput, deleteResults);
    }
  };

  deleteInput?.addEventListener("input", () => {
    window.clearTimeout(debounceTimer);
    highlightedIndex = -1;
    debounceTimer = window.setTimeout(
      () => searchForDeletion(deleteInput.value.trim()),
      200
    );
  });

  deleteInput?.addEventListener("keydown", (event) => {
    const items = deleteResults.querySelectorAll(".entry-item:not(.is-empty)");

    if (!deleteResults.classList.contains("is-open") || items.length === 0) {
      if (!deleteInput.value) return;
    }

    if (event.key === "ArrowDown" || (event.key === "Tab" && !event.shiftKey)) {
      event.preventDefault();
      highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
      updateHighlight(items, highlightedIndex);
    } else if (event.key === "ArrowUp" || (event.key === "Tab" && event.shiftKey)) {
      event.preventDefault();
      highlightedIndex = Math.max(highlightedIndex - 1, 0);
      updateHighlight(items, highlightedIndex);
    } else if (event.key === "Enter" && highlightedIndex >= 0 && items[highlightedIndex]) {
      event.preventDefault();
      deleteInput.value = items[highlightedIndex].dataset.word;
      closeDropdown(deleteInput, deleteResults);
    } else if (event.key === "Escape") {
      closeDropdown(deleteInput, deleteResults);
    }
  });

  deleteButton?.addEventListener("click", async () => {
    const word = deleteInput?.value.trim();
    if (!word) {
      setStatus(deleteStatus, "Type a word first.", "err");
      return;
    }

    deleteButton.disabled = true;

    try {
      const data = await deleteEntry(word);
      setStatus(deleteStatus, data.message || `Deleted "${word}".`, "ok");
      deleteInput.value = "";
      closeDropdown(deleteInput, deleteResults);
    } catch (error) {
      setStatus(
        deleteStatus,
        formatError(error.detail, `Could not delete "${word}".`),
        "err"
      );
    } finally {
      deleteButton.disabled = false;
    }
  });

  const performDeleteAll = async () => {
    deleteAllButton.disabled = true;
    if (confirmDeleteAllButton) confirmDeleteAllButton.disabled = true;
    if (cancelDeleteAllButton) cancelDeleteAllButton.disabled = true;
    confirmationDialog?.close();
    setStatus(deleteStatus, "Deleting every entry…");

    try {
      const data = await deleteAllEntries();
      setStatus(deleteStatus, data.message || "Deleted all entries.", "ok");
      deleteInput.value = "";
      closeDropdown(deleteInput, deleteResults);
      deleteResults.replaceChildren();
      document.dispatchEvent(new CustomEvent("dictionary:cleared"));
    } catch (error) {
      setStatus(
        deleteStatus,
        deleteAllErrorMessage(error),
        "err"
      );
    } finally {
      deleteAllButton.disabled = false;
      if (confirmDeleteAllButton) confirmDeleteAllButton.disabled = false;
      if (cancelDeleteAllButton) cancelDeleteAllButton.disabled = false;
    }
  };

  deleteAllButton?.addEventListener("click", () => {
    setStatus(dialogStatus, "");

    if (typeof confirmationDialog?.showModal === "function") {
      confirmationDialog.showModal();
      return;
    }

    if (window.confirm("Delete every dictionary entry? This cannot be undone.")) {
      performDeleteAll();
    }
  });

  confirmDeleteAllButton?.addEventListener("click", performDeleteAll);
  cancelDeleteAllButton?.addEventListener("click", () => confirmationDialog?.close());

  document.addEventListener("click", (event) => {
    if (!deleteBox?.contains(event.target)) {
      closeDropdown(deleteInput, resultsList);
    }
  });
}
