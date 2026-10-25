"""Integration test executing the full Part 1 account lifecycle against the live website."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright
from config.settings import get_settings
from utils.logger import setup_logger
from tasks.account import generate_unique_user, register_account
from tasks.authentication import (
    login_initial,
    enable_totp,
    logout,
    test_invalid_password,
    login_with_totp,
)


def run_account_lifecycle_test(headless: bool = False):
    """Execute the end-to-end Part 1 account lifecycle with live visual inspection."""
    settings = get_settings(headed_override=not headless)
    logger = setup_logger(settings.log_file, settings.log_level)

    logger.info("[PART_1] Starting account lifecycle and 2FA test run")

    # User profile is fully derived from centralized settings
    user = generate_unique_user(settings)
    logger.info(f"[PART_1] Generated test user: email='{user.email}'")

    with sync_playwright() as playwright:
        logger.info(f"[PART_1] Launching Chromium (headless={headless})...")
        browser = playwright.chromium.launch(headless=headless, slow_mo=300)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Step 1: Register Account
            logger.info("[STEP_1] Executing registration...")
            register_account(page, user, settings.base_url, logger)

            # Step 2: Initial Login (without 2FA)
            logger.info("[STEP_2] Executing initial login without 2FA...")
            login_initial(page, user.email, user.password, settings.base_url, logger)

            # Step 3: Enable TOTP 2FA in Profile
            logger.info("[STEP_3] Enabling Two-Factor Authentication in profile...")
            user.totp_secret = enable_totp(page, settings.base_url, logger)
            assert user.totp_secret, "Failed to capture TOTP secret key"

            # Step 4: Logout
            logger.info("[STEP_4] Logging out of session...")
            logout(page, logger)

            # Step 5: Negative Login Test (Configurable incorrect password)
            logger.info("[STEP_5] Testing incorrect password rejection...")
            test_invalid_password(page, user.email, settings.wrong_test_password, settings.base_url, logger)

            # Step 6: Log in with correct password and fresh TOTP code
            logger.info("[STEP_6] Logging in with correct credentials and fresh TOTP code...")
            login_with_totp(page, user.email, user.password, user.totp_secret, settings.base_url, logger)

            logger.info("[PART_1] SUCCESS: Complete Part 1 account lifecycle verified successfully!")
        except Exception as exc:
            logger.error(f"[PART_1] Test failed with error: {exc}", exc_info=True)
            page.screenshot(path="artifacts/part1_failure.png", full_page=True)
            raise
        finally:
            context.close()
            browser.close()


def test_account_lifecycle_integration():
    """Pytest entrypoint running in automated test suites."""
    run_account_lifecycle_test(headless=False)


if __name__ == "__main__":
    run_account_lifecycle_test(headless=False)
