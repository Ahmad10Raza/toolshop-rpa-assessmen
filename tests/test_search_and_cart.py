"""Integration test for Part 3A search, cart addition, math validation, and item deletion."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright
from config.settings import get_settings
from utils.logger import setup_logger
from tasks.checkout import (
    search_catalog,
    add_product_to_cart,
    navigate_to_cart,
    validate_cart_items,
    delete_cart_item,
)


def run_search_and_cart_test(headless: bool = False):
    """Execute the end-to-end Part 3A workflow with live headed browser inspection."""
    settings = get_settings(headed_override=not headless)
    logger = setup_logger(settings.log_file, settings.log_level)

    logger.info("[PART_3A] Starting search and cart test run")

    with sync_playwright() as playwright:
        logger.info(f"[PART_3A] Launching Chromium (headless={headless})...")
        browser = playwright.chromium.launch(headless=headless, slow_mo=200)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Step 1: Search for 'pliers'
            logger.info("[STEP_1] Executing search for 'pliers'...")
            search_results = search_catalog(page, "pliers", settings.base_url, logger)
            assert len(search_results) >= 2, f"Expected at least 2 search results, got {len(search_results)}"
            logger.info(f"[STEP_1] Discovered {len(search_results)} relevant products.")

            # Step 2: Add Product 1 with Quantity = 3
            prod1 = search_results[0]
            logger.info(f"[STEP_2] Adding Product 1: '{prod1['title']}' with quantity 3...")
            add_product_to_cart(page, prod1["url"], quantity=3, logger=logger)

            # Step 3: Add Product 2 with Quantity = 1
            prod2 = search_results[1]
            logger.info(f"[STEP_3] Adding Product 2: '{prod2['title']}' with quantity 1...")
            add_product_to_cart(page, prod2["url"], quantity=1, logger=logger)

            # Step 4: Navigate to Cart
            logger.info("[STEP_4] Navigating to Cart / Checkout...")
            navigate_to_cart(page, settings.base_url, logger)

            # Step 5: Validate Line Item Pricing and Calculations
            logger.info("[STEP_5] Validating cart table line items and math...")
            cart_items = validate_cart_items(page, logger)
            assert len(cart_items) == 2, f"Expected 2 cart items, got {len(cart_items)}"
            logger.info("[STEP_5] Cart arithmetic validation passed for all items.")

            # Step 6: Delete One Item from Cart
            logger.info("[STEP_6] Deleting first item from cart...")
            delete_cart_item(page, item_index=0, logger=logger)

            # Step 7: Verify Updated Cart State
            logger.info("[STEP_7] Re-validating remaining cart state...")
            remaining_items = validate_cart_items(page, logger)
            assert len(remaining_items) == 1, f"Expected 1 remaining item, got {len(remaining_items)}"
            logger.info(f"[STEP_7] Verified single item remaining: '{remaining_items[0]['title']}'.")

            logger.info("[PART_3A] SUCCESS: Search, cart addition, math validation, and deletion verified successfully!")
        except Exception as exc:
            logger.error(f"[PART_3A] Test failed with error: {exc}", exc_info=True)
            page.screenshot(path="artifacts/part3a_failure.png", full_page=True)
            raise
        finally:
            context.close()
            browser.close()


def test_search_and_cart_integration():
    """Pytest entrypoint for automated test suites."""
    run_search_and_cart_test(headless=False)


if __name__ == "__main__":
    run_search_and_cart_test(headless=False)
