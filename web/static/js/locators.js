/* Locators tab: cards on mobile, table at 720px+, add/edit in a sheet. Backed by /api/locators. */
(function () {
  const { $, esc, api, toast, sheet, confirmSheet, onTab } = window.Nitros;
  const STRATEGIES = ["XPATH", "ID", "CSS_SELECTOR", "NAME", "CLASS_NAME", "TAG_NAME"];
  const MATCHES = ["contains", "starts-with", "exact"];
  let rows = [];
  let loaded = false;

  function filtered() {
    const q = $("loc-search").value.trim().toLowerCase();
    const strat = $("loc-filter").value;
    return rows.filter((r) => {
      if (strat && (r.Strategy || "").toUpperCase() !== strat) return false;
      if (!q) return true;
      return [r.Name, r.Value, r["Full XPath"], r.Notes].some((v) => (v || "").toLowerCase().includes(q));
    });
  }

  function render() {
    const list = filtered();
    $("loc-count").textContent = `${list.length} of ${rows.length} locators`;
    const cards = $("loc-list");
    const table = $("loc-table");

    if (!loaded) {
      cards.innerHTML = '<div class="card"><div class="skeleton wide"></div><div class="skeleton"></div><div class="skeleton short"></div></div>';
      return;
    }
    if (!rows.length) {
      cards.innerHTML = '<div class="card empty"><span>No locators yet.</span><span>Add one, or fill in Locators.xlsx.</span></div>';
      table.innerHTML = "";
      $("loc-table-wrap").hidden = true;
      return;
    }
    if (!list.length) {
      cards.innerHTML = '<div class="card empty"><span>No locator matches this search.</span></div>';
    } else {
      cards.innerHTML = list.map((r) => `
        <div class="item" data-row="${r.row}">
          <div class="item-main">
            <div class="item-title">${esc(r.Name)}</div>
            <div class="item-meta"><span class="pill pill-muted">${esc(r.Strategy || "XPATH")}</span>
              ${r.Match ? `<span class="pill">${esc(r.Match)}</span>` : ""}
              ${r.Attribute ? `<span class="pill pill-muted">${esc(r.Attribute)}</span>` : ""}</div>
            <div class="item-value" title="${esc(r.Value)}">${esc(r.Value || r["Full XPath"] || "-")}</div>
          </div>
          <div class="item-actions">
            <button type="button" class="icon-btn" data-edit="${r.row}" aria-label="Edit ${esc(r.Name)}">${pencil()}</button>
            <button type="button" class="icon-btn danger" data-del="${r.row}" aria-label="Delete ${esc(r.Name)}">${trash()}</button>
          </div>
        </div>`).join("");
    }

    table.innerHTML = list.map((r) => `<tr>
        <td><b>${esc(r.Name)}</b></td>
        <td>${esc(r.Strategy)}</td>
        <td>${esc(r.Match)}</td>
        <td class="mono">${esc(r.Attribute)}</td>
        <td class="mono wrap">${esc(r.Value)}</td>
        <td class="wrap">${esc(r.Notes)}</td>
        <td><span class="item-actions">
          <button type="button" class="icon-btn" data-edit="${r.row}" aria-label="Edit ${esc(r.Name)}">${pencil()}</button>
          <button type="button" class="icon-btn danger" data-del="${r.row}" aria-label="Delete ${esc(r.Name)}">${trash()}</button>
        </span></td></tr>`).join("");
    $("loc-table-wrap").hidden = false;
  }

  function pencil() { return '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16v4Z"/></svg>'; }
  function trash() { return '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>'; }

  async function load() {
    try {
      const d = await api("/api/locators");
      rows = d.rows;
      loaded = true;
    } catch (e) {
      loaded = true;
      rows = [];
      $("loc-list").innerHTML = `<div class="card empty"><b>Could not read Locators.xlsx</b><span>${esc(e.message)}</span></div>`;
      return;
    }
    render();
  }

  function form(data = {}) {
    const wrap = document.createElement("div");
    const opt = (list, val) => list.map((v) => `<option ${v === val ? "selected" : ""}>${v}</option>`).join("");
    wrap.innerHTML = `
      <div class="field"><label for="lf-name">Name</label>
        <div class="control"><input id="lf-name" class="mono" value="${esc(data.Name)}" placeholder="GlobalSearchBox" autocomplete="off"></div></div>
      <div class="field"><label for="lf-strategy">Strategy</label>
        <div class="control"><select id="lf-strategy" class="select" style="border:0;background:transparent;min-height:32px;padding:0">${opt(STRATEGIES, data.Strategy || "XPATH")}</select></div></div>
      <div class="field"><label for="lf-match">Match</label>
        <div class="control"><select id="lf-match" class="select" style="border:0;background:transparent;min-height:32px;padding:0"><option value="">(none yet)</option>${opt(MATCHES, data.Match)}</select></div></div>
      <div class="field"><label for="lf-attr">Attribute</label>
        <div class="control"><input id="lf-attr" class="mono" value="${esc(data.Attribute)}" placeholder="id, text, aria-label, class" autocomplete="off"></div></div>
      <div class="field"><label for="lf-value">Value <span class="muted" style="font-size:11.5px">parts inside contains(), up to 3</span></label>
        <div class="control"><input id="lf-value" class="mono" value="${esc(data.Value)}" placeholder="timeline | highlights | content" autocomplete="off"></div>
        <div class="hint">Separate parts with <span class="mono">|</span>. Each part becomes its own <span class="mono">contains()</span>, joined with <span class="mono">and</span>. Trim dynamic numbers such as <span class="mono">-420</span>.</div></div>
      <div class="field"><label for="lf-full">Full XPath</label>
        <div class="control"><textarea id="lf-full" class="mono" rows="3" style="resize:vertical" placeholder="Paste the XPath from DevTools">${esc(data["Full XPath"])}</textarea></div>
        <div class="row-between" style="margin-top:8px"><span class="hint" style="margin:0">Fill Attribute and Value from the id inside this XPath.</span>
          <button type="button" class="btn" id="lf-fill" style="min-height:36px;padding:0 12px">Fill from Full XPath</button></div></div>
      <div class="field"><span class="muted" style="font-size:12.5px;display:block;margin-bottom:6px">Generated XPath preview</span>
        <div id="lf-preview" class="mono" style="font-size:12.5px;display:grid;gap:8px;word-break:break-all"></div></div>
      <div class="field"><label for="lf-notes">Notes</label>
        <div class="control"><input id="lf-notes" value="${esc(data.Notes)}" autocomplete="off"></div></div>`;
    return wrap;
  }

  // Same rules as core/locators.py build_xpath, so the preview matches what the runner builds
  function xpathLiteral(text) {
    if (!text.includes("'")) return `'${text}'`;
    if (!text.includes('"')) return `"${text}"`;
    return "concat(" + text.split("'").map((p) => `'${p}'`).join(`, "'", `) + ")";
  }
  // Same rules as core/locators.py build_xpath: Value holds up to 3 parts separated by "|"
  function splitParts(value) {
    return value.split("|").map((p) => p.trim()).filter(Boolean).slice(0, 3);
  }
  function buildXPath(attribute, value, match) {
    const parts = splitParts(value);
    if (!parts.length) return null;
    const target = attribute === "text" ? "normalize-space(.)" : `@${attribute || "id"}`;
    const conds = parts.map((part, i) => {
      const lit = xpathLiteral(part);
      if (i === 0 && match === "exact" && parts.length === 1) return `${target}=${lit}`;
      if (i === 0 && match === "starts-with") return `starts-with(${target},${lit})`;
      return `contains(${target},${lit})`;
    });
    const cond = conds.join(" and ");
    // Text also matches the elements wrapping it (toolbar div, body, html...): keep the innermost one
    if (attribute === "text") return `//*[${cond} and not(.//*[${cond}])]`;
    return `//*[${cond}]`;
  }
  // Pull the first id literal out of a pasted XPath: @id='x', contains(@id,'x') or starts-with(@id,'x').
  // Dynamic numeric tails (e.g. "-420" or "_2") are trimmed so the fragment still matches next time.
  function idFromFullXPath(xpath) {
    const m = xpath.match(/@id\s*=\s*(['"])(.*?)\1/) || xpath.match(/(?:contains|starts-with)\(\s*@id\s*,\s*(['"])(.*?)\1/);
    return m ? m[2].replace(/[-_]\d+$/, "") : "";
  }

  function wirePreview(root) {
    const q = (sel) => root.querySelector(sel);
    const out = q("#lf-preview");
    const refresh = () => {
      const attr = q("#lf-attr").value.trim() || "id";
      const value = q("#lf-value").value.trim();
      const chosen = q("#lf-match").value;
      if (!splitParts(value).length) { out.innerHTML = '<span class="muted">Enter a Value to see the XPath.</span>'; return; }
      out.innerHTML = MATCHES.map((m) => `<div style="display:grid;gap:2px">
          <span class="muted" style="font-family:inherit;font-size:12px">${m}${m === chosen ? ' <span class="pill" style="font-size:10.5px;padding:1px 6px">used</span>' : ""}</span>
          <span style="color:${m === chosen ? "var(--text)" : "var(--muted)"}">${esc(buildXPath(attr, value, m))}</span></div>`).join("");
    };
    ["#lf-attr", "#lf-value", "#lf-full"].forEach((sel) => q(sel).addEventListener("input", refresh));
    q("#lf-match").addEventListener("change", refresh);
    q("#lf-fill").addEventListener("click", () => {
      const id = idFromFullXPath(q("#lf-full").value);
      if (!id) { toast("No id found in the Full XPath", "error"); return; }
      q("#lf-attr").value = "id";
      // Split the id at its dash/underscore boundaries, so parts can be trimmed in the field
      q("#lf-value").value = id.split(/[-_]/).filter((p) => p && !/^\d+$/.test(p)).slice(0, 3).join(" | ");
      if (!q("#lf-match").value) q("#lf-match").value = "contains";
      refresh();
      toast("Value filled from the Full XPath");
    });
    refresh();
  }

  function collect(root) {
    return {
      Name: root.querySelector("#lf-name").value,
      Strategy: root.querySelector("#lf-strategy").value,
      Match: root.querySelector("#lf-match").value,
      Attribute: root.querySelector("#lf-attr").value,
      Value: root.querySelector("#lf-value").value,
      "Full XPath": root.querySelector("#lf-full").value,
      Notes: root.querySelector("#lf-notes").value,
    };
  }

  function openEditor(existing) {
    const body = form(existing || {});
    const foot = document.createElement("div");
    foot.innerHTML = `<button type="button" class="btn" data-close>Cancel</button><button type="button" class="btn btn-primary" id="lf-save">${existing ? "Save locator" : "Add locator"}</button>`;
    const s = sheet({ title: existing ? "Edit locator" : "Add locator", body, foot, full: false });
    wirePreview(s.body);
    s.el.querySelector("#lf-save").addEventListener("click", async (e) => {
      e.currentTarget.disabled = true;
      try {
        const data = collect(s.body);
        if (existing) await api(`/api/locators/${existing.row}`, { method: "PUT", body: data });
        else await api("/api/locators", { method: "POST", body: data });
        s.close();
        toast(existing ? "Locator updated" : "Locator added");
        await load();
      } catch (err) {
        toast(err.message, "error");
        e.currentTarget.disabled = false;
      }
    });
  }

  async function remove(row) {
    const r = rows.find((x) => x.row === row);
    if (!r) return;
    const yes = await confirmSheet("Delete locator", `Delete "${r.Name}" from Locators.xlsx? Flows that use it will fail until it is re-added.`);
    if (!yes) return;
    try {
      await api(`/api/locators/${row}`, { method: "DELETE" });
      toast("Locator deleted");
      await load();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  function onListClick(e) {
    const edit = e.target.closest("[data-edit]");
    const del = e.target.closest("[data-del]");
    if (edit) { const r = rows.find((x) => x.row === +edit.dataset.edit); if (r) openEditor(r); }
    if (del) remove(+del.dataset.del);
  }
  $("loc-list").addEventListener("click", onListClick);
  $("loc-table").addEventListener("click", onListClick);
  $("loc-search").addEventListener("input", render);
  $("loc-filter").addEventListener("change", render);
  $("loc-add").addEventListener("click", () => openEditor(null));

  render();
  onTab("locators", load);
})();
