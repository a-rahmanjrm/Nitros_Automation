"""Paths, settings and small JSON helpers shared by the web app and the runner."""
import json
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_DIR = os.path.join(BASE_DIR, "excel")
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATE_DIR = os.path.join(DATA_DIR, "message_templates")
LOG_DIR = os.path.join(DATA_DIR, "logs")
ERROR_DIR = os.path.join(LOG_DIR, "errors")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
FLOWS_PATH = os.path.join(DATA_DIR, "flows.json")
SCRAPE_PATH = os.path.join(DATA_DIR, "scrape_map.json")
RUN_LOG = os.path.join(LOG_DIR, "run.log")
RUN_STATUS = os.path.join(LOG_DIR, "run_status.json")

DEFAULT_CONFIG = {
    "locators_path": os.path.join(EXCEL_DIR, "Locators.xlsx"),
    "cases_path": os.path.join(EXCEL_DIR, "Cases.xlsx"),
    "crm_url": "",  # e.g. https://<your-org>.crm.dynamics.com (set in the Setup tab)
    "dialer_url": "",  # your Genesys WWE login page (set in the Setup tab)
    "agent_name": "",
    # Empty = a dedicated Chrome profile in data/chrome_profile.
    # Set to your Chrome "User Data" folder to reuse your logged-in session (close Chrome first).
    "chrome_user_data_dir": "",
    "chrome_profile_dir": "Default",
}


def ensure_dirs():
    for folder in (DATA_DIR, TEMPLATE_DIR, LOG_DIR, ERROR_DIR, EXCEL_DIR):
        os.makedirs(folder, exist_ok=True)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=folder, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def load_config():
    return {**DEFAULT_CONFIG, **load_json(CONFIG_PATH, {})}


def save_config(updates):
    cfg = load_config()
    cfg.update({k: str(v).strip() for k, v in updates.items() if k in DEFAULT_CONFIG})
    save_json(CONFIG_PATH, cfg)
    return cfg
