"""Integration test for Part 3B authenticated checkout wizard, payment, and invoice handling."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright
from config.settings import get_settings
from utils.logger import setup_logger
from tasks.account import generate_unique_user, register_account
from tasks.authentication import login_initial
from tasks.checkout import (
    search_catalog,
    add_product_to_cart,
    navigate_to_cart,
    proceed_to_checkout_wizard,
    handle_checkout_auth,
    fill_billing_address,
    select_payment_and_confirm,
    handle_invoice_download,
)


def run_checkout_workflow_test(headless: bool = False):
    """Execute authenticated checkout wizard, order confirmation, and invoice handling headed."""
    settings = get_settings(headed_override=not headless)
    logger = setup_logger(settings.log_file, settings.log_level)

    logger.info("[PART_3B] Starting checkout workflow test run")

    user = generate_unique_user(settings)
    logger.info(f"[PART_3B] Generated test user: '{user.email}'")

    with sync_playwright() as playwright:
        logger.info(f"[PART_3B] Launching Chromium (headless={headless})...")
        browser = playwright.chromium.launch(headless=headless, slow_mo=200)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Step 1: User Registration and Login Setup
            logger.info("[STEP_1] Registering and authenticating test user...")
            register_account(page, user, settings.base_url, logger)
            login_initial(page, user.email, user.password, settings.base_url, logger)

            # Step 2: Add Product to Cart
            logger.info("[STEP_2] Searching catalog and adding item to cart...")
            search_results = search_catalog(page, "pliers", settings.base_url, logger)
            assert len(search_results) > 0, "No search results returned"
            add_product_to_cart(page, search_results[0]["url"], quantity=1, logger=logger)

            # Step 3: Navigate to Cart
            logger.info("[STEP_3] Navigating to Cart...")
            navigate_to_cart(page, settings.base_url, logger)

            # Step 4: Step 1 -> Step 2 (Proceed to Checkout Wizard)
            logger.info("[STEP_4] Advancing to checkout wizard...")
            proceed_to_checkout_wizard(page, logger)

            # Step 5: Verify Auth in Wizard Step 2
            logger.info("[STEP_5] Verifying user authentication in wizard...")
            handle_checkout_auth(page, user, settings.base_url, logger)

            # Step 6: Step 3 (Billing Address)
            logger.info("[STEP_6] Populating billing address...")
            fill_billing_address(page, user, logger)

            # Step 7: Step 4 (Payment Method & Confirmation)
            logger.info("[STEP_7] Selecting payment method and confirming order...")
            confirmation_msg = select_payment_and_confirm(
                page=page,
                artifacts_dir=settings.artifacts_dir,
                payment_method=settings.payment_method,
                logger=logger,
            )
            assert "Payment was successful" in confirmation_msg, f"Unexpected message: {confirmation_msg}"

            # Step 8: Verify Order Confirmation Screenshot Deliverable
            screenshot_file = settings.artifacts_dir / "order_confirmation.png"
            assert screenshot_file.exists(), "Order confirmation screenshot was not created"
            logger.info(f"[STEP_8] Verified order confirmation screenshot deliverable: {screenshot_file}")

            # Step 9: Handle Invoice Download
            logger.info("[STEP_9] Checking invoice download availability...")
            invoice_pdf = handle_invoice_download(page, settings.base_url, settings.artifacts_dir, logger)
            if invoice_pdf:
                logger.info(f"[STEP_9] Downloaded invoice deliverable: {invoice_pdf}")
            else:
                logger.info("[STEP_9] Invoice handling completed cleanly (no invoice provided by demo backend).")

            logger.info("[PART_3B] SUCCESS: Authenticated checkout workflow verified successfully!")
        except Exception as exc:
            logger.error(f"[PART_3B] Test failed with error: {exc}", exc_info=True)
            page.screenshot(path="artifacts/part3b_failure.png", full_page=True)
            raise
        finally:
            context.close()
            browser.close()


def test_checkout_workflow_integration():
    """Pytest entrypoint for automated test suites."""
    run_checkout_workflow_test(headless=False)


if __name__ == "__main__":
    run_checkout_workflow_test(headless=False)
