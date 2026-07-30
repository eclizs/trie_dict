import { setStatus } from "./utils.js";

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

  uploadBtn?.addEventListener("click", async () => {
    if (!fileInput?.files?.length) {
      setStatus(addStatus, "Select a file first.", "err");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const res = await fetch("/insert_excel", {
      method: "POST",
      body: formData,
    });

    const data = await res.json().catch(() => ({}));
    const fails = Array.isArray(data.failed)
      ? data.failed.map((item) => item.reason).filter(Boolean)
      : [];

    const statusMsg = `${fails.length} insertion(s) failed:\n${fails.length ? fails.join("\n") : ""}`;
    setStatus(uploadStatus, statusMsg, "err");

    if (!res.ok) {
      alert("Upload failed");
    }
  });

  addBtn?.addEventListener("click", async () => {
    const word = addInput?.value.trim();
    if (!word) {
      setStatus(addStatus, "Type a word first.", "err");
      return;
    }

    try {
      const res = await fetch(`/insert?word=${encodeURIComponent(word)}`, {
        method: "POST",
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setStatus(addStatus, data.message || `Added "${word}".`, "ok");
        addInput.value = "";
      } else {
        setStatus(addStatus, data.detail || `Could not add "${word}".`, "err");
      }
    } catch (error) {
      setStatus(addStatus, "Error: Unprocessable content", "err");
    }
  });

  deleteBtn?.addEventListener("click", async () => {
    const word = deleteInput?.value.trim();
    if (!word) {
      setStatus(deleteStatus, "Type a word first.", "err");
      return;
    }

    try {
      const res = await fetch(`/delete?word=${encodeURIComponent(word)}`, {
        method: "DELETE",
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setStatus(deleteStatus, data.message || `Deleted "${word}".`, "ok");
        deleteInput.value = "";
      } else {
        setStatus(deleteStatus, data.detail || `Could not delete "${word}".`, "err");
      }
    } catch (error) {
      setStatus(deleteStatus, "Error: Unprocessable content", "err");
    }
  });
}
