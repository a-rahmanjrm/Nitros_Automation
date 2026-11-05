/* Scrape data tab: variable cards, progress and export. Backed by /api/scrape (GET/PUT). */
(function () {
  const { $, esc, api, toast, sheet, confirmSheet, onTab, dirtyTracker } = window.Nitros;
  const TRANSFORMS = [["", "None"], ["title", "Title case"]];
  let items = [];
  let loaded = false;
  let dirty = false;
  let locatorNames = [];

  async function load() {
    try {
      const [d, l] = await Promise.all([api("/api/scrape"), api("/api/locators").catch(() => ({ rows: [] }))]);
      items = d.items;
      locatorNames = l.rows.map((r) => r.Name);
      loaded = true;
      dirty = false;
      $("scrape-save").disabled = true;
      render();
    } catch (e) { toast(e.message, "error"); }
  }

  function render() {
    const list = $("scrape-list");
    const total = items.length;
    const ready = items.filter((i) => i.variable && i.item).length;
    $("scrape-progress-text").textContent = !loaded ? "Loading" : `${ready} of ${total} variables are fully configured`;
    $("scrape-progress").style.width = total ? `${Math.round((ready / total) * 100)}%` : "0";
    if (!loaded) { list.innerHTML = '<div class="card"><div class="skeleton wide"></div><div class="skeleton"></div></div>'; return; }
    if (!items.length) { list.innerHTML = '<div class="card empty"><span>No variables yet.</span><span>Add one to copy a value from the page.</span></div>'; return; }
    list.innerHTML = items.map((s, i) => {
      const ok = s.variable && s.item;
      return `<div class="item" data-i="${i}">
        <div class="item-main">
          <div class="item-title mono" style="font-size:14px">{${esc(s.variable || "unnamed")}}</div>
          <div class="item-meta">
            <span class="pill ${ok ? "pill-ok" : "pill-warn"}">${ok ? "Ready" : "Incomplete"}</span>
            <span class="pill pill-muted">${esc(s.attribute || "text")}</span>
            ${s.transform === "title" ? '<span class="pill pill-muted">Title case</span>' : ""}
          </div>
          <div class="item-sub">From <span class="mono">${esc(s.item || "-")}</span>${s.default ? ` · default "${esc(s.default)}"` : ""}</div>
        </div>
        <button type="button" class="icon-btn" data-edit="${i}" aria-label="Edit ${esc(s.variable || "variable")}">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16v4Z"/></svg></button>
      </div>`;
    }).join("");
  }

  function editor(index) {
    const isNew = index === null;
    const s = isNew ? { variable: "", item: "", attribute: "text", transform: "", default: "" } : items[index];
    const body = document.createElement("div");
    body.innerHTML = `
      <div class="field"><label for="sc-var">Variable name</label>
        <div class="control"><input id="sc-var" class="mono" value="${esc(s.variable)}" placeholder="CX_name" autocomplete="off"></div>
        <div class="hint">Use it in templates as {${esc(s.variable || "CX_name")}}.</div></div>
      <div class="field"><label for="sc-item">Locator name</label>
        <div class="control"><input id="sc-item" class="mono" list="sc-items" value="${esc(s.item)}" autocomplete="off">
          <datalist id="sc-items">${locatorNames.map((n) => `<option value="${esc(n)}">`).join("")}</datalist></div></div>
      <div class="field"><label for="sc-attr">Read from</label>
        <div class="control"><input id="sc-attr" class="mono" value="${esc(s.attribute || "text")}" placeholder="text, aria-label, value" autocomplete="off"></div></div>
      <div class="field"><label for="sc-tr">Transform</label>
        <div class="control"><select id="sc-tr" class="select" style="border:0;background:transparent;min-height:32px;padding:0">${TRANSFORMS.map(([v, l]) => `<option value="${v}" ${v === (s.transform || "") ? "selected" : ""}>${l}</option>`).join("")}</select></div></div>
      <div class="field"><label for="sc-def">Default if empty</label>
        <div class="control"><input id="sc-def" value="${esc(s.default)}" autocomplete="off"></div></div>`;
    const foot = document.createElement("div");
    foot.innerHTML = `${isNew ? "" : '<button type="button" class="btn btn-danger" id="sc-delete">Delete</button><span class="spacer"></span>'}
      <button type="button" class="btn" data-close>Cancel</button>
      <button type="button" class="btn btn-primary" id="sc-save">${isNew ? "Add variable" : "Apply"}</button>`;
    const sh = sheet({ title: isNew ? "New variable" : "Edit variable", body, foot });
    sh.el.querySelector("#sc-save").addEventListener("click", () => {
      const next = {
        variable: sh.el.querySelector("#sc-var").value.trim(),
        item: sh.el.querySelector("#sc-item").value.trim(),
        attribute: sh.el.querySelector("#sc-attr").value.trim() || "text",
        transform: sh.el.querySelector("#sc-tr").value,
        default: sh.el.querySelector("#sc-def").value,
      };
      if (!next.variable) { toast("Variable name is required", "error"); return; }
      if (items.some((x, i) => x.variable === next.variable && i !== index)) { toast("That variable already exists", "error"); return; }
      if (isNew) items.push(next); else items[index] = next;
      dirty = true;
      $("scrape-save").disabled = false;
      sh.close();
      render();
    });
    const del = sh.el.querySelector("#sc-delete");
    if (del) del.addEventListener("click", () => {
      items.splice(index, 1);
      dirty = true;
      $("scrape-save").disabled = false;
      sh.close();
      render();
    });
  }

  async function saveAll() {
    const btn = $("scrape-save");
    btn.disabled = true;
    try {
      await api("/api/scrape", { method: "PUT", body: { items } });
      dirty = false;
      toast("Variables saved");
    } catch (e) {
      toast(e.message, "error");
      btn.disabled = false;
    }
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(items, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "scrape_map.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  $("scrape-list").addEventListener("click", (e) => {
    const b = e.target.closest("[data-edit]");
    if (b) editor(+b.dataset.edit);
  });
  $("scrape-add").addEventListener("click", () => editor(null));
  $("scrape-export").addEventListener("click", exportJson);
  $("scrape-save").addEventListener("click", saveAll);

  render();
  onTab("scrape", load);
})();
