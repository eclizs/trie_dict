export function setStatus(el, message, kind) {
  if (!el) return;

  el.textContent = message;
  el.className = `status-msg ${kind}`;
}

export function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

export function updateHighlight(items, highlightedIndex) {
  items.forEach((item, index) => {
    item.classList.toggle("is-highlighted", index === highlightedIndex);
  });

  if (items[highlightedIndex]) {
    items[highlightedIndex].scrollIntoView({ block: "nearest" });
  }
}

export function openDropdown(input, list) {
  list.classList.add("is-open");
  input.setAttribute("aria-expanded", "true");
}

export function closeDropdown(input, list) {
  list.classList.remove("is-open");
  input.setAttribute("aria-expanded", "false");
}

export function renderMessage(message, input, list) {
  list.innerHTML = `<li class="entry-item is-empty">${escapeHtml(message)}</li>`;
  openDropdown(input, list);
}

export function renderResults(words, list, input, onSelect) {
  if (words.length === 0) {
    renderMessage("No matches found.", input, list);
    return;
  }

  list.innerHTML = words
    .map((word) => `
      <li class="entry-item" data-word="${escapeHtml(word)}" role="option">
        <div class="entry-word">${escapeHtml(word)}</div>
      </li>
    `)
    .join("");

  list.querySelectorAll(".entry-item").forEach((item) => {
    item.addEventListener("click", () => {onSelect(item.dataset.word); input.focus()});
  });

  openDropdown(input, list);
}

export async function runSearch(prefix, list, input, onSelect) {
  const searchTerm = prefix || "";

  try {
    const res = await fetch(`/search?prefix=${encodeURIComponent(searchTerm)}`);
    if (!res.ok) throw new Error(`Search failed (${res.status})`);
    const data = await res.json();
    renderResults(data.words || [], list, input, onSelect);
  } catch (error) {
    renderMessage("No matches found", input, list);
  }
}

export function selectWord(word, numberInput, savedList) {
  const count = numberInput.value ? `${numberInput.value} ` : "";
  const curr = savedList.value;
  savedList.value = curr ? `${curr}\n${count}${word}` : `${count}${word}`;
}