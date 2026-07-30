import { escapeHtml } from "./utils.js";
import { setStatus } from "./utils.js";

export function initSearch() {
  const searchInput = document.getElementById("search-input");
  const numberInput = document.getElementById("number-input");
  const headerInput = document.getElementById("header-input");
  const resultsList = document.getElementById("results-list");
  const searchBox = document.querySelector(".search-box");
  const clearBtn = document.getElementById("clearBtn");
  const copyBtn = document.getElementById("copyBtn");
  const saveBtn = document.getElementById("saveBtn");
  const headerBtn = document.getElementById("headerBtn");
  const savedList = document.getElementById("saved-list");
  const headerText = document.getElementById("header-text");

  let debounceTimer;
  let highlightedIndex = -1;
  let count = "";
  let header;

  function updateHighlight(items) {
    items.forEach((item, index) => {
      item.classList.toggle("is-highlighted", index === highlightedIndex);
    });

    if (items[highlightedIndex]) {
      items[highlightedIndex].scrollIntoView({ block: "nearest" });
    }
  }

  function openDropdown() {
    resultsList.classList.add("is-open");
    searchInput.setAttribute("aria-expanded", "true");
  }
  
  function closeDropdown() {
    resultsList.classList.remove("is-open");
    searchInput.setAttribute("aria-expanded", "false");
    highlightedIndex = -1;
  }

  function renderMessage(message) {
    highlightedIndex = -1;
    resultsList.innerHTML = `<li class="entry-item is-empty">${escapeHtml(message)}</li>`;
    openDropdown();
  }

  function renderResults(words) {
    if (words.length === 0) {
      renderMessage("No matches found.");
      return;
    }

    highlightedIndex = -1;
    resultsList.innerHTML = words
      .map((word) => `
        <li class="entry-item" data-word="${escapeHtml(word)}" role="option">
          <div class="entry-word">${escapeHtml(word)}</div>
        </li>
      `)
      .join("");

    resultsList.querySelectorAll(".entry-item").forEach((item) => {
      item.addEventListener("click", () => selectWord(count + item.dataset.word));
    });

    openDropdown();
  }

  async function runSearch(prefix) {
    const searchTerm = prefix || "";

    try {
      const res = await fetch(`/search?prefix=${encodeURIComponent(searchTerm)}`);
      if (!res.ok) throw new Error(`Search failed (${res.status})`);
      const data = await res.json();
      renderResults(data.words || []);
    } catch (error) {
      renderMessage("No matches found");
    }
  }

  function selectWord(word) {
    const count = numberInput.value ? `${numberInput.value} ` : "";
    const curr = savedList.value;
    savedList.value = curr ? `${curr}\n${count}${word}` : `${count}${word}`;
  }

  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);

    const raw = searchInput.value.trim();

    let prefix = raw;

    debounceTimer = setTimeout(() => runSearch(prefix), 200);
  });

  searchInput.addEventListener("keydown", (event) => {
    const items = resultsList.querySelectorAll(".entry-item:not(.is-empty)");
    if (!resultsList.classList.contains("is-open") || items.length === 0)
    {
      if(searchInput.value === "") return;
      else if(event.key === "Enter") {
        selectWord(searchInput.value);
        numberInput.focus();
      }
    }

    if (event.key === "ArrowDown" || (event.key === "Tab" && !event.shiftKey)) {
      event.preventDefault();
      highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
      updateHighlight(items);
    } else if (event.key === "ArrowUp" || (event.key === "Tab" && event.shiftKey)) {
      event.preventDefault();
      highlightedIndex = Math.max(highlightedIndex - 1, 0);
      updateHighlight(items);
    } else if (event.key === "Enter") {
      if (highlightedIndex >= 0 && items[highlightedIndex]) {
        event.preventDefault();
        selectWord(count + items[highlightedIndex].dataset.word);
      }
      numberInput.focus();
    } else if (event.key === "Escape") {
      closeDropdown();
      numberInput.focus();
    }
  });
  
  numberInput.addEventListener("keydown", (event) => {
    if(event.key === "Enter" || event.key === " ")
    {
      event.preventDefault();
      searchInput.focus();
    }
  });

  document.addEventListener("click", (event) => {
    if (!searchBox.contains(event.target)) {
      closeDropdown();
    }
  });

  headerBtn?.addEventListener("click", () => {
    header = headerInput.value.trim();
    if (header === "") return;
    headerText.textContent = header;
    headerInput.value = "";
  });

  clearBtn?.addEventListener("click", () => {
    navigator.clipboard.writeText(savedList.value);
    savedList.value = "";
    searchInput.focus();  
  });

  saveBtn?.addEventListener("click", () => {
    const text = (header ? (header + '\n') : "") + savedList.value;
    if (text === "") {
      setStatus(document.getElementById("save-status"), "Nothing to save!", "err");
      return;
    }

    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.setAttribute("download", header || "saved-words.txt");
    anchor.href = url;
    anchor.click();
    URL.revokeObjectURL(url);
  });

  copyBtn?.addEventListener("click", () => {
    const text = (header ? (header + '\n') : "") + savedList.value;
    navigator.clipboard.writeText(text);
  });
}
