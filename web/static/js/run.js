/* Run tab: configuration, start/stop, live log with level colours, status pill. Backed by /api/run*, /api/flows, /api/cases. */
(function () {
  const { $, esc, api, toast, setStatus, onTab } = window.Nitros;
  let pollTimer = null;
  let running = false;
  let lastLogLength = -1;

  function levelOf(line) {
    if (/\[ERROR\]|\[FAILED\]|FAILED|Traceback|Error/.test(line)) return "error";
    if (/\[WARN\]|WARN|retrying|not saved/.test(line)) return "warn";
    if (/^=== |^Flow |Finished|Loaded|First session|Existing Chrome/.test(line)) return "head";
    if (/^\s*OK$|matched with|= |security warning page passed/.test(line)) return "ok";
    return "muted";
  }

  function renderLog(text) {
    const box = $("run-log");
    if (!text) { box.innerHTML = '<div class="empty"><span>No output yet.</span></div>'; return; }
    box.innerHTML = text.split("\n").filter((l) => l.length).map((l) =>
      `<div class="log-line lvl-${levelOf(l)}">${esc(l)}</div>`).join("");
    if ($("run-autoscroll").checked) box.scrollTop = box.scrollHeight;
  }

  async function loadPickers() {
    try {
      const d = await api("/api/flows");
      const opts = d.flows.map((f) => `<option>${esc(f.name)}</option>`).join("");
      const prevSetup = $("run-setup").value;
      const prevCase = $("run-case").value;
      $("run-setup").innerHTML = `<option value="">(none)</option>${opts}`;
      $("run-case").innerHTML = opts;
      if (prevSetup) $("run-setup").value = prevSetup;
      if (prevCase) $("run-case").value = prevCase;
    } catch (e) { toast(e.message, "error"); }
    try {
      const c = await api("/api/cases");
      $("run-cases").textContent = `${c.count} case${c.count === 1 ? "" : "s"} queued`;
      $("run-cases-hint").textContent = c.path;
    } catch (e) {
      $("run-cases").textContent = "Cases.xlsx unavailable";
      $("run-cases-hint").textContent = e.message;
    }
    const setup = await api("/api/setup").catch(() => null);
    $("run-summary").textContent = setup && setup.config && setup.config.crm_url
      ? "Chrome opens to CRM, runs the setup flow once, then the case flow for each case."
      : "Set the CRM address in Setup before running.";
  }

  function setButtons(isRunning) {
    running = isRunning;
    $("run-start").disabled = isRunning;
    $("run-stop").disabled = !isRunning;
    $("run-setup").disabled = isRunning;
    $("run-case").disabled = isRunning;
  }

  async function poll() {
    let d;
    try { d = await api("/api/run/status"); } catch (e) { return; }
    renderLog(d.log);
    const st = d.status || {};
    const total = st.total || 0;
    const index = st.index || 0;
    const pct = total ? Math.round(((st.state === "finished" ? total : Math.max(index - 1, 0)) / total) * 100) : 0;
    $("run-progress").style.width = pct + "%";
    if (d.running) {
      setButtons(true);
      setStatus("running", "Running");
      $("run-progress-text").textContent = `Case ${index} of ${total}${st.case ? " · " + st.case : ""}${st.failed ? ` · ${st.failed} failed` : ""}`;
    } else {
      setButtons(false);
      clearInterval(pollTimer);
      pollTimer = null;
      const state = st.state || "idle";
      if (state === "finished") {
        const ok = st.failed === 0;
        setStatus(ok ? "success" : "failed", ok ? "Success" : `${st.failed} failed`);
        $("run-progress-text").textContent = `Finished · ${total - (st.failed || 0)} of ${total} succeeded`;
      } else if (state === "error") {
        setStatus("failed", "Failed");
        $("run-progress-text").textContent = st.message || "Run stopped with an error";
      } else {
        setStatus("idle", "Idle");
        $("run-progress-text").textContent = "Not started";
      }
    }
  }

  function startPolling() {
    clearInterval(pollTimer);
    pollTimer = setInterval(poll, 1500);
    poll();
  }

  async function start() {
    try {
      await api("/api/run", { method: "POST", body: { setup_flow: $("run-setup").value, case_flow: $("run-case").value } });
      toast("Run started");
      setButtons(true);
      setStatus("running", "Running");
      startPolling();
    } catch (e) { toast(e.message, "error"); }
  }

  async function stop() {
    try {
      await api("/api/stop", { method: "POST" });
      toast("Stopping run");
    } catch (e) { toast(e.message, "error"); }
  }

  $("run-start").addEventListener("click", start);
  $("run-stop").addEventListener("click", stop);

  onTab("run", async () => {
    await loadPickers();
    startPolling();
  });
  // Keep the status pill accurate even before the Run tab is opened
  poll();
  setInterval(() => { if (!running) poll(); }, 5000);
})();
