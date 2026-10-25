"""Authentication task workflows: login, TOTP 2FA setup, negative test, and 2FA login."""

import logging
from typing import Optional
import pyotp
from playwright.sync_api import Page
from utils.logger import log_business_outcome
from utils.retry import execute_with_retry


def login_initial(
    page: Page,
    email: str,
    password: str,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Log in with registered credentials prior to 2FA enablement using safe-anchor retry."""
    log = logger or logging.getLogger("toolshop_rpa")
    login_url = f"{base_url}/auth/login"

    def _perform_login():
        log.info(f"[LOGIN_INITIAL] Navigating to {login_url}")
        page.goto(login_url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")

        log.info("[LOGIN_INITIAL] Submitting credentials...")
        page.locator("[data-test='email']").fill(email)
        page.locator("[data-test='password']").fill(password)
        page.locator("[data-test='login-submit']").click()

        # Wait for observable account dashboard title
        page.locator("[data-test='page-title']").wait_for(state="visible", timeout=15000)
        page.wait_for_load_state("networkidle")
        log.info("[LOGIN_INITIAL] Logged in to account dashboard")

    execute_with_retry(
        page=page,
        action_name="login_initial",
        action_fn=_perform_login,
        recovery_url=login_url,
        logger=log,
    )


def enable_totp(
    page: Page,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Navigate to profile, extract TOTP secret into memory, submit verification code, and return secret."""
    log = logger or logging.getLogger("toolshop_rpa")
    profile_url = f"{base_url}/account/profile"
    log.info(f"[TOTP_SETUP] Navigating to {profile_url}")

    page.goto(profile_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    # Locate the TOTP secret key rendered on screen
    log.info("[TOTP_SETUP] Locating TOTP secret key...")
    secret_locator = page.locator("[data-test='totp-secret']")
    secret_locator.wait_for(state="visible", timeout=15000)
    raw_secret = secret_locator.inner_text().strip()

    # Sanitized validation (held strictly in memory)
    secret = raw_secret.replace(" ", "").upper()
    log.info("[TOTP_SETUP] Captured TOTP secret key into memory.")

    # Calculate immediate verification code
    totp = pyotp.TOTP(secret)
    verification_code = totp.now()
    log.info("[TOTP_SETUP] Submitting calculated verification code to activate 2FA...")

    totp_input = page.locator("input#totp_code, input[data-test='totp-code'], input[placeholder*='TOTP']")
    totp_input.fill(verification_code)

    verify_btn = page.locator("button:has-text('Verify TOTP'), [data-test='totp-submit'], [data-test='verify-totp']")
    verify_btn.click()

    # Wait for success notification banner
    success_banner = page.locator("div.alert-success:has-text('TOTP verified and enabled successfully')")
    try:
        success_banner.wait_for(state="visible", timeout=10000)
        log.info("[TOTP_SETUP] TOTP verified and enabled successfully")
    except Exception as exc:
        log.warning(f"[TOTP_SETUP] Success banner wait: {exc}. Checking page state...")

    # Known front-end quirk handling
    quirk_alert = page.locator("div.alert-danger:has-text('Failed to load TOTP setup details')")
    if quirk_alert.count() > 0 and quirk_alert.is_visible():
        log.warning("[TOTP_SETUP] UI anomaly detected: 'Failed to load TOTP setup details'. Continuing.")

    return secret


def logout(
    page: Page,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Log out of the current authenticated user session."""
    log = logger or logging.getLogger("toolshop_rpa")
    log.info("[LOGOUT] Opening user menu to log out...")

    # Verified selector for the user menu dropdown in navbar
    user_menu = page.locator("[data-test='nav-menu'], #menu")
    user_menu.wait_for(state="visible", timeout=15000)
    user_menu.click()

    sign_out_btn = page.locator("[data-test='nav-sign-out']")
    sign_out_btn.wait_for(state="visible", timeout=10000)
    sign_out_btn.click()

    # Wait for navigation link to revert to Sign in
    page.locator("[data-test='nav-sign-in']").wait_for(state="visible", timeout=15000)
    page.wait_for_load_state("networkidle")
    log.info("[LOGOUT] User session ended cleanly")


def test_invalid_password(
    page: Page,
    email: str,
    wrong_password: str,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Attempt login with an incorrect password and assert clean business rejection."""
    log = logger or logging.getLogger("ncare_rpa")
    login_url = f"{base_url}/auth/login"
    log.info(f"[AUTH_NEGATIVE_TEST] Navigating to {login_url} to test invalid password...")

    page.goto(login_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    page.locator("[data-test='email']").fill(email)
    page.locator("[data-test='password']").fill(wrong_password)
    page.locator("[data-test='login-submit']").click()

    # Observable wait for expected error message
    error_alert = page.locator("div.alert-danger:has-text('Invalid email or password'), [data-test='login-error']")
    error_alert.wait_for(state="visible", timeout=10000)

    log_business_outcome(
        log,
        action="AUTH_NEGATIVE_TEST",
        outcome="EXPECTED_REJECTION",
        details="Site rejected invalid credentials as expected",
    )


def login_with_totp(
    page: Page,
    email: str,
    password: str,
    secret: str,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Complete 2FA login by entering password and generating fresh TOTP code at login moment."""
    log = logger or logging.getLogger("ncare_rpa")
    login_url = f"{base_url}/auth/login"
    log.info(f"[LOGIN_TOTP] Navigating to {login_url} for 2FA login...")

    page.goto(login_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    # Step 1: Submit email and password
    page.locator("[data-test='email']").fill(email)
    page.locator("[data-test='password']").fill(password)
    page.locator("[data-test='login-submit']").click()

    # Step 2: Observable wait for the TOTP second-step input field
    log.info("[LOGIN_TOTP] Waiting for 2FA prompt...")
    totp_input = page.locator("input#totp_code, input[data-test='totp-code'], input[placeholder*='TOTP']")
    totp_input.wait_for(state="visible", timeout=15000)

    # Generate fresh code at the moment of submission
    fresh_code = pyotp.TOTP(secret).now()
    log.info("[LOGIN_TOTP] Generated fresh TOTP code. Submitting...")
    totp_input.fill(fresh_code)

    # Verified locator for the 2FA login submit input
    verify_btn = page.locator("[data-test='verify-totp'], input[value='Verify TOTP'], button:has-text('Verify TOTP')")
    verify_btn.wait_for(state="visible", timeout=10000)
    verify_btn.click()

    # Step 3: Verify arrival on authenticated account page
    page.locator("[data-test='page-title']:has-text('My account')").wait_for(state="visible", timeout=15000)
    page.wait_for_load_state("networkidle")
    log.info("[LOGIN_TOTP] Logged in successfully with 2FA")
