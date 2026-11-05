/* Templates tab: card list, full-screen editor on mobile (dialog on 720px+). Backed by /api/templates. */
(function () {
  const { $, esc, api, toast, sheet, confirmSheet, onTab } = window.Nitros;
  let names = [];
  let loaded = false;

  // Highlight {placeholders} as monospace chips inside the preview
  function chips(text) {
    return esc(text).replace(/\{([A-Za-z0-9_]+)\}/g, '<span class="chip">{$1}</span>');
  }

  async function load() {
    try {
      const d = await api("/api/templates");
      names = d.names;
    } catch (e) {
      toast(e.message, "error");
    }
    loaded = true;
    render();
  }

  function render() {
    const list = $("tpl-list");
    $("tpl-count").textContent = loaded ? `${names.length} template${names.length === 1 ? "" : "s"}` : "";
    if (!loaded) {
      list.innerHTML = '<div class="card"><div class="skeleton wide"></div><div class="skeleton"></div></div>';
      return;
    }
    if (!names.length) {
      list.innerHTML = '<div class="card empty"><span>No templates yet.</span><span>Create one to use in a flow step.</span></div>';
      return;
    }
    list.innerHTML = names.map((n) => `
      <button type="button" class="item" data-name="${esc(n)}">
        <span class="item-main">
          <span class="item-title">${esc(n)}</span>
          <span class="item-sub" data-preview="${esc(n)}">Loading preview</span>
        </span>
        <svg class="icon chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>
      </button>`).join("");
    names.forEach(loadPreview);
  }

  async function loadPreview(name) {
    try {
      const { text } = await api("/api/templates/" + encodeURIComponent(name));
      const el = document.querySelector(`[data-preview="${CSS.escape(name)}"]`);
      if (el) el.textContent = text.replace(/\s+/g, " ").slice(0, 120);
      const found = text.match(/\{[A-Za-z0-9_]+\}/g);
      if (found && el) el.insertAdjacentHTML("afterend", `<span class="chips" style="margin-top:4px">${[...new Set(found)].map((p) => `<span class="chip">${esc(p)}</span>`).join("")}</span>`);
    } catch (e) { /* preview is optional */ }
  }

  function editor(name, text) {
    const isNew = !name;
    const body = document.createElement("div");
    body.innerHTML = `
      <div class="field"><label for="te-name">Name <span class="muted" style="font-size:11.5px">letters, numbers, spaces, _ and -</span></label>
        <div class="control"><input id="te-name" value="${esc(name || "")}" autocomplete="off"></div></div>
      <div class="field"><label for="te-text">Text</label>
        <div class="control"><textarea id="te-text" class="mono" rows="12" style="min-height:260px;resize:vertical;font-size:16px;line-height:1.5">${esc(text || "")}</textarea></div>
        <div class="hint">Placeholders: <span class="chips" style="display:inline-flex;vertical-align:middle">${["{CX_name}", "{case_number}", "{agent_name}", "{notes}"].map((p) => `<span class="chip">${p}</span>`).join("")}</span></div>
      </div>
      <div class="sheet-section" id="te-preview-wrap" style="padding-top:12px">
        <div class="section-label" style="padding:0 0 6px">Preview</div>
        <div class="muted" id="te-preview" style="white-space:pre-wrap;font-size:14px"></div>
      </div>`;
    const foot = document.createElement("div");
    foot.innerHTML = `${isNew ? "" : '<button type="button" class="btn btn-danger" id="te-delete">Delete</button><span class="spacer"></span>'}
      <button type="button" class="btn" data-close>Cancel</button>
      <button type="button" class="btn btn-primary" id="te-save">Save template</button>`;
    const s = sheet({ title: isNew ? "New template" : "Edit template", body, foot, full: true });
    const ta = s.el.querySelector("#te-text");
    const preview = s.el.querySelector("#te-preview");
    const updatePreview = () => { preview.innerHTML = chips(ta.value); };
    ta.addEventListener("input", updatePreview);
    updatePreview();

    s.el.querySelector("#te-save").addEventListener("click", async (e) => {
      const newName = s.el.querySelector("#te-name").value.trim();
      e.currentTarget.disabled = true;
      try {
        await api("/api/templates/" + encodeURIComponent(newName), { method: "PUT", body: { text: ta.value } });
        if (!isNew && newName !== name) await api("/api/templates/" + encodeURIComponent(name), { method: "DELETE" });
        s.close();
        toast("Template saved");
        await load();
      } catch (err) {
        toast(err.message, "error");
        e.currentTarget.disabled = false;
      }
    });
    const del = s.el.querySelector("#te-delete");
    if (del) del.addEventListener("click", async () => {
      const yes = await confirmSheet("Delete template", `Delete "${name}"? Steps that use it will stop working.`);
      if (!yes) return;
      await api("/api/templates/" + encodeURIComponent(name), { method: "DELETE" });
      s.close();
      toast("Template deleted");
      load();
    });
  }

  async function open(name) {
    try {
      const { text } = await api("/api/templates/" + encodeURIComponent(name));
      editor(name, text);
    } catch (err) { toast(err.message, "error"); }
  }

  $("tpl-list").addEventListener("click", (e) => {
    const b = e.target.closest("[data-name]");
    if (b) open(b.dataset.name);
  });
  $("tpl-new").addEventListener("click", () => editor(null, ""));

  onTab("templates", load);
})();
