import json
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BASE_URL = os.getenv("BASE_URL", "https://practicesoftwaretesting.com").rstrip("/")


def inspect_catalog(page):
    """Inspect catalog, filters, search, and pagination on home page."""
    print("[INFO] Inspecting catalog page...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    # Inspect search controls
    search_input = page.locator("[data-test='search-query']")
    search_btn = page.locator("[data-test='search-submit']")
    print(f"Search input data-test='search-query' visible: {search_input.is_visible()}")
    print(f"  Search button data-test='search-submit' visible: {search_btn.is_visible()}")

    # Inspect filter sidebar
    categories = page.locator("[data-test^='category-']").all()
    print(f"  Found {len(categories)} category filter elements")
    category_names = [cat.inner_text().strip() for cat in categories[:5]]
    print(f"Sample categories: {category_names}")

    brands = page.locator("[data-test^='brand-']").all()
    print(f"  Found {len(brands)} brand filter elements")
    brand_names = [b.inner_text().strip() for b in brands[:5]]
    print(f"Sample brands: {brand_names}")

    # Inspect product cards
    products = page.locator("a.card").all()
    print(f"  Found {len(products)} product card links on current page")
    first_product_url = products[0].get_attribute("href") if products else None
    print(f"First product href: {first_product_url}")

    # Inspect pagination
    pagination = page.locator("ul.pagination")
    print(f"Pagination container visible: {pagination.is_visible()}")
    page_items = page.locator("ul.pagination li.page-item").all()
    print(f"Found {len(page_items)} pagination items")

    return first_product_url


def inspect_register_page(page):
    """Inspect registration form fields and submit button."""
    print("[INFO] Inspecting registration page...")
    page.goto(f"{BASE_URL}/auth/register", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    fields = [
        "first-name",
        "last-name",
        "dob",
        "address",
        "postcode",
        "city",
        "state",
        "country",
        "phone",
        "email",
        "password",
        "register-submit",
    ]
    results = {}
    for f in fields:
        loc = page.locator(f"[data-test='{f}']")
        results[f] = loc.is_visible()
    print(f"Registration fields presence: {json.dumps(results, indent=2)}")


def inspect_login_page(page):
    """Inspect login form fields and alerts."""
    print("[INFO] Inspecting login page...")
    page.goto(f"{BASE_URL}/auth/login", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    fields = ["email", "password", "login-submit"]
    for f in fields:
        loc = page.locator(f"[data-test='{f}']")
        print(f"Login field data-test='{f}' visible: {loc.is_visible()}")


def inspect_product_detail(page, product_href):
    """Inspect product detail elements, quantity, add-to-cart button."""
    if not product_href:
        return
    url = f"{BASE_URL}{product_href}" if product_href.startswith("/") else product_href
    print(f"[INFO] Inspecting product detail page: {url}")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    detail_selectors = {
        "product_name": "[data-test='product-name']",
        "unit_price": "[data-test='unit-price']",
        "description": "[data-test='product-description']",
        "quantity": "[data-test='quantity']",
        "add_to_cart": "[data-test='add-to-cart']",
        "increase_quantity": "[data-test='increase-quantity']",
        "decrease_quantity": "[data-test='decrease-quantity']",
    }
    for name, sel in detail_selectors.items():
        loc = page.locator(sel)
        print(f"Product detail '{name}' ({sel}) visible: {loc.is_visible()}")


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        first_product_url = inspect_catalog(page)
        inspect_register_page(page)
        inspect_login_page(page)
        if first_product_url:
            inspect_product_detail(page, first_product_url)

        browser.close()
        print("[INFO] DOM inspection completed successfully.")


if __name__ == "__main__":
    main()
