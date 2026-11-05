"""Chrome startup and the Genesys popup handler."""
import os
import time

from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from core import config


def profile_paths(cfg):
    """(user data folder, profile folder inside it) that Chrome will use."""
    user_data = cfg.get("chrome_user_data_dir") or os.path.join(config.DATA_DIR, "chrome_profile")
    return user_data, os.path.join(user_data, cfg.get("chrome_profile_dir") or "Default")


def profile_state(cfg):
    """'new' if the profile has never been opened (first session needs a manual login), else 'existing'."""
    _, profile_dir = profile_paths(cfg)
    return "existing" if os.path.isdir(profile_dir) and os.listdir(profile_dir) else "new"


def start_browser(cfg):
    options = Options()
    for arg in ("--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu", "--start-maximized"):
        options.add_argument(arg)
    user_data, _ = profile_paths(cfg)
    os.makedirs(user_data, exist_ok=True)
    options.add_argument(f"--user-data-dir={user_data}")
    options.add_argument(f"--profile-directory={cfg.get('chrome_profile_dir') or 'Default'}")
    # Block notification prompts so the "Allow notifications?" bubble never stops the flow.
    # 2 = block (the value Chrome stores for the notifications content setting).
    options.add_argument("--disable-notifications")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
    })
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def dismiss_genesys_popup(driver):
    """Accept the 'Genesys WWE - Integration Enabled' alert if it is open."""
    try:
        alert = driver.switch_to.alert
        text = alert.text
    except (NoAlertPresentException, WebDriverException):
        return False
    if "Genesys WWE" in text and "Integration Enabled" in text:
        alert.accept()
        return True
    return False


def dismiss_security_warning(driver):
    """Clear Chrome's 'Your connection is not private' page: click Advanced, then Proceed.

    Chrome gives this page fixed ids: 'details-button' (Advanced) and 'proceed-link'.
    Returns True if the page was passed.
    """
    try:
        details = driver.find_elements(By.ID, "details-button")
        if details and details[0].is_displayed():
            details[0].click()
            time.sleep(0.5)
        links = driver.find_elements(By.ID, "proceed-link")
        if links and links[0].is_displayed():
            links[0].click()
            time.sleep(1)
            return True
    except WebDriverException:
        pass
    return False


def dismiss_popups(driver):
    """Clear every blocking popup that can stop a step: Genesys alert and Chrome security page."""
    dismissed = dismiss_genesys_popup(driver)
    dismissed = dismiss_security_warning(driver) or dismissed
    return dismissed


def wait_and_dismiss(driver, tries=5, poll=1):
    """Give the security page a moment to appear after a navigation, then clear it."""
    for _ in range(tries):
        if dismiss_popups(driver):
            return True
        time.sleep(poll)
    return False
