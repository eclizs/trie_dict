import * as utils from "./utils.js";

export function initSearch() {
  const searchInput = document.getElementById("search-input");
  const numberInput = document.getElementById("number-input");
  const headerInput = document.getElementById("header-input");
  const resultsList = document.getElementById("results-list-search");
  const searchBox = document.querySelector(".search-box");
  const clearBtn = document.getElementById("clearBtn");
  const copyBtn = document.getElementById("copyBtn");
  const saveBtn = document.getElementById("saveBtn");
  const headerBtn = document.getElementById("headerBtn");
  const savedList = document.getElementById("saved-list");
  const headerText = document.getElementById("header-text");

  let debounceTimer;
  let highlightedIndex = -1;
  let header;

  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);

    const raw = searchInput.value.trim();

    let prefix = raw;

    debounceTimer = setTimeout(
      () =>
        utils.runSearch(prefix, resultsList, searchInput, (word) =>
          utils.selectWord(word, numberInput, savedList)
        ),
      200
    );
  });

  searchInput.addEventListener("keydown", (event) => {
    const items = resultsList.querySelectorAll(".entry-item:not(.is-empty)");
    if (!resultsList.classList.contains("is-open") || items.length === 0)
    {
      if(searchInput.value === "") return;
      else if(event.key === "Enter") {
        utils.selectWord(searchInput.value, numberInput, savedList);
        numberInput.focus();
      }
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
        utils.selectWord(count + items[highlightedIndex].dataset.word, numberInput, savedList);
      }
      numberInput.focus();
    } else if (event.key === "Escape") {
      utils.closeDropdown(searchInput, resultsList);
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
      utils.closeDropdown(searchInput, resultsList);
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
