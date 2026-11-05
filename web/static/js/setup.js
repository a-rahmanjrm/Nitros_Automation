/* Setup tab: credentials, workbook paths, endpoints, Chrome profile. */
(function () {
  const { $, api, toast, onTab, dirtyTracker } = window.Nitros;
  const FIELDS = ["genesys_user", "agent_name", "locators_path", "cases_path", "crm_url", "dialer_url", "chrome_user_data_dir", "chrome_profile_dir"];
  const form = $("setup-form");
  const save = $("setup-save");
  const discard = $("setup-discard");
  const tracker = dirtyTracker();
  let saved = {};

  // Snapshot of every visible field, excluding the password (it is never loaded back)
  function snapshot() {
    const o = {};
    FIELDS.forEach((f) => o[f] = $(f).value);
    o.genesys_place = $("genesys_place").value;
    o.genesys_password = $("genesys_password").value;
    return JSON.stringify(o);
  }
  function refreshDirty() {
    const dirty = tracker.isDirty(snapshot());
    save.disabled = discard.disabled = !dirty;
  }

  async function load() {
    const d = await api("/api/setup");
    const c = d.config;
    FIELDS.forEach((f) => { $(f).value = c[f] || ""; });
    $("genesys_place").value = d.credentials.place || "";
    $("genesys_user").value = d.credentials.user || $("genesys_user").value;
    $("genesys_password").value = "";
    $("genesys_password").placeholder = d.credentials.has_password ? "Leave blank to keep current" : "Not saved yet";
    $("pass-state").hidden = !d.credentials.has_password;
    saved = snapshot();
    tracker.set(saved);
    refreshDirty();
    loadProfileState();
  }

  async function loadProfileState() {
    const el = $("profile-state");
    el.textContent = "";
  }

  form.addEventListener("input", refreshDirty);

  discard.addEventListener("click", () => {
    load();
    toast("Changes discarded");
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {};
    FIELDS.forEach((f) => body[f] = $(f).value);
    body.genesys_place = $("genesys_place").value;
    body.genesys_password = $("genesys_password").value;
    save.disabled = discard.disabled = true;
    save.textContent = "Saving";
    try {
      await api("/api/setup", { method: "POST", body });
      toast("Setup saved");
      await load();
    } catch (err) {
      toast(err.message, "error");
      refreshDirty();
    } finally {
      save.textContent = "Save setup";
    }
  });

  $("toggle-pass").addEventListener("click", (e) => {
    const p = $("genesys_password");
    const show = p.type === "password";
    p.type = show ? "text" : "password";
    e.currentTarget.setAttribute("aria-pressed", String(show));
    e.currentTarget.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });

  onTab("setup", load);
})();
