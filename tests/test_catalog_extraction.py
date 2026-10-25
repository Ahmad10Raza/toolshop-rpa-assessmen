"""Integration test for Part 2 catalog crawling, product extraction, and idempotency."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright
from config.settings import get_settings
from utils.logger import setup_logger
from utils.database import get_product_count, get_all_products
from tasks.catalog import crawl_catalog, export_catalog_csv


def run_catalog_extraction_test(headless: bool = False, max_pages: int = 2):
    """Execute catalog crawling test in headed browser mode and assert database persistence."""
    settings = get_settings(headed_override=not headless)
    logger = setup_logger(settings.log_file, settings.log_level)

    logger.info(f"[PART_2] Starting catalog extraction test (max_pages={max_pages})")

    # Use dedicated test DB to verify clean isolated run
    test_db = settings.output_dir / "test_products.db"
    test_csv = settings.output_dir / "test_products.csv"
    if test_db.exists():
        test_db.unlink()
    if test_csv.exists():
        test_csv.unlink()

    with sync_playwright() as playwright:
        logger.info(f"[PART_2] Launching Chromium (headless={headless})...")
        browser = playwright.chromium.launch(headless=headless, slow_mo=100)
        context = browser.new_context()

        try:
            # 1. First Crawl Run
            logger.info("[RUN_1] Executing first crawl...")
            count_run_1 = crawl_catalog(
                context=context,
                base_url=settings.base_url,
                db_path=test_db,
                max_pages=max_pages,
                logger=logger,
            )
            assert count_run_1 > 0, "No products were extracted during first run"
            logger.info(f"[RUN_1] Extracted {count_run_1} unique products.")

            # 2. Export to CSV
            csv_rows = export_catalog_csv(test_db, test_csv, logger)
            assert csv_rows == count_run_1, f"CSV rows ({csv_rows}) != DB rows ({count_run_1})"
            assert test_csv.exists(), "CSV output file was not created"
            logger.info(f"[RUN_1] Verified CSV export has exactly {csv_rows} rows.")

            # Sample validation
            sample_products = get_all_products(test_db)
            first_product = sample_products[0]
            logger.info(f"[RUN_1] Sample extracted product: ID='{first_product['product_id']}', Name='{first_product['product_name']}', Price={first_product['price']}, Category='{first_product['category']}', Brand='{first_product['brand']}'")
            assert first_product["product_name"], "Product name is empty"
            assert first_product["price"] is not None, "Product price is missing or null"

            # 3. Idempotency Test (Second Crawl Run)
            logger.info("[RUN_2] Executing second crawl over page 1 to verify idempotency...")
            count_run_2 = crawl_catalog(
                context=context,
                base_url=settings.base_url,
                db_path=test_db,
                max_pages=1,
                logger=logger,
            )
            db_count_after_rerun = get_product_count(test_db)
            assert db_count_after_rerun == count_run_1, (
                f"Idempotency failed: DB row count increased from {count_run_1} to {db_count_after_rerun}"
            )
            logger.info(f"[RUN_2] Idempotency confirmed: DB count remained exactly {db_count_after_rerun} after second run.")

            # 4. Populate standard output files for project deliverables
            export_catalog_csv(test_db, settings.csv_path, logger)
            # Copy test_db to main db_path
            import shutil
            shutil.copyfile(test_db, settings.db_path)
            logger.info(f"[PART_2] Populated deliverables: {settings.db_path} and {settings.csv_path}")

            logger.info("[PART_2] SUCCESS: Catalog crawl, detail extraction, and idempotency verified successfully!")
        except Exception as exc:
            logger.error(f"[PART_2] Test failed with error: {exc}", exc_info=True)
            raise
        finally:
            context.close()
            browser.close()


def test_catalog_extraction_integration():
    """Pytest entrypoint for automated test suites."""
    run_catalog_extraction_test(headless=False, max_pages=2)


if __name__ == "__main__":
    run_catalog_extraction_test(headless=False, max_pages=2)
