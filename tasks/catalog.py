"""Product catalog crawling, dynamic facet discovery, and detail extraction."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from playwright.sync_api import BrowserContext, Page
from utils.database import init_database, upsert_product, export_to_csv, get_product_count


def discover_facets(
    page: Page,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> Tuple[List[str], List[str]]:
    """Dynamically discover available category and brand filter options from sidebar."""
    log = logger or logging.getLogger("toolshop_rpa")
    log.info(f"[CATALOG_DISCOVERY] Navigating to {base_url} to discover dynamic facets...")

    page.goto(base_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    # Locate category labels containing dynamic category checkboxes
    category_labels = page.locator("label:has(input[data-test^='category-'])").all()
    categories = [lbl.inner_text().strip() for lbl in category_labels if lbl.inner_text().strip()]

    # Locate brand labels containing dynamic brand checkboxes
    brand_labels = page.locator("label:has(input[data-test^='brand-'])").all()
    brands = [lbl.inner_text().strip() for lbl in brand_labels if lbl.inner_text().strip()]

    log.info(f"[CATALOG_DISCOVERY] Discovered {len(categories)} categories: {categories[:5]}...")
    log.info(f"[CATALOG_DISCOVERY] Discovered {len(brands)} brands: {brands}")

    return categories, brands


def parse_price(raw_price: str) -> Optional[float]:
    """Extract numeric float from raw price string (e.g. '$14.15' -> 14.15)."""
    cleaned = re.sub(r"[^\d.]", "", raw_price.strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def extract_product_detail(
    page: Page,
    product_url: str,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """Navigate to a product detail page, extract all 5 required fields, and return dict."""
    log = logger or logging.getLogger("ncare_rpa")
    page.goto(product_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    # Product Name
    name_locator = page.locator("[data-test='product-name']")
    name_locator.wait_for(state="visible", timeout=15000)
    product_name = name_locator.inner_text().strip()

    # Product ID extracted from URL slug
    product_id = product_url.rstrip("/").split("/product/")[-1]

    # Unit Price
    price_locator = page.locator("[data-test='unit-price']")
    raw_price = price_locator.inner_text().strip() if price_locator.count() > 0 else ""
    price = parse_price(raw_price)

    # Category badge
    cat_locator = page.locator("span.badge[aria-label='category']")
    category = cat_locator.inner_text().strip() if cat_locator.count() > 0 else None

    # Brand badge
    brand_locator = page.locator("span.badge[aria-label='brand']")
    brand = brand_locator.inner_text().strip() if brand_locator.count() > 0 else None

    # Availability description
    desc_locator = page.locator("[data-test='product-description']")
    desc = desc_locator.inner_text().strip() if desc_locator.count() > 0 else None

    product_data = {
        "product_id": product_id,
        "product_name": product_name,
        "category": category,
        "brand": brand,
        "price": price,
        "availability_description": desc,
        "status": "SUCCESS",
    }
    return product_data


def crawl_catalog(
    context: BrowserContext,
    base_url: str,
    db_path: Path,
    max_pages: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
) -> int:
    """Traverse all catalog pagination pages and extract every product into SQLite."""
    log = logger or logging.getLogger("toolshop_rpa")
    init_database(db_path)

    catalog_page = context.new_page()
    log.info(f"[CRAWLER] Loading catalog homepage: {base_url}")
    catalog_page.goto(base_url, wait_until="domcontentloaded")
    catalog_page.wait_for_load_state("networkidle")

    # Discover and log sidebar facets
    discover_facets(catalog_page, base_url, log)

    current_page_num = 1
    total_extracted = 0

    while True:
        log.info(f"[CRAWLER] Processing catalog page {current_page_num}...")
        catalog_page.locator("a.card").first.wait_for(state="visible", timeout=15000)

        # Collect all product card hrefs on current page
        card_elements = catalog_page.locator("a.card").all()
        card_hrefs = [card.get_attribute("href") for card in card_elements if card.get_attribute("href")]

        log.info(f"[CRAWLER] Page {current_page_num}: Found {len(card_hrefs)} product cards.")

        for href in card_hrefs:
            full_url = href if href.startswith("http") else f"{base_url.rstrip('/')}{href}"
            detail_tab = context.new_page()
            try:
                item = extract_product_detail(detail_tab, full_url, log)
                upsert_product(db_path, item)
                total_extracted += 1
                log.info(f"[EXTRACTED] [{item['product_id']}] {item['product_name']} | Price: {item['price']} | Category: {item['category']}")
            except Exception as exc:
                log.warning(f"[EXTRACT_ERROR] Failed extracting {full_url}: {exc}")
            finally:
                detail_tab.close()

        # Check pagination stop condition
        if max_pages and current_page_num >= max_pages:
            log.info(f"[CRAWLER] Reached requested max_pages limit ({max_pages}). Stopping traversal.")
            break

        # Check if next page button is disabled or missing
        next_li = catalog_page.locator("li:has(button[data-test='pagination-next'])")
        if next_li.count() == 0:
            log.info("[CRAWLER] No pagination container found. Traversal complete.")
            break

        next_class = next_li.get_attribute("class") or ""
        if "disabled" in next_class:
            log.info(f"[CRAWLER] Pagination next button is disabled. Traversal complete at page {current_page_num}.")
            break

        # Advance to next page with network synchronization
        next_btn = catalog_page.locator("button[data-test='pagination-next']")
        try:
            with catalog_page.expect_response(
                lambda r: "products" in r.url and r.status == 200,
                timeout=15000,
            ):
                next_btn.click()
            catalog_page.wait_for_load_state("networkidle")
            current_page_num += 1
        except Exception as exc:
            log.warning(f"[CRAWLER] Pagination transition to next page encountered timeout: {exc}. Ending pagination.")
            break

    catalog_page.close()
    final_count = get_product_count(db_path)
    log.info(f"[CRAWLER] Crawl complete. Stored {final_count} products in database")
    return final_count


def export_catalog_csv(
    db_path: Path,
    csv_path: Path,
    logger: Optional[logging.Logger] = None,
) -> int:
    """Export all stored products from SQLite database to CSV file."""
    log = logger or logging.getLogger("toolshop_rpa")
    count = export_to_csv(db_path, csv_path)
    log.info(f"[CSV_EXPORT] Exported {count} products to {csv_path}")
    return count
