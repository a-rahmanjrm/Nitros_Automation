"""safe_find / safe_click / safe_send_keys: every element lookup in the runner goes through here.

Each lookup tries the locator's match types (contains, starts-with, exact) in the current
window first, then every open Chrome tab, and inside every iframe (Dynamics 365 puts the
record form in nested iframes, and a dialer is usually in its own tab).

In each document it also looks inside open Shadow DOM roots, which XPath and normal
find_elements cannot see into (Salesforce Lightning web components use them).
"""
import time

from selenium.common.exceptions import (
    InvalidSelectorException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.locators import candidates

MAX_FRAME_DEPTH = 3
MAX_SHADOW_MATCHES = 25

# Runs in the page: collects every open shadow root (nested ones too) and returns, for each
# candidate, the elements it matches inside those roots. Chromium will not run XPath with a
# shadow root as the context node, so XPath runs from the root's first element instead,
# where "//" means "anywhere in this shadow tree". Closed shadow roots cannot be reached.
_SHADOW_SEARCH_JS = """
const cands = arguments[0], limit = arguments[1];
const roots = [];
(function collect(node) {
  for (const el of node.querySelectorAll('*')) {
    if (el.shadowRoot) { roots.push(el.shadowRoot); collect(el.shadowRoot); }
  }
})(document);
if (!roots.length) return [];
const quote = (v) => '"' + CSS.escape(String(v)) + '"';
return cands.map(([kind, sel]) => {
  const out = [];
  for (const root of roots) {
    try {
      if (kind === 'xpath') {
        const ctx = root.firstElementChild;
        if (!ctx) continue;
        const res = document.evaluate(sel, ctx, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        for (let i = 0; i < res.snapshotLength; i++) {
          const n = res.snapshotItem(i);
          if (n.nodeType === 1) out.push(n);
        }
      } else {
        const css = kind === 'id' ? '[id=' + quote(sel) + ']'
          : kind === 'name' ? '[name=' + quote(sel) + ']'
          : kind === 'class' ? '.' + CSS.escape(sel)
          : sel;
        out.push(...root.querySelectorAll(css));
      }
    } catch (e) { /* selector not valid here: skip this root */ }
    if (out.length >= limit) break;
  }
  return out.slice(0, limit);
});
"""

_SHADOW_KINDS = {
    By.ID: "id",
    By.NAME: "name",
    By.CLASS_NAME: "class",
    By.CSS_SELECTOR: "css",
    By.TAG_NAME: "css",
}


def _shadow_candidates(cands):
    """(label, kind, selector) for the candidates that can be searched inside shadow roots.
    Absolute XPaths ('/html/body/...') cannot point inside a shadow tree, so they are skipped."""
    out = []
    for label, by, locator in cands:
        if by == By.XPATH:
            if not locator.startswith("/") or locator.startswith("//"):
                out.append((label, "xpath", locator))
        elif by in _SHADOW_KINDS:
            out.append((label, _SHADOW_KINDS[by], locator))
    return out


def _first_displayed(elements):
    for element in elements:
        try:
            if element.is_displayed():
                return element
        except (StaleElementReferenceException, WebDriverException):
            continue
    return None


def _shadow_match(driver, cands):
    shadow = _shadow_candidates(cands)
    if not shadow:
        return None, None
    try:
        results = driver.execute_script(_SHADOW_SEARCH_JS, [[k, s] for _, k, s in shadow], MAX_SHADOW_MATCHES)
    except WebDriverException:
        return None, None
    for (label, _, _), found in zip(shadow, results or []):
        element = _first_displayed(found or [])
        if element is not None:
            return element, label
    return None, None


def _displayed_match(driver, cands):
    for label, by, locator in cands:
        try:
            found = driver.find_elements(by, locator)
        except InvalidSelectorException:
            continue
        element = _first_displayed(found)
        if element is not None:
            return element, label
    return _shadow_match(driver, cands)


def _walk_frames(driver, cands, depth):
    """Search the current document, then each iframe (recursively). Leaves the driver inside
    the frame where the element was found, or back in the parent frame when it was not."""
    element, label = _displayed_match(driver, cands)
    if element is not None or depth >= MAX_FRAME_DEPTH:
        return element, label
    frame_count = len(driver.find_elements(By.TAG_NAME, "iframe"))
    for index in range(frame_count):
        try:
            driver.switch_to.frame(index)
        except WebDriverException:
            driver.switch_to.default_content()
            continue
        element, label = _walk_frames(driver, cands, depth + 1)
        if element is not None:
            return element, label
        driver.switch_to.parent_frame()
    return None, None


def _search_everywhere(driver, cands):
    original = driver.current_window_handle
    handles = [original] + [h for h in driver.window_handles if h != original]
    try:
        for handle in handles:
            try:
                driver.switch_to.window(handle)
                driver.switch_to.default_content()
                element, label = _walk_frames(driver, cands, 0)
            except WebDriverException:
                continue
            if element is not None:
                return element, label
        return None, None
    finally:
        # If nothing matched, leave the driver where it started
        if driver.current_window_handle != original:
            try:
                driver.switch_to.window(original)
            except WebDriverException:
                pass


def safe_find(driver, row, timeout=10, retries=2, poll=0.5, on_popup=None):
    """Return (element, match_label) for a Locators.xlsx row, or (None, None).

    Retries until timeout, then once more after clearing any blocking popup.
    """
    cands = candidates(row)
    if not cands:
        return None, None
    for attempt in range(retries + 1):
        deadline = time.monotonic() + timeout
        while True:
            element, label = _search_everywhere(driver, cands)
            if element is not None:
                return element, label
            if time.monotonic() >= deadline:
                break
            time.sleep(poll)
        if attempt < retries and on_popup and on_popup(driver):
            continue
        break
    return None, None


def safe_click(driver, element_lookup, retries=1):
    """Click an element found by safe_find. Re-finds it once if it went stale."""
    element = element_lookup()
    for attempt in range(retries + 1):
        try:
            element.click()
            return True
        except StaleElementReferenceException:
            if attempt == retries:
                return False
            element = element_lookup()
            if element is None:
                return False
        except WebDriverException:
            return False
    return False


def safe_send_keys(driver, element_lookup, text, enter=False, clear=True, retries=1):
    """Type text into an element found by safe_find. Re-finds it once if it went stale."""
    element = element_lookup()
    for attempt in range(retries + 1):
        try:
            if clear:
                try:
                    element.clear()
                except WebDriverException:
                    pass
            element.send_keys(text)
            if enter:
                element.send_keys(Keys.ENTER)
            return True
        except StaleElementReferenceException:
            if attempt == retries:
                return False
            element = element_lookup()
            if element is None:
                return False
        except WebDriverException:
            return False
    return False


def switch_to_tab_containing(driver, fragment, timeout=5):
    """Make the tab whose URL contains fragment the current one. Returns True if found."""
    deadline = time.monotonic() + timeout
    while True:
        for handle in driver.window_handles:
            try:
                driver.switch_to.window(handle)
                if fragment in driver.current_url:
                    driver.switch_to.default_content()
                    return True
            except WebDriverException:
                continue
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.5)
