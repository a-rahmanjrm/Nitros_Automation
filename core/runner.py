"""Automation runner. Started by the web app as a subprocess:

    python -m core.runner --case-flow "Search and open case" [--setup-flow "Dialer login"]

It reads the saved credentials, flows, scrape map, Locators.xlsx and Cases.xlsx,
then runs the setup flow once and the case flow once per case.
"""
import argparse
import re
import time
import traceback
from datetime import datetime

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

from core import config, credentials, excel_io, flows, templates
from core.browser import dismiss_popups, profile_state, start_browser, wait_and_dismiss
from core.locators import MATCH_TYPES
from core.safe import safe_click, safe_find, safe_send_keys, switch_to_tab_containing


class StepFailed(Exception):
    pass


def log(message):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {message}", flush=True)


def write_status(**fields):
    fields["updated"] = datetime.now().isoformat(timespec="seconds")
    config.save_json(config.RUN_STATUS, fields)


class Runner:
    def __init__(self, cfg, driver, locators, scrape_map, flows):
        self.cfg = cfg
        self.driver = driver
        self.locators = {row["Name"]: row for row in locators}
        self.scrape_map = scrape_map
        self.flows = flows

    def find(self, name):
        """Find a locator's element, or None. Saves a newly working match type to Locators.xlsx."""
        row = self.locators.get(name)
        if row is None:
            raise StepFailed(f"locator '{name}' is not in Locators.xlsx")
        element, found_by = safe_find(self.driver, row, timeout=10, retries=2, on_popup=dismiss_popups)
        if element is None:
            self._screenshot(name)
            return None
        if found_by in MATCH_TYPES and found_by != row.get("Match"):
            log(f"    '{name}' matched with '{found_by}' (saved: '{row.get('Match') or 'none'}'), saving")
            row["Match"] = found_by
            try:
                excel_io.update_locator_match(self.cfg["locators_path"], row["_row"], found_by)
            except PermissionError:
                log("    [WARN] Locators.xlsx is open in Excel, match type not saved")
        return element

    def element(self, name):
        element = self.find(name)
        if element is None:
            raise StepFailed(f"element '{name}' not found")
        return element

    def run_flow(self, flow, variables, stack=()):
        if flow["name"] in stack:
            raise StepFailed(f"flow '{flow['name']}' calls itself ({' -> '.join(stack + (flow['name'],))})")
        indent = "  " * len(stack)
        log(f"{indent}Flow '{flow['name']}' ({len(flow['steps'])} steps)")
        for number, step in enumerate(flow["steps"], start=1):
            label = step.get("label") or step.get("item") or step.get("operation")
            log(f"{indent}  [{number}] {label}")
            dismiss_popups(self.driver)
            try:
                self.execute(step, variables, stack + (flow["name"],))
            except (WebDriverException, templates.MissingVariable, StepFailed) as e:
                raise StepFailed(f"step {number} '{label}': {e}") from None
            # wait_for uses its wait as the timeout, so it does not also sleep afterwards
            wait = float(step.get("wait") or 0)
            if wait and step.get("operation") != "wait_for":
                time.sleep(wait)

    def wait_for(self, name, timeout):
        """Poll until a locator appears (used for the manual CRM login on a new profile)."""
        row = self.locators.get(name)
        if row is None:
            raise StepFailed(f"locator '{name}' is not in Locators.xlsx")
        log(f"    waiting up to {int(timeout)}s for '{name}' to appear")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            dismiss_popups(self.driver)
            element, _ = safe_find(self.driver, row, timeout=2, retries=0)
            if element is not None:
                return
        raise StepFailed(f"'{name}' did not appear within {int(timeout)}s")

    def execute(self, step, variables, stack=()):
        operation = step.get("operation")
        value = (step.get("value") or "").strip()
        if operation == "run_flow":
            sub = self.flows.get(value)
            if sub is None:
                raise StepFailed(f"flow '{value}' does not exist")
            self.run_flow(sub, variables, stack)
        elif operation == "wait_for":
            self.wait_for(step.get("item") or "", float(step.get("wait") or 0) or 300)
        elif operation == "navigate":
            self.driver.get(templates.render(value, variables))
            if wait_and_dismiss(self.driver):
                log("    security warning page passed (Advanced > Proceed)")
        elif operation == "new_tab":
            # Open a URL in its own tab so the CRM tab is kept
            self.driver.switch_to.new_window("tab")
            self.driver.get(templates.render(value, variables))
            if wait_and_dismiss(self.driver):
                log("    security warning page passed (Advanced > Proceed)")
        elif operation == "switch_tab":
            if not switch_to_tab_containing(self.driver, templates.render(value, variables)):
                raise StepFailed(f"no open tab has '{value}' in its address")
        elif operation == "scrape":
            self.scrape(value, variables)
        elif operation == "click":
            if not safe_click(self.driver, lambda: self.element(step.get("item") or "")):
                raise StepFailed(f"could not click '{step.get('item')}'")
        elif operation in ("send_keys", "send_enter"):
            text = self.text_for(step, variables)
            lookup = lambda: self.element(step.get("item") or "")
            if not safe_send_keys(self.driver, lookup, text, enter=(operation == "send_enter")):
                raise StepFailed(f"could not type into '{step.get('item')}'")
        else:
            raise StepFailed(f"unknown operation '{operation}'")

    def text_for(self, step, variables):
        """Text to type: the template file if one is chosen, otherwise the step value."""
        source = templates.read_template(step["template"]) if step.get("template") else step.get("value") or ""
        return templates.render(source, variables)

    def scrape(self, variable, variables):
        spec = self.scrape_map.get(variable)
        if spec is None:
            raise StepFailed(f"scrape variable '{variable}' is not defined in the Scrape data tab")
        element = self.find(spec["item"])
        raw = ""
        if element is not None:
            attribute = spec.get("attribute") or "text"
            raw = (element.text if attribute == "text" else element.get_attribute(attribute)) or ""
        raw = raw.strip()
        if spec.get("transform") == "title":
            raw = " ".join(word.capitalize() for word in raw.split())
        variables[variable] = raw or spec.get("default", "")
        log(f"    {variable} = {variables[variable]}")

    def _screenshot(self, name):
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", name)
        path = f"{config.ERROR_DIR}/{safe}_{datetime.now():%Y%m%d_%H%M%S}.png"
        try:
            self.driver.save_screenshot(path)
        except WebDriverException:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run Nitros automation flows")
    parser.add_argument("--case-flow", required=True)
    parser.add_argument("--setup-flow", default="")
    args = parser.parse_args(argv)

    config.ensure_dirs()
    templates.seed_defaults()
    cfg = config.load_config()

    try:
        creds = credentials.load_for_run()
    except credentials.MissingCredentials as e:
        log(f"[ERROR] {e}")
        write_status(state="error", message=str(e))
        return 2

    all_flows = {f["name"]: f for f in flows.load_flows()}
    for name in filter(None, (args.case_flow, args.setup_flow)):
        if name not in all_flows:
            log(f"[ERROR] flow '{name}' does not exist")
            write_status(state="error", message=f"flow '{name}' does not exist")
            return 2

    if not cfg["crm_url"]:
        log("[ERROR] CRM URL is not set. Add it in the Setup tab first.")
        write_status(state="error", message="CRM URL is not set in the Setup tab")
        return 2

    locators = excel_io.read_locators(cfg["locators_path"])
    cases = excel_io.read_cases(cfg["cases_path"])
    scrape_map = {s["variable"]: s for s in flows.load_scrape_map()}
    base_vars = {
        "genesys_user": creds["user"],
        "genesys_password": creds["password"],
        "genesys_place": creds["place"],
        "dialer_url": cfg["dialer_url"],
        "agent_name": cfg["agent_name"],
    }
    log(f"Loaded {len(locators)} locators and {len(cases)} cases")

    state = profile_state(cfg)
    if state == "new":
        log("First session: this Chrome profile is new. Log in to CRM in the browser window; the run waits for you.")
    else:
        log("Existing Chrome profile found, reusing its saved login.")
    driver = start_browser(cfg)
    runner = Runner(cfg, driver, locators, scrape_map, all_flows)
    total, failed = len(cases), 0
    try:
        driver.get(cfg["crm_url"])
        if args.setup_flow:
            write_status(state="running", message="Setup flow", total=total, failed=0)
            runner.run_flow(all_flows[args.setup_flow], dict(base_vars))

        for index, case in enumerate(cases, start=1):
            number = case["case_number"]
            log(f"=== Case {index}/{total}: {number}")
            write_status(state="running", case=number, index=index, total=total, failed=failed)
            variables = {**base_vars, "case_number": number, "notes": case["notes"]}
            try:
                runner.run_flow(all_flows[args.case_flow], variables)
                log("    OK")
            except StepFailed as e:
                failed += 1
                log(f"    [FAILED] {e}")
        write_status(state="finished", total=total, failed=failed)
        log(f"Finished: {total - failed} succeeded, {failed} failed")
        return 0
    except Exception:
        log(f"[ERROR] run stopped:\n{traceback.format_exc()}")
        write_status(state="error", total=total, failed=failed, message="run stopped, see log")
        return 1
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
