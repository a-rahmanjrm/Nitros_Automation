"""Turn a Locators.xlsx row into a Selenium locator and find the element.

MSD ids are dynamic, so each row stores a fragment (Value) plus a match type.
If the saved match type finds nothing, the other match types are tried in turn.
The runner saves whichever one works back to Locators.xlsx.
"""
import time

from selenium.common.exceptions import InvalidSelectorException, StaleElementReferenceException
from selenium.webdriver.common.by import By

MATCH_TYPES = ("contains", "starts-with", "exact")
STRATEGIES = {
    "XPATH": By.XPATH,
    "ID": By.ID,
    "CSS_SELECTOR": By.CSS_SELECTOR,
    "NAME": By.NAME,
    "CLASS_NAME": By.CLASS_NAME,
    "TAG_NAME": By.TAG_NAME,
}


def xpath_literal(text):
    """Quote a string for XPath, handling embedded single or double quotes."""
    if "'" not in text:
        return f"'{text}'"
    if '"' not in text:
        return f'"{text}"'
    parts = text.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"


PART_SEPARATOR = "|"
MAX_PARTS = 3


def split_parts(value):
    """Value may hold up to three fragments separated by '|', e.g. 'timeline|highlights|content'."""
    return [p.strip() for p in (value or "").split(PART_SEPARATOR) if p.strip()][:MAX_PARTS]


def build_xpath(attribute, value, match):
    """Build //*[...] for one match type.

    Each fragment becomes its own condition, joined with 'and'. The first fragment uses the
    match type (contains / starts-with / exact); later fragments always use contains, and
    'exact' with more than one fragment falls back to contains because one attribute cannot equal several values.
    Attribute 'text' matches the element's text. A text match also holds for elements that wrap
    the text (a toolbar div, body, html...), so it is narrowed to the innermost element: one that
    matches but has no matching descendant.
    """
    parts = split_parts(value)
    if not parts:
        return None
    target = "normalize-space(.)" if attribute == "text" else f"@{attribute or 'id'}"
    conditions = []
    for index, part in enumerate(parts):
        literal = xpath_literal(part)
        if index == 0 and match == "exact" and len(parts) == 1:
            conditions.append(f"{target}={literal}")
        elif index == 0 and match == "starts-with":
            conditions.append(f"starts-with({target},{literal})")
        else:
            conditions.append(f"contains({target},{literal})")
    condition = " and ".join(conditions)
    if attribute == "text":
        return f"//*[{condition} and not(.//*[{condition}])]"
    return f"//*[{condition}]"


def candidates(row):
    """Ordered (label, by, locator) tuples to try for one locator row.

    Order: Full XPath (if pasted), then the saved match type, then the other match types.
    """
    value = (row.get("Value") or "").strip()
    full = (row.get("Full XPath") or "").strip()
    strategy = (row.get("Strategy") or "XPATH").strip().upper()
    out = []
    if full:
        out.append(("Full XPath", By.XPATH, full))
    if strategy != "XPATH" and strategy in STRATEGIES:
        if value:
            out.append((strategy, STRATEGIES[strategy], value))
        return out
    if not value:
        return out
    saved = (row.get("Match") or "").strip().lower()
    order = [saved] + [m for m in MATCH_TYPES if m != saved] if saved in MATCH_TYPES else list(MATCH_TYPES)
    for match in order:
        xpath = build_xpath(row.get("Attribute"), value, match)
        if xpath:
            out.append((match, By.XPATH, xpath))
    return out


def resolve(driver, row, timeout=10, poll=0.5):
    """Return (element, label) for the first displayed match, or (None, None) after timeout."""
    cands = candidates(row)
    deadline = time.monotonic() + timeout
    while True:
        for label, by, locator in cands:
            try:
                found = driver.find_elements(by, locator)
            except InvalidSelectorException:
                continue
            for element in found:
                try:
                    if element.is_displayed():
                        return element, label
                except StaleElementReferenceException:
                    continue
        if time.monotonic() >= deadline:
            return None, None
        time.sleep(poll)
