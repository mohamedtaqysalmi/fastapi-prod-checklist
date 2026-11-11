(() => {
  const root = document.getElementById("checklist-root");
  const filter = document.getElementById("filter");
  const progress = document.getElementById("progress");
  const themeToggle = document.getElementById("theme-toggle");
  const storageKey = "fpc-checklist-v1";
  const themeKey = "fpc-theme";

  const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    themeToggle.textContent = theme === "dark" ? "Light" : "Dark";
    themeToggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    localStorage.setItem(themeKey, theme);
  }

  const preferred =
    localStorage.getItem(themeKey) ||
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  applyTheme(preferred);

  themeToggle.addEventListener("click", () => {
    applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });

  function render() {
    root.innerHTML = "";
    for (const item of window.CHECKLIST_ITEMS) {
      const details = document.createElement("article");
      details.className = "item";
      details.dataset.category = item.category;
      details.dataset.id = item.id;

      const summary = document.createElement("button");
      summary.type = "button";
      summary.className = "item-summary";
      summary.setAttribute("aria-expanded", "false");

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "check";
      checkbox.checked = Boolean(saved[item.id]);
      checkbox.setAttribute("aria-label", `Mark done: ${item.title}`);
      checkbox.addEventListener("click", (event) => event.stopPropagation());
      checkbox.addEventListener("change", () => {
        saved[item.id] = checkbox.checked;
        localStorage.setItem(storageKey, JSON.stringify(saved));
        updateProgress();
      });

      const text = document.createElement("span");
      text.innerHTML = `<strong>${item.title}</strong><div class="item-meta">${item.category} · <code>${item.test}</code></div>`;

      const chevron = document.createElement("span");
      chevron.className = "chevron";
      chevron.setAttribute("aria-hidden", "true");

      summary.append(checkbox, text, chevron);

      const body = document.createElement("div");
      body.className = "item-body";
      body.hidden = true;
      body.innerHTML = `
        <h3>Why</h3>
        <p>${item.why}</p>
        <h3>How to verify</h3>
        <p>${item.verify}</p>
      `;

      summary.addEventListener("click", (event) => {
        if (event.target === checkbox) return;
        const open = details.classList.toggle("open");
        summary.setAttribute("aria-expanded", open ? "true" : "false");
        body.hidden = !open;
      });

      details.append(summary, body);
      root.append(details);
    }
    applyFilter();
    updateProgress();
  }

  function updateProgress() {
    const total = window.CHECKLIST_ITEMS.length;
    const done = window.CHECKLIST_ITEMS.filter((item) => saved[item.id]).length;
    progress.textContent = `${done} / ${total} checked`;
  }

  function applyFilter() {
    const value = filter.value;
    for (const el of root.querySelectorAll(".item")) {
      el.hidden = !(value === "all" || el.dataset.category === value);
    }
  }

  filter.addEventListener("change", applyFilter);

  document.getElementById("expand-all").addEventListener("click", () => {
    for (const el of root.querySelectorAll(".item")) {
      el.classList.add("open");
      el.querySelector(".item-summary").setAttribute("aria-expanded", "true");
      el.querySelector(".item-body").hidden = false;
    }
  });

  document.getElementById("collapse-all").addEventListener("click", () => {
    for (const el of root.querySelectorAll(".item")) {
      el.classList.remove("open");
      el.querySelector(".item-summary").setAttribute("aria-expanded", "false");
      el.querySelector(".item-body").hidden = true;
    }
  });

  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const target = document.getElementById(btn.getAttribute("data-copy"));
      const text = target.innerText;
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = "Copied";
        setTimeout(() => {
          btn.textContent = "Copy";
        }, 1200);
      } catch {
        btn.textContent = "Select & copy";
      }
    });
  });

  render();
})();
