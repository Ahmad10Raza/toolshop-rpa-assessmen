"""Smoke test to verify Playwright Chromium browser execution and target site connectivity."""

import sys
from playwright.sync_api import sync_playwright

TARGET_URL = "https://practicesoftwaretesting.com"


def run_smoke_test():
    """Launch headless Chromium, open home page, verify title, and exit."""
    print("[INFO] Starting browser smoke test...")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[INFO] Navigating to {TARGET_URL}")
        page.goto(TARGET_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")

        title = page.title()
        url = page.url
        print(f"[INFO] Page loaded successfully: title='{title}', url='{url}'")

        if "Practice Software Testing" not in title:
            print(f"[ERROR] Unexpected page title: {title}")
            browser.close()
            sys.exit(1)

        # Check visibility of main navigation element
        nav_locator = page.locator("nav.navbar")
        if not nav_locator.is_visible():
            print("[ERROR] Navbar element is not visible")
            browser.close()
            sys.exit(1)

        print("[INFO] Navbar is visible. Verification passed.")
        browser.close()
        print("[INFO] Browser closed cleanly. Smoke test passed.")


if __name__ == "__main__":
    run_smoke_test()
