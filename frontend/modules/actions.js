import * as utils from "./utils.js";

export function initActions() {
  const addInput = document.getElementById("add-input");
  const fileInput = document.getElementById("file");
  const addBtn = document.getElementById("add-btn");
  const uploadBtn = document.getElementById("uploadBtn");
  const addStatus = document.getElementById("add-status");
  const deleteInput = document.getElementById("delete-input");
  const deleteBtn = document.getElementById("delete-btn");
  const deleteStatus = document.getElementById("delete-status");
  const uploadStatus = document.getElementById("upload-status");
  const resultsList = document.getElementById("results-list-delete");

  let debounceTimer;
  let highlightedIndex = -1;

  uploadBtn?.addEventListener("click", async () => {
    if (!fileInput?.files?.length) {
      utils.setStatus(addStatus, "Select a file first.", "err");
      return;
    }
    
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const res = await fetch("/admin/insert_excel", {
      method: "POST",
      body: formData,
    });

    const data = await res.json().catch(() => ({}));
    const fails = Array.isArray(data.failed)
      ? data.failed.map((item) => item.reason).filter(Boolean)
      : [];

    const statusMsg = `${fails.length} insertion(s) failed:\n${fails.length ? fails.join("\n") : ""}`;
    utils.setStatus(uploadStatus, statusMsg, "err");

    if (!res.ok) {
      alert("Upload failed");
    }
  });

  addBtn?.addEventListener("click", async () => {
    const word = addInput?.value.trim();
    if (!word) {
      utils.setStatus(addStatus, "Type a word first.", "err");
      return;
    }

    try {
      const res = await fetch(`/insert?word=${encodeURIComponent(word)}`, {
        method: "POST",
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        utils.setStatus(addStatus, data.message || `Added "${word}".`, "ok");
        addInput.value = "";
      } else {
        utils.setStatus(addStatus, data.detail || `Could not add "${word}".`, "err");
      }
    } catch (error) {
      utils.setStatus(addStatus, "Error: Unprocessable content", "err");
    }
  });

  deleteInput?.addEventListener("input", () => {
    clearTimeout(debounceTimer);

    const raw = deleteInput.value.trim();

    let prefix = raw;

    debounceTimer = setTimeout(
      () =>
        utils.runSearch(prefix, resultsList, deleteInput, (word) => {
          deleteInput.value = word;
        }),
      200
    );
  });

  deleteInput?.addEventListener("keydown", (event) => {
    const items = resultsList.querySelectorAll(".entry-item:not(.is-empty)");
    if (!resultsList.classList.contains("is-open") || items.length === 0)
    {
      if(deleteInput.value === "") return;
    }

    if (event.key === "ArrowDown" || (event.key === "Tab" && !event.shiftKey)) {
      event.preventDefault();
      highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
      utils.updateHighlight(items, highlightedIndex);
    } else if (event.key === "ArrowUp" || (event.key === "Tab" && event.shiftKey)) {
      event.preventDefault();
      highlightedIndex = Math.max(highlightedIndex - 1, 0);
      utils.updateHighlight(items, highlightedIndex);
    } else if (event.key === "Enter") {
      if (highlightedIndex >= 0 && items[highlightedIndex]) {
        event.preventDefault();
        deleteInput.value = items[highlightedIndex].dataset.word;
        utils.closeDropdown(deleteInput, resultsList);
      }
    } else if (event.key === "Escape") {
      utils.closeDropdown(deleteInput, resultsList);
    }
  });

  deleteBtn?.addEventListener("click", async () => {
    const word = deleteInput?.value.trim();
    if (!word) {
      utils.setStatus(deleteStatus, "Type a word first.", "err");
      return;
    }

    try {
      const res = await fetch(`/delete?word=${encodeURIComponent(word)}`, {
        method: "DELETE",
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        utils.setStatus(deleteStatus, data.message || `Deleted "${word}".`, "ok");
        deleteInput.value = "";
      } else {
        utils.setStatus(deleteStatus, data.detail || `Could not delete "${word}".`, "err");
      }
    } catch (error) {
      utils.setStatus(deleteStatus, "Error: Unprocessable content", "err");
    }
  });
}
