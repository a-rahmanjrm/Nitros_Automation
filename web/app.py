"""Local Flask control panel: set up credentials, locators, templates, flows and scrape data,
then start the automation runner from the Run tab.

    python web/app.py     (opens http://127.0.0.1:5057 in your browser)
"""
import os
import subprocess
import sys
import threading
import webbrowser

from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core import config, credentials, excel_io, flows, templates  # noqa: E402

app = Flask(__name__)
PORT = 5057
_runner_proc = None
_runner_lock = threading.Lock()


def _error(message, code=400):
    return jsonify({"ok": False, "error": message}), code


# ---------- pages ----------

@app.get("/")
def index():
    return render_template("index.html")


# ---------- setup: config + credentials ----------

@app.get("/api/setup")
def get_setup():
    cfg = config.load_config()
    return jsonify({
        "config": cfg,
        "credentials": credentials.describe(),
        "configured": credentials.is_configured(),
    })


@app.post("/api/setup")
def post_setup():
    data = request.get_json(force=True)
    try:
        config.save_config({k: data.get(k, "") for k in config.DEFAULT_CONFIG})
        credentials.save(
            user=(data.get("genesys_user") or "").strip(),
            password=data.get("genesys_password") or "",
            place=(data.get("genesys_place") or "").strip(),
        )
    except Exception as e:  # keyring backend errors
        return _error(f"Could not save: {e}", 500)
    return jsonify({"ok": True})


# ---------- locators (read-only view of Locators.xlsx) ----------

@app.get("/api/locators")
def get_locators():
    cfg = config.load_config()
    try:
        rows = excel_io.read_locators(cfg["locators_path"])
    except (FileNotFoundError, ValueError) as e:
        return _error(str(e))
    return jsonify({"rows": [{**{k: v for k, v in r.items() if k != "_row"}, "row": r["_row"]} for r in rows]})


def _locator_payload(data):
    fields = {f: (data.get(f) or "").strip() for f in excel_io.LOCATOR_FIELDS}
    if not fields["Name"]:
        raise ValueError("Name is required")
    if " " in fields["Name"]:
        raise ValueError("Name cannot contain spaces")
    if fields["Match"] and fields["Match"] not in ("contains", "starts-with", "exact"):
        raise ValueError("Match must be contains, starts-with or exact")
    return fields


def _name_taken(path, name, except_row=None):
    return any(r["Name"] == name and r["_row"] != except_row for r in excel_io.read_locators(path))


@app.post("/api/locators")
def add_locator():
    cfg = config.load_config()
    try:
        fields = _locator_payload(request.get_json(force=True))
        if _name_taken(cfg["locators_path"], fields["Name"]):
            return _error(f"A locator named '{fields['Name']}' already exists")
        row = excel_io.write_locator(cfg["locators_path"], None, fields)
    except PermissionError:
        return _error("Locators.xlsx is open in Excel. Close it and try again.", 423)
    except (ValueError, FileNotFoundError) as e:
        return _error(str(e))
    return jsonify({"ok": True, "row": row})


@app.put("/api/locators/<int:row>")
def update_locator(row):
    cfg = config.load_config()
    try:
        fields = _locator_payload(request.get_json(force=True))
        if _name_taken(cfg["locators_path"], fields["Name"], except_row=row):
            return _error(f"A locator named '{fields['Name']}' already exists")
        excel_io.write_locator(cfg["locators_path"], row, fields)
    except PermissionError:
        return _error("Locators.xlsx is open in Excel. Close it and try again.", 423)
    except (ValueError, FileNotFoundError) as e:
        return _error(str(e))
    return jsonify({"ok": True})


@app.delete("/api/locators/<int:row>")
def delete_locator(row):
    cfg = config.load_config()
    try:
        excel_io.delete_locator(cfg["locators_path"], row)
    except PermissionError:
        return _error("Locators.xlsx is open in Excel. Close it and try again.", 423)
    except FileNotFoundError as e:
        return _error(str(e))
    return jsonify({"ok": True})


@app.get("/api/cases")
def get_cases():
    cfg = config.load_config()
    try:
        cases = excel_io.read_cases(cfg["cases_path"])
    except (FileNotFoundError, ValueError) as e:
        return _error(str(e))
    return jsonify({"count": len(cases), "path": cfg["cases_path"]})


# ---------- templates ----------

@app.get("/api/templates")
def list_templates():
    return jsonify({"names": templates.list_templates()})


@app.get("/api/templates/<name>")
def get_template(name):
    try:
        return jsonify({"name": name, "text": templates.read_template(name)})
    except (FileNotFoundError, ValueError) as e:
        return _error(str(e), 404)


@app.put("/api/templates/<name>")
def put_template(name):
    text = (request.get_json(force=True).get("text") or "")
    try:
        templates.write_template(name, text)
    except ValueError as e:
        return _error(str(e))
    return jsonify({"ok": True})


@app.delete("/api/templates/<name>")
def delete_template(name):
    try:
        templates.delete_template(name)
    except ValueError as e:
        return _error(str(e))
    return jsonify({"ok": True})


# ---------- flows ----------

@app.get("/api/flows")
def get_flows():
    return jsonify({"flows": flows.load_flows(), "operations": flows.OPERATIONS})


@app.put("/api/flows")
def put_flows():
    try:
        flows.save_flows(request.get_json(force=True).get("flows", []))
    except ValueError as e:
        return _error(str(e))
    return jsonify({"ok": True})


# ---------- scrape map ----------

@app.get("/api/scrape")
def get_scrape():
    return jsonify({"items": flows.load_scrape_map()})


@app.put("/api/scrape")
def put_scrape():
    try:
        flows.save_scrape_map(request.get_json(force=True).get("items", []))
    except ValueError as e:
        return _error(str(e))
    return jsonify({"ok": True})


# ---------- run ----------

@app.post("/api/run")
def start_run():
    global _runner_proc
    data = request.get_json(force=True)
    case_flow = (data.get("case_flow") or "").strip()
    setup_flow = (data.get("setup_flow") or "").strip()
    if not case_flow:
        return _error("Choose a case flow")
    with _runner_lock:
        if _runner_proc and _runner_proc.poll() is None:
            return _error("An automation run is already in progress", 409)
        cmd = [sys.executable, "-m", "core.runner", "--case-flow", case_flow]
        if setup_flow:
            cmd += ["--setup-flow", setup_flow]
        _runner_proc = subprocess.Popen(cmd, cwd=BASE_DIR, stdout=_open_log(), stderr=subprocess.STDOUT)
    return jsonify({"ok": True, "pid": _runner_proc.pid})


@app.post("/api/stop")
def stop_run():
    with _runner_lock:
        if not _runner_proc or _runner_proc.poll() is not None:
            return _error("No run in progress", 404)
        _runner_proc.terminate()
    return jsonify({"ok": True})


@app.get("/api/run/status")
def run_status():
    running = bool(_runner_proc and _runner_proc.poll() is None)
    status = config.load_json(config.RUN_STATUS, {})
    return jsonify({"running": running, "status": status, "log": _tail_log()})


def _open_log():
    config.ensure_dirs()
    return open(config.RUN_LOG, "a", encoding="utf-8")


def _tail_log(lines=200):
    try:
        with open(config.RUN_LOG, encoding="utf-8") as f:
            return "".join(f.readlines()[-lines:])
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    config.ensure_dirs()
    templates.seed_defaults()
    flows.load_flows()
    flows.load_scrape_map()
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    app.run(host="127.0.0.1", port=PORT, debug=False)
