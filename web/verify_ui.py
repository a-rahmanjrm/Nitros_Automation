"""Load every tab at phone, tablet and desktop widths. Report console errors, page errors
and any horizontal overflow, and save screenshots to data/logs/ui_check/.

    python web/verify_ui.py      (start web/app.py first, or this script starts it)
"""
import os
import sys
import threading
import time
import urllib.request

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5057"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "logs", "ui_check")
WIDTHS = [375, 768, 1280]
TABS = ["setup", "locators", "templates", "flows", "scrape", "run"]


def server_up():
    try:
        urllib.request.urlopen(BASE, timeout=1)
        return True
    except Exception:
        return False


def main():
    os.makedirs(OUT, exist_ok=True)
    if not server_up():
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import app as web_app
        threading.Thread(target=lambda: web_app.app.run(host="127.0.0.1", port=5057, debug=False, use_reloader=False), daemon=True).start()
        for _ in range(40):
            if server_up():
                break
            time.sleep(0.25)

    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for width in WIDTHS:
            ctx = browser.new_context(viewport={"width": width, "height": 860}, device_scale_factor=1)
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m, errs=errors: errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
            page.on("pageerror", lambda e, errs=errors: errs.append(f"pageerror: {e}"))
            for tab in TABS:
                page.goto(f"{BASE}/#{tab}")
                page.wait_for_timeout(900)
                overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                active = page.evaluate("() => document.querySelector('.view.active')?.id")
                if overflow > 0:
                    problems.append(f"{width}px {tab}: horizontal overflow {overflow}px")
                if active != f"view-{tab}":
                    problems.append(f"{width}px {tab}: wrong view active ({active})")
                page.screenshot(path=os.path.join(OUT, f"{tab}_{width}.png"), full_page=True)
            for e in errors:
                problems.append(f"{width}px: {e}")
            ctx.close()
        browser.close()

    print("Screenshots:", OUT)
    if problems:
        print("PROBLEMS:")
        for line in dict.fromkeys(problems):
            print(" -", line)
        return 1
    print("No overflow, no console errors, all views rendered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
