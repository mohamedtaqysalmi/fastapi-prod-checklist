(() => {
  const items = window.CHECKLIST_ITEMS || [];
  const list = document.getElementById("checklist");
  const filters = document.getElementById("filters");
  const progress = document.getElementById("progress");
  const storageKey = "fpc-checklist-v2";
  const categories = ["all", "runtime", "security", "observability", "ops"];

  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
  } catch {
    saved = {};
  }
  let active = "all";

  function persist() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(saved));
    } catch {
      // Storage can be blocked. The checklist still works for this visit.
    }
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function updateProgress() {
    const done = items.filter((item) => saved[item.id]).length;
    progress.textContent = `${done} / ${items.length} checked`;
  }

  function buildItem(item) {
    const row = element("li", "check-item");
    row.dataset.category = item.category;

    const box = element("input");
    box.type = "checkbox";
    box.id = `check-${item.id}`;
    box.checked = Boolean(saved[item.id]);
    box.setAttribute("aria-label", `Mark as done: ${item.title}`);
    box.addEventListener("change", () => {
      saved[item.id] = box.checked;
      persist();
      updateProgress();
    });

    const details = element("details");
    const summary = element("summary", "", item.title);
    summary.append(element("span", "meta", `${item.category} · ${item.test}`));

    const body = element("div", "detail");
    body.append(
      element("h3", "", "Why"),
      element("p", "", item.why),
      element("h3", "", "How to verify"),
      element("p", "", item.verify),
    );
    details.append(summary, body);
    row.append(box, details);
    return row;
  }

  function applyFilter() {
    for (const row of list.children) {
      row.hidden = !(active === "all" || row.dataset.category === active);
    }
    for (const button of filters.querySelectorAll("button")) {
      button.setAttribute("aria-pressed", String(button.dataset.value === active));
    }
  }

  function setAllOpen(open) {
    for (const row of list.children) {
      row.querySelector("details").open = open;
    }
  }

  for (const category of categories) {
    const chip = element("button", "chip", category === "all" ? "All" : category);
    chip.type = "button";
    chip.dataset.value = category;
    chip.addEventListener("click", () => {
      active = category;
      applyFilter();
    });
    filters.append(chip);
  }
  document.getElementById("expand-all").addEventListener("click", () => setAllOpen(true));
  document.getElementById("collapse-all").addEventListener("click", () => setAllOpen(false));

  for (const item of items) list.append(buildItem(item));
  applyFilter();
  updateProgress();
})();
