"""User account model, unique credential generator, and registration workflow."""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional
from playwright.sync_api import Page
from config.settings import Settings, get_settings


@dataclass
class UserProfile:
    """Represents a generated user profile for the assessment run."""
    first_name: str
    last_name: str
    dob: str
    street: str
    house_number: str
    postal_code: str
    city: str
    state: str
    country: str
    phone: str
    email: str
    password: str
    totp_secret: Optional[str] = None


def generate_unique_user(settings: Optional[Settings] = None) -> UserProfile:
    """Generate a unique test user profile derived from centralized configuration."""
    cfg = settings or get_settings()
    unique_suffix = uuid.uuid4().hex[:8]

    # Combine configured base password and unique suffix to avoid data breach blocks
    safe_password = f"{cfg.user_base_password}_{unique_suffix}"

    return UserProfile(
        first_name=cfg.user_first_name,
        last_name=cfg.user_last_name,
        dob=cfg.user_dob,
        street=cfg.user_street,
        house_number=cfg.user_house_number,
        postal_code=cfg.user_postal_code,
        city=cfg.user_city,
        state=cfg.user_state,
        country=cfg.user_country,
        phone=cfg.user_phone,
        email=f"{cfg.user_email_prefix}_{unique_suffix}@{cfg.user_email_domain}",
        password=safe_password,
    )


def register_account(
    page: Page,
    user: UserProfile,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Navigate to the registration page, fill the full form, and verify registration."""
    log = logger or logging.getLogger("toolshop_rpa")
    register_url = f"{base_url}/auth/register"
    log.info(f"[REGISTRATION] Navigating to {register_url}")

    try:
        page.goto(register_url, wait_until="domcontentloaded", timeout=30000)
    except Exception as exc:
        log.warning(f"[REGISTRATION] Initial page load timed out ({exc}), retrying navigation...")
        page.goto(register_url, wait_until="domcontentloaded", timeout=45000)

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    log.info(f"[REGISTRATION] Filling registration form for email: {user.email}")
    page.locator("[data-test='first-name']").fill(user.first_name)
    page.locator("[data-test='last-name']").fill(user.last_name)
    page.locator("[data-test='dob']").fill(user.dob)
    page.locator("[data-test='street']").fill(user.street)
    page.locator("[data-test='house_number']").fill(user.house_number)
    page.locator("[data-test='postal_code']").fill(user.postal_code)
    page.locator("[data-test='city']").fill(user.city)
    page.locator("[data-test='state']").fill(user.state)
    page.locator("[data-test='country']").select_option(user.country)
    page.locator("[data-test='phone']").fill(user.phone)
    page.locator("[data-test='email']").fill(user.email)
    page.locator("[data-test='password']").fill(user.password)

    page.locator("[data-test='register-submit']").click()

    # Wait for observable redirect to login page
    log.info("[REGISTRATION] Submitting form and awaiting redirect to login...")
    page.wait_for_url("**/auth/login", timeout=15000)
    page.wait_for_load_state("networkidle")
    log.info(f"[REGISTRATION] Registered account for '{user.email}'")
