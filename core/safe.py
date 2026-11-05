"""safe_find / safe_click / safe_send_keys: every element lookup in the runner goes through here.

Each lookup tries the locator's match types (contains, starts-with, exact) in the current
window first, then every open Chrome tab, and inside every iframe (Dynamics 365 puts the
record form in nested iframes, and the dialer is usually in its own tab).
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


def _displayed_match(driver, cands):
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
    return None, None


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
