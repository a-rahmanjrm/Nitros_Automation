/* Shared helpers: API calls, escaping, toast, bottom sheet, tab routing (URL hash), status pill. */
(function () {
  const TABS = ["setup", "locators", "templates", "flows", "scrape", "run"];
  const listeners = {};

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  async function api(url, opts = {}) {
    const init = { method: opts.method || "GET", headers: {} };
    if (opts.body !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(opts.body);
    }
    const res = await fetch(url, init);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }

  // ----- toast -----
  let toastTimer = null;
  function toast(text, kind = "ok") {
    const el = $("toast");
    $("toast-text").textContent = text;
    el.classList.toggle("error", kind === "error");
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), kind === "error" ? 4200 : 1900);
  }

  // ----- bottom sheet (mobile) / dialog (720px+). Returns a close function. -----
  // opts: { title, body (HTML string or Node), foot (HTML string or Node), full: bool, onClose }
  function sheet(opts) {
    const wrap = document.createElement("div");
    wrap.className = "sheet-wrap";
    wrap.innerHTML = `
      <div class="sheet-backdrop" data-close></div>
      <div class="sheet ${opts.full ? "full" : ""}" role="dialog" aria-modal="true" aria-label="${esc(opts.title)}">
        <div class="sheet-grab" aria-hidden="true"></div>
        <div class="sheet-head"><h2>${esc(opts.title)}</h2>
          <button type="button" class="icon-btn" data-close aria-label="Close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="icon"><path d="M6 6l12 12M18 6 6 18"/></svg>
          </button>
        </div>
        <div class="sheet-body"></div>
        ${opts.foot ? '<div class="sheet-foot"></div>' : ""}
      </div>`;
    const body = wrap.querySelector(".sheet-body");
    if (typeof opts.body === "string") body.innerHTML = opts.body; else if (opts.body) body.appendChild(opts.body);
    if (opts.foot) {
      const foot = wrap.querySelector(".sheet-foot");
      if (typeof opts.foot === "string") foot.innerHTML = opts.foot; else foot.appendChild(opts.foot);
    }
    const previous = document.activeElement;
    const close = () => {
      document.removeEventListener("keydown", onKey);
      wrap.remove();
      if (previous && previous.focus) previous.focus();
      if (opts.onClose) opts.onClose();
    };
    const onKey = (e) => { if (e.key === "Escape") close(); };
    wrap.addEventListener("click", (e) => { if (e.target.closest("[data-close]")) close(); });
    document.addEventListener("keydown", onKey);
    document.body.appendChild(wrap);
    const first = wrap.querySelector("input, select, textarea, button:not([data-close])") || wrap.querySelector("[data-close]");
    if (first) first.focus();
    return { close, el: wrap, body, foot: wrap.querySelector(".sheet-foot") };
  }

  function confirmSheet(title, message, confirmLabel = "Delete") {
    return new Promise((resolve) => {
      const body = document.createElement("div");
      body.className = "sheet-section";
      body.innerHTML = `<p class="muted">${esc(message)}</p>`;
      const foot = document.createElement("div");
      foot.innerHTML = `<button type="button" class="btn" data-close>Cancel</button>
        <button type="button" class="btn btn-solid-danger" id="confirm-yes">${esc(confirmLabel)}</button>`;
      let answered = false;
      const s = sheet({ title, body, foot, onClose: () => { if (!answered) resolve(false); } });
      s.el.querySelector("#confirm-yes").addEventListener("click", () => { answered = true; s.close(); resolve(true); });
    });
  }

  // ----- dirty tracking for save bars -----
  // Returns { set(snapshotString), isDirty(snapshotString), clean() }
  function dirtyTracker() {
    let baseline = "";
    return {
      set(snapshot) { baseline = snapshot; },
      isDirty(snapshot) { return snapshot !== baseline; },
    };
  }

  // ----- tabs -----
  let current = "setup";
  function showTab(name, { updateHash = true } = {}) {
    if (!TABS.includes(name)) name = "setup";
    current = name;
    document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + name));
    document.querySelectorAll("[data-bar]").forEach((b) => { b.hidden = b.dataset.bar !== name; });
    document.querySelectorAll("[data-tab]").forEach((b) => {
      if (b.dataset.tab === name) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    if (updateHash && location.hash !== "#" + name) history.replaceState(null, "", "#" + name);
    document.title = "Nitros - " + name.charAt(0).toUpperCase() + name.slice(1);
    (listeners[name] || []).forEach((fn) => fn());
    window.scrollTo({ top: 0 });
  }
  function onTab(name, fn) { (listeners[name] = listeners[name] || []).push(fn); }
  function currentTab() { return current; }

  document.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  window.addEventListener("hashchange", () => showTab(location.hash.slice(1), { updateHash: false }));

  // ----- status pill: idle | running | success | failed -----
  function setStatus(state, text) {
    const el = $("app-status");
    el.dataset.state = state;
    $("app-status-text").textContent = text || { idle: "Idle", running: "Running", success: "Success", failed: "Failed" }[state] || state;
  }

  // ----- copy button -----
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-copy]");
    if (!b) return;
    const input = $(b.dataset.copy);
    if (input && navigator.clipboard) navigator.clipboard.writeText(input.value).then(() => toast("Path copied"));
  });

  window.Nitros = { $, esc, api, toast, sheet, confirmSheet, dirtyTracker, showTab, onTab, currentTab, setStatus };

  // Open the tab named in the URL hash (or Setup). Runs after every tab script has registered its listeners.
  document.addEventListener("DOMContentLoaded", () => showTab(location.hash.slice(1), { updateHash: false }));
})();
