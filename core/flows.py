"""Flows (categorised main flows made of ordered steps) and the scrape map."""
import copy

from core import config

OPERATIONS = [
    ("click", "Click"),
    ("send_keys", "Send keys"),
    ("send_enter", "Send keys + Enter"),
    ("scrape", "Scrape into variable"),
    ("navigate", "Navigate to URL (this tab)"),
    ("new_tab", "Open URL in a new tab"),
    ("switch_tab", "Switch to tab (address contains)"),
    ("wait_for", "Wait until element appears (login check)"),
    ("run_flow", "Run another flow"),
]

LOGIN_FLOW = {
    "name": "CRM login check",
    "category": "Setup",
    "steps": [
        {"label": "Wait for CRM login (first session: log in in the browser)", "item": "GlobalSearchBox", "operation": "wait_for", "value": "", "template": "", "wait": 300},
    ],
}

DEFAULT_FLOWS = [
    {
        "name": "Dialer login",
        "category": "Setup",
        "steps": [
            {"label": "Open dialer in its own tab", "item": "", "operation": "new_tab", "value": "{dialer_url}", "template": "", "wait": 3},
            {"label": "Enter Genesys user", "item": "DialerLoginUser", "operation": "send_keys", "value": "{genesys_user}", "template": "", "wait": 1},
            {"label": "Enter password", "item": "DialerLoginPass", "operation": "send_enter", "value": "{genesys_password}", "template": "", "wait": 1},
            {"label": "Enter place ID", "item": "DialerPlaceID", "operation": "send_enter", "value": "{genesys_place}", "template": "", "wait": 10},
        ],
    },
    {
        "name": "Search and open case",
        "category": "Case",
        "steps": [
            {"label": "Type case number", "item": "GlobalSearchBox", "operation": "send_keys", "value": "{case_number}", "template": "", "wait": 1},
            {"label": "Open first result", "item": "FirstSearchResult", "operation": "click", "value": "", "template": "", "wait": 2},
            {"label": "Read customer name", "item": "", "operation": "scrape", "value": "CX_name", "template": "", "wait": 0},
        ],
    },
    {
        "name": "Search and send SMS",
        "category": "Communication",
        "steps": [
            {"label": "Type case number", "item": "GlobalSearchBox", "operation": "send_keys", "value": "{case_number}", "template": "", "wait": 1},
            {"label": "Open first result", "item": "FirstSearchResult", "operation": "click", "value": "", "template": "", "wait": 2},
            {"label": "Read customer name", "item": "", "operation": "scrape", "value": "CX_name", "template": "", "wait": 0},
            {"label": "Open + menu", "item": "AddMenuButton", "operation": "click", "value": "", "template": "", "wait": 1},
            {"label": "Pick SMS", "item": "FlyoutMenuItemSMS", "operation": "click", "value": "", "template": "", "wait": 2},
            {"label": "Type SMS", "item": "SMSTextInput", "operation": "send_keys", "value": "", "template": "SMS_1", "wait": 2},
            {"label": "Save and close", "item": "SMSSaveClose", "operation": "click", "value": "", "template": "", "wait": 3},
        ],
    },
]

DEFAULT_SCRAPE = [
    {"variable": "CX_name", "item": "CustomerNameAnchor", "attribute": "aria-label", "transform": "title", "default": "Our Valued Customer"},
]


def load_flows():
    data = config.load_json(config.FLOWS_PATH, None)
    if data is None:
        data = copy.deepcopy(DEFAULT_FLOWS + [LOGIN_FLOW])
        config.save_json(config.FLOWS_PATH, data)
    return data


def _check_sub_flows(flows):
    """A 'Run another flow' step must name an existing flow, and flows may not call themselves in a loop."""
    by_name = {f["name"]: f for f in flows}

    def visit(name, path):
        if name in path:
            raise ValueError("Flow calls itself: " + " -> ".join(path + [name]))
        for step in by_name[name]["steps"]:
            if step.get("operation") == "run_flow":
                target = (step.get("value") or "").strip()
                if target not in by_name:
                    raise ValueError(f"'{name}' runs flow '{target}', which does not exist")
                visit(target, path + [name])

    for flow in flows:
        visit(flow["name"], [])


def save_flows(flows):
    for flow in flows:
        if not flow.get("name", "").strip():
            raise ValueError("Every flow needs a name")
    names = [f["name"] for f in flows]
    if len(names) != len(set(names)):
        raise ValueError("Flow names must be unique")
    _check_sub_flows(flows)
    config.save_json(config.FLOWS_PATH, flows)


def load_scrape_map():
    data = config.load_json(config.SCRAPE_PATH, None)
    if data is None:
        data = copy.deepcopy(DEFAULT_SCRAPE)
        config.save_json(config.SCRAPE_PATH, data)
    return data


def save_scrape_map(items):
    variables = [i.get("variable", "") for i in items]
    if any(not v for v in variables) or len(variables) != len(set(variables)):
        raise ValueError("Each scrape variable needs a unique name")
    config.save_json(config.SCRAPE_PATH, items)
