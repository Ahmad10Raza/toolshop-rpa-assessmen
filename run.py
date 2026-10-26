"""Entrypoint orchestrator for nCare RPA assessment automation."""

import argparse
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

from config.settings import Settings, get_settings
from utils.logger import setup_logger, log_business_outcome
from tasks.account import generate_unique_user, register_account
from tasks.authentication import (
    login_initial,
    enable_totp,
    logout,
    test_invalid_password,
    login_with_totp,
)
from tasks.catalog import crawl_catalog, export_catalog_csv
from tasks.checkout import (
    search_catalog,
    add_product_to_cart,
    navigate_to_cart,
    validate_cart_items,
    delete_cart_item,
    proceed_to_checkout_wizard,
    handle_checkout_auth,
    fill_billing_address,
    select_payment_and_confirm,
    handle_invoice_download,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for browser mode and catalog limits."""
    parser = argparse.ArgumentParser(description="Autonomous RPA bot for Practice Software Testing.")
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in visible headed mode.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Force browser to run in headless mode.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Max catalog pages to crawl (default: all pages).",
    )
    return parser.parse_args()


def run_orchestrator(settings: Settings, max_pages: int = None) -> int:
    """Run all assessment steps sequentially in a single unattended execution."""
    logger = setup_logger(settings.log_file, settings.log_level)

    logger.info("[ORCHESTRATOR] Starting RPA assessment run")
    logger.info(f"[ORCHESTRATOR] Target base URL: {settings.base_url}")
    logger.info(f"[ORCHESTRATOR] Headless: {settings.headless}")
    logger.info(f"[ORCHESTRATOR] Database path: {settings.db_path}")
    logger.info(f"[ORCHESTRATOR] CSV export path: {settings.csv_path}")

    user = generate_unique_user(settings)
    logger.info(f"[ORCHESTRATOR] Generated test user: '{user.email}'")

    with sync_playwright() as playwright:
        slow_mo = 200 if not settings.headless else 0
        launch_args = ["--start-maximized"] if not settings.headless else []
        logger.info(f"[ORCHESTRATOR] Launching Chromium (headless={settings.headless}, slow_mo={slow_mo})")
        browser = playwright.chromium.launch(
            headless=settings.headless,
            slow_mo=slow_mo,
            args=launch_args,
        )
        context = browser.new_context(no_viewport=True if not settings.headless else None)
        page = context.new_page()

        try:
            # Part 1: Account registration, 2FA setup, and negative test
            logger.info("[PART_1] Starting account lifecycle and 2FA")

            logger.info("[PART_1] Step 1: Registering user account...")
            register_account(page, user, settings.base_url, logger)

            logger.info("[PART_1] Step 2: Logging in before 2FA setup...")
            login_initial(page, user.email, user.password, settings.base_url, logger)

            logger.info("[PART_1] Step 3: Enabling TOTP in profile...")
            user.totp_secret = enable_totp(page, settings.base_url, logger)
            assert user.totp_secret, "Failed to capture TOTP secret key"

            logger.info("[PART_1] Step 4: Logging out...")
            logout(page, logger)

            logger.info("[PART_1] Step 5: Testing incorrect password rejection...")
            test_invalid_password(page, user.email, settings.wrong_test_password, settings.base_url, logger)

            logger.info("[PART_1] Step 6: Logging in with correct password and TOTP...")
            login_with_totp(page, user.email, user.password, user.totp_secret, settings.base_url, logger)
            logger.info("[PART_1] Account lifecycle steps finished successfully.")

            # Part 2: Dynamic facet discovery, catalog crawl, and SQLite persistence
            logger.info("[PART_2] Starting catalog extraction")

            total_products = crawl_catalog(
                context=context,
                base_url=settings.base_url,
                db_path=settings.db_path,
                max_pages=max_pages,
                logger=logger,
            )
            assert total_products > 0, "No products were extracted during catalog crawl"
            logger.info(f"[PART_2] Extracted {total_products} unique products to SQLite")

            exported_rows = export_catalog_csv(settings.db_path, settings.csv_path, logger)
            assert exported_rows == total_products, f"Export row mismatch: {exported_rows} != {total_products}"
            logger.info(f"[PART_2] Exported {exported_rows} products to {settings.csv_path}")

            # Part 3A: Search, relevance checks, cart additions, and price validation
            logger.info("[PART_3A] Starting search and cart validation")

            search_query = "pliers"
            search_results = search_catalog(page, search_query, settings.base_url, logger)
            assert len(search_results) >= 2, f"Expected at least 2 results for '{search_query}', got {len(search_results)}"

            prod1 = search_results[0]
            logger.info(f"[PART_3A] Adding '{prod1['title']}' (quantity 3)...")
            add_product_to_cart(page, prod1["url"], quantity=3, logger=logger)

            prod2 = search_results[1]
            logger.info(f"[PART_3A] Adding '{prod2['title']}' (quantity 1)...")
            add_product_to_cart(page, prod2["url"], quantity=1, logger=logger)

            navigate_to_cart(page, settings.base_url, logger)

            cart_items = validate_cart_items(page, logger)
            assert len(cart_items) == 2, f"Expected 2 cart items, got {len(cart_items)}"

            cart_initial_screenshot = settings.artifacts_dir / "cart_initial.png"
            page.screenshot(path=str(cart_initial_screenshot), full_page=True)
            logger.info(f"[PART_3A] Saved cart initial screenshot: {cart_initial_screenshot}")

            logger.info("[PART_3A] Deleting first item from cart...")
            delete_cart_item(page, item_index=0, logger=logger)

            remaining_items = validate_cart_items(page, logger)
            assert len(remaining_items) == 1, f"Expected 1 remaining item, got {len(remaining_items)}"

            cart_delete_screenshot = settings.artifacts_dir / "cart_after_delete.png"
            page.screenshot(path=str(cart_delete_screenshot), full_page=True)
            logger.info(f"[PART_3A] Saved cart after deletion screenshot: {cart_delete_screenshot}")
            logger.info("[PART_3A] Search and cart validation completed.")

            # Part 3B: Checkout wizard, payment, confirmation, and invoice check
            logger.info("[PART_3B] Starting checkout wizard")

            proceed_to_checkout_wizard(page, logger)
            handle_checkout_auth(page, user, settings.base_url, logger)
            fill_billing_address(page, user, logger)

            billing_screenshot = settings.artifacts_dir / "checkout_billing.png"
            page.screenshot(path=str(billing_screenshot), full_page=True)
            logger.info(f"[PART_3B] Saved checkout billing screenshot: {billing_screenshot}")

            confirmation_msg = select_payment_and_confirm(
                page=page,
                artifacts_dir=settings.artifacts_dir,
                payment_method=settings.payment_method,
                logger=logger,
            )
            assert "Payment was successful" in confirmation_msg

            screenshot_path = settings.artifacts_dir / "order_confirmation.png"
            assert screenshot_path.exists(), "Order confirmation screenshot was not created"
            logger.info(f"[PART_3B] Order confirmation screenshot saved: {screenshot_path}")

            invoice_pdf = handle_invoice_download(page, settings.base_url, settings.artifacts_dir, logger)
            if invoice_pdf:
                logger.info(f"[PART_3B] Downloaded invoice: {invoice_pdf}")
            else:
                logger.info("[PART_3B] Invoice handling finished (none returned by demo backend).")

            logger.info("[PART_3B] Checkout workflow completed.")

            # Summary
            logger.info("[ORCHESTRATOR] Run finished successfully.")
            logger.info(f"[ORCHESTRATOR] Products in database: {settings.db_path} ({total_products} records)")
            logger.info(f"[ORCHESTRATOR] Products in CSV: {settings.csv_path} ({exported_rows} rows)")
            logger.info(f"[ORCHESTRATOR] Log file: {settings.log_file}")
            logger.info(f"[ORCHESTRATOR] Confirmation screenshot: {screenshot_path}")

            log_business_outcome(
                logger,
                action="FULL_EXECUTION",
                outcome="SUCCESS",
                details=f"All parts (1, 2, 3A, 3B) completed successfully. Total products: {total_products}.",
            )
            return 0

        except Exception as exc:
            logger.error(f"[ORCHESTRATOR] Run failed with error: {exc}", exc_info=True)
            settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
            failure_screenshot = settings.artifacts_dir / "run_failure.png"
            page.screenshot(path=str(failure_screenshot), full_page=True)
            logger.error(f"[ORCHESTRATOR] Saved failure screenshot to {failure_screenshot}")
            return 1
        finally:
            context.close()
            browser.close()


def main():
    """CLI entrypoint."""
    args = parse_arguments()

    headed_override = args.headed
    settings = get_settings(headed_override=headed_override)
    if args.headless:
        settings.headless = True

    exit_code = run_orchestrator(settings, max_pages=args.max_pages)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
