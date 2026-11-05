/* Flows tab: flow cards, step list with touch reorder, step editor in a bottom sheet.
   Backed by /api/flows (GET/PUT), /api/templates and /api/locators for the pickers. */
(function () {
  const { $, esc, api, toast, sheet, confirmSheet, onTab } = window.Nitros;
  let flows = [];
  let operations = [];
  let locatorNames = [];
  let templateNames = [];
  let selected = -1;
  let dirty = false;
  let loaded = false;

  const OP_LABEL = {};
  function opLabel(v) { return OP_LABEL[v] || v; }

  async function load() {
    try {
      const [f, l, t] = await Promise.all([
        api("/api/flows"),
        api("/api/locators").catch(() => ({ rows: [] })),
        api("/api/templates").catch(() => ({ names: [] })),
      ]);
      flows = f.flows;
      operations = f.operations;
      operations.forEach(([v, l2]) => { OP_LABEL[v] = l2; });
      locatorNames = l.rows.map((r) => r.Name);
      templateNames = t.names;
      loaded = true;
      dirty = false;
      refreshSave();
      render();
    } catch (e) { toast(e.message, "error"); }
  }

  function refreshSave() { $("flows-save").disabled = !dirty; }
  function markDirty() { dirty = true; refreshSave(); }

  function renderList() {
    const list = $("flow-list");
    $("flow-count").textContent = loaded ? `${flows.length} flow${flows.length === 1 ? "" : "s"}` : "";
    if (!loaded) { list.innerHTML = '<div class="card"><div class="skeleton wide"></div><div class="skeleton"></div></div>'; return; }
    if (!flows.length) { list.innerHTML = '<div class="card empty"><span>No flows yet.</span><span>Create one to start building steps.</span></div>'; return; }
    list.innerHTML = flows.map((f, i) => {
      const n = f.steps.length;
      const status = n ? "ready" : "empty";
      return `<button type="button" class="item ${i === selected ? "" : ""}" data-flow="${i}" aria-current="${i === selected ? "true" : "false"}"
          style="${i === selected ? "border-color:rgba(124,156,255,.45)" : ""}">
        <span class="item-main">
          <span class="item-title">${esc(f.name)}</span>
          <span class="item-meta"><span class="pill pill-muted">${esc(f.category || "Uncategorised")}</span>
            <span class="pill ${n ? "pill-ok" : "pill-warn"}">${n} step${n === 1 ? "" : "s"}</span>
            ${status === "empty" ? '<span class="pill pill-warn">Needs steps</span>' : ""}</span>
        </span>
        <svg class="icon chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>
      </button>`;
    }).join("");
  }

  function renderEditor() {
    const f = flows[selected];
    $("flow-editor").hidden = !f;
    if (!f) return;
    $("fe-name").textContent = f.name;
    $("fe-cat").textContent = f.category || "Uncategorised";
    $("fe-status").textContent = f.steps.length ? `${f.steps.length} steps` : "Needs steps";
    $("fe-status").className = "pill " + (f.steps.length ? "pill-ok" : "pill-warn");
    const steps = $("fe-steps");
    if (!f.steps.length) {
      steps.innerHTML = '<div class="card empty"><span>No steps yet.</span><span>Add a step to start this flow.</span></div>';
      return;
    }
    steps.innerHTML = f.steps.map((s, i) => `
      <div class="item" data-step="${i}">
        <div class="step-move">
          <button type="button" class="icon-btn" data-move="up" data-i="${i}" aria-label="Move step ${i + 1} up" ${i === 0 ? "disabled" : ""}>
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m6 15 6-6 6 6"/></svg></button>
          <button type="button" class="icon-btn" data-move="down" data-i="${i}" aria-label="Move step ${i + 1} down" ${i === f.steps.length - 1 ? "disabled" : ""}>
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></button>
        </div>
        <button type="button" class="step-row item-main" data-edit="${i}" style="background:none;border:0;padding:0;text-align:left;color:inherit;cursor:pointer;min-width:0">
          <span class="step-num">${i + 1}</span>
          <span style="min-width:0;flex:1;display:grid;gap:4px">
            <span class="item-title">${esc(s.label || s.item || opLabel(s.operation))}</span>
            <span class="item-meta"><span class="pill pill-muted">${esc(opLabel(s.operation))}</span>
              ${s.item ? `<span class="item-value">${esc(s.item)}</span>` : ""}
              ${s.template ? `<span class="pill">${esc(s.template)}</span>` : ""}
              ${s.wait ? `<span class="pill pill-muted">${esc(s.wait)}s</span>` : ""}</span>
          </span>
        </button>
        <button type="button" class="icon-btn danger" data-remove="${i}" aria-label="Delete step ${i + 1}">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg></button>
      </div>`).join("");
  }

  function render() {
    renderList();
    renderEditor();
  }

  function select(i) {
    selected = i;
    render();
    const el = $("flow-editor");
    if (!el.hidden && window.innerWidth < 720) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function options(list, val, blank) {
    return (blank ? `<option value="">${blank}</option>` : "") + list.map((v) => `<option ${v === val ? "selected" : ""}>${esc(v)}</option>`).join("");
  }

  function stepSheet(index) {
    const f = flows[selected];
    const isNew = index === null;
    const s = isNew ? { label: "", item: "", operation: "click", value: "", template: "", wait: 1 } : f.steps[index];
    const body = document.createElement("div");
    body.innerHTML = `
      <div class="field"><label for="se-label">Label</label>
        <div class="control"><input id="se-label" value="${esc(s.label)}" placeholder="What this step does"></div></div>
      <div class="field"><label for="se-op">Operation</label>
        <div class="control"><select id="se-op" class="select" style="border:0;background:transparent;min-height:32px;padding:0">${operations.map(([v, l]) => `<option value="${v}" ${v === s.operation ? "selected" : ""}>${esc(l)}</option>`).join("")}</select></div></div>
      <div class="field"><label for="se-item">Item (locator name)</label>
        <div class="control"><input id="se-item" class="mono" list="se-items" value="${esc(s.item)}" autocomplete="off"><datalist id="se-items">${locatorNames.map((n) => `<option value="${esc(n)}">`).join("")}</datalist></div></div>
      <div class="field" id="se-value-wrap"><label for="se-value">Value</label>
        <div class="control"><input id="se-value" class="mono" value="${esc(s.value)}" placeholder="{case_number} or a literal" autocomplete="off"></div>
        <div class="hint">Used when no template is chosen. Scrape operations take a variable name here.</div></div>
      <div class="field" id="se-flow-wrap" hidden><label for="se-flow">Flow to run</label>
        <div class="control"><select id="se-flow" class="select" style="border:0;background:transparent;min-height:32px;padding:0">${options(flows.map((x) => x.name), s.operation === "run_flow" ? s.value : "", "(choose a flow)")}</select></div>
        <div class="hint">Its steps run here, in order, then this flow continues.</div></div>
      <div class="field"><label for="se-tpl">Template</label>
        <div class="control"><select id="se-tpl" class="select" style="border:0;background:transparent;min-height:32px;padding:0">${options(templateNames, s.template, "(none)")}</select></div>
        <div class="hint">When set, the template text is typed instead of Value.</div></div>
      <div class="field"><label for="se-wait">Wait after step (seconds)</label>
        <div class="control"><input id="se-wait" type="number" min="0" step="0.5" value="${esc(s.wait ?? 0)}" inputmode="decimal"></div>
        <div class="hint">For login checks, this is the timeout instead.</div></div>`;
    const foot = document.createElement("div");
    foot.innerHTML = `${isNew ? "" : '<button type="button" class="btn btn-danger" id="se-delete">Delete</button><span class="spacer"></span>'}
      <button type="button" class="btn" data-close>Cancel</button>
      <button type="button" class="btn btn-primary" id="se-save">${isNew ? "Add step" : "Save step"}</button>`;
    const sh = sheet({ title: isNew ? "New step" : `Step ${index + 1}`, body, foot });
    const opSel = sh.el.querySelector("#se-op");
    const syncFlowField = () => {
      const isSub = opSel.value === "run_flow";
      sh.el.querySelector("#se-flow-wrap").hidden = !isSub;
      sh.el.querySelector("#se-value-wrap").hidden = isSub;
      sh.el.querySelector("#se-item").closest(".field").hidden = isSub;
      sh.el.querySelector("#se-tpl").closest(".field").hidden = isSub;
    };
    opSel.addEventListener("change", syncFlowField);
    syncFlowField();
    sh.el.querySelector("#se-save").addEventListener("click", () => {
      const isSub = opSel.value === "run_flow";
      const next = {
        label: sh.el.querySelector("#se-label").value.trim(),
        operation: opSel.value,
        item: isSub ? "" : sh.el.querySelector("#se-item").value.trim(),
        value: isSub ? sh.el.querySelector("#se-flow").value : sh.el.querySelector("#se-value").value,
        template: isSub ? "" : sh.el.querySelector("#se-tpl").value,
        wait: parseFloat(sh.el.querySelector("#se-wait").value) || 0,
      };
      if (isSub && !next.value) { toast("Choose the flow to run", "error"); return; }
      if (isNew) f.steps.push(next); else f.steps[index] = next;
      markDirty();
      sh.close();
      render();
      toast(isNew ? "Step added" : "Step saved");
    });
    const del = sh.el.querySelector("#se-delete");
    if (del) del.addEventListener("click", () => {
      f.steps.splice(index, 1);
      markDirty();
      sh.close();
      render();
      toast("Step deleted");
    });
  }

  function move(i, dir) {
    const steps = flows[selected].steps;
    const j = i + dir;
    if (j < 0 || j >= steps.length) return;
    [steps[i], steps[j]] = [steps[j], steps[i]];
    markDirty();
    renderEditor();
    const btn = document.querySelector(`[data-move="${dir < 0 ? "up" : "down"}"][data-i="${j}"]`);
    if (btn) btn.focus();
  }

  function flowSheet(index) {
    const isNew = index === null;
    const f = isNew ? { name: "", category: "" } : flows[index];
    const body = document.createElement("div");
    body.innerHTML = `
      <div class="field"><label for="fl-name">Flow name</label>
        <div class="control"><input id="fl-name" value="${esc(f.name)}" autocomplete="off"></div></div>
      <div class="field"><label for="fl-cat">Category</label>
        <div class="control"><input id="fl-cat" value="${esc(f.category)}" list="fl-cats" autocomplete="off">
          <datalist id="fl-cats">${[...new Set(flows.map((x) => x.category).filter(Boolean))].map((c) => `<option value="${esc(c)}">`).join("")}</datalist></div></div>`;
    const foot = document.createElement("div");
    foot.innerHTML = `<button type="button" class="btn" data-close>Cancel</button><button type="button" class="btn btn-primary" id="fl-save">${isNew ? "Create flow" : "Save"}</button>`;
    const sh = sheet({ title: isNew ? "New flow" : "Edit flow", body, foot });
    sh.el.querySelector("#fl-save").addEventListener("click", () => {
      const name = sh.el.querySelector("#fl-name").value.trim();
      const category = sh.el.querySelector("#fl-cat").value.trim();
      if (!name) { toast("Flow name is required", "error"); return; }
      if (flows.some((x, i) => x.name === name && i !== index)) { toast("A flow with that name exists", "error"); return; }
      if (isNew) { flows.push({ name, category, steps: [] }); selected = flows.length - 1; }
      else { flows[index].name = name; flows[index].category = category; }
      markDirty();
      sh.close();
      render();
    });
  }

  async function saveAll() {
    const btn = $("flows-save");
    btn.disabled = true;
    try {
      await api("/api/flows", { method: "PUT", body: { flows } });
      dirty = false;
      toast("Flows saved");
    } catch (e) {
      toast(e.message, "error");
      btn.disabled = false;
    }
  }

  async function deleteFlow() {
    const f = flows[selected];
    if (!f) return;
    const yes = await confirmSheet("Delete flow", `Delete "${f.name}" and all its steps? Save to make it permanent.`);
    if (!yes) return;
    flows.splice(selected, 1);
    selected = -1;
    markDirty();
    render();
    toast("Flow removed, save to keep the change");
  }

  $("flow-list").addEventListener("click", (e) => {
    const b = e.target.closest("[data-flow]");
    if (b) select(+b.dataset.flow);
  });
  $("fe-steps").addEventListener("click", (e) => {
    const edit = e.target.closest("[data-edit]");
    const rm = e.target.closest("[data-remove]");
    const mv = e.target.closest("[data-move]");
    if (edit) stepSheet(+edit.dataset.edit);
    if (rm) {
      const i = +rm.dataset.remove;
      flows[selected].steps.splice(i, 1);
      markDirty();
      render();
    }
    if (mv) move(+mv.dataset.i, mv.dataset.move === "up" ? -1 : 1);
  });
  $("step-add").addEventListener("click", () => { if (flows[selected]) stepSheet(null); else toast("Select a flow first", "error"); });
  $("flow-new").addEventListener("click", () => flowSheet(null));
  $("flow-edit-meta").addEventListener("click", () => { if (flows[selected]) flowSheet(selected); });
  $("flow-delete").addEventListener("click", deleteFlow);
  $("flows-save").addEventListener("click", saveAll);

  render();
  onTab("flows", load);
})();
