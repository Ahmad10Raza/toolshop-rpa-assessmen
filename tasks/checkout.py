"""Cart, search, and checkout operations for nCare RPA assessment."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.sync_api import Page
from utils.logger import log_business_outcome
from tasks.account import UserProfile


def parse_numeric_currency(raw_text: str) -> float:
    """Parse a currency string (e.g. '$14.15') into a floating-point number."""
    cleaned = re.sub(r"[^\d.]", "", raw_text.strip())
    return float(cleaned) if cleaned else 0.0


def search_catalog(
    page: Page,
    query: str,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> List[Dict[str, str]]:
    """Execute catalog search and validate relevance of returned card titles."""
    log = logger or logging.getLogger("ncare_rpa")
    log.info(f"[SEARCH] Navigating to {base_url} to search for '{query}'...")

    page.goto(base_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    search_input = page.locator("[data-test='search-query']")
    search_input.wait_for(state="visible", timeout=15000)
    search_input.fill(query)

    search_btn = page.locator("[data-test='search-submit']")
    try:
        with page.expect_response(
            lambda r: ("products" in r.url or "search" in r.url) and r.status == 200,
            timeout=15000,
        ):
            search_btn.click()
    except Exception:
        search_btn.click()

    page.wait_for_load_state("networkidle")

    # Collect search results
    cards = page.locator("a.card").all()
    log.info(f"[SEARCH] Found {len(cards)} search result cards for query '{query}'.")

    results = []
    all_relevant = True
    for idx, card in enumerate(cards):
        title = card.locator("[data-test='product-name']").inner_text().strip()
        href = card.get_attribute("href") or ""
        full_url = href if href.startswith("http") else f"{base_url.rstrip('/')}{href}"
        results.append({"title": title, "url": full_url})

        # Validate relevance (case-insensitive substring check)
        if query.lower() in title.lower():
            log.info(f"[SEARCH_RELEVANCE] Card {idx + 1}: '{title}' matches '{query}'")
        else:
            all_relevant = False
            log.warning(f"[SEARCH_RELEVANCE] Card {idx + 1}: '{title}' does not contain search term '{query}'")

    if all_relevant:
        log_business_outcome(
            log,
            action="SEARCH_RELEVANCE",
            outcome="RELEVANT",
            details=f"All {len(results)} search results contain search term '{query}'",
        )
    else:
        log_business_outcome(
            log,
            action="SEARCH_RELEVANCE",
            outcome="MIXED_RELEVANCE",
            details=f"Some search results do not strictly contain '{query}' in title",
        )

    return results


def add_product_to_cart(
    page: Page,
    product_url: str,
    quantity: int = 1,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Navigate to a product detail page, set quantity, and add to shopping cart."""
    log = logger or logging.getLogger("ncare_rpa")
    log.info(f"[CART_ADD] Navigating to {product_url} (quantity={quantity})...")

    page.goto(product_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    product_title = page.locator("[data-test='product-name']").inner_text().strip()

    # Capture initial cart count prior to adding item
    badge_locator = page.locator("[data-test='cart-quantity']")
    initial_badge_text = badge_locator.inner_text().strip() if badge_locator.count() > 0 and badge_locator.is_visible() else "0"
    try:
        initial_count = int(initial_badge_text)
    except ValueError:
        initial_count = 0

    expected_count = initial_count + quantity

    # Adjust quantity if greater than 1
    if quantity > 1:
        qty_input = page.locator("[data-test='quantity']")
        qty_input.wait_for(state="visible", timeout=10000)
        qty_input.fill(str(quantity))
        log.info(f"[CART_ADD] Set quantity input to {quantity} for '{product_title}'.")

    # Click Add to Cart
    add_btn = page.locator("[data-test='add-to-cart']")
    add_btn.wait_for(state="visible", timeout=10000)
    add_btn.click()

    # Synchronize on observable increment of the cart quantity badge
    page.wait_for_function(
        f"() => parseInt(document.querySelector('[data-test=\"cart-quantity\"]')?.innerText || '0') >= {expected_count}",
        timeout=15000,
    )
    current_badge_count = page.locator("[data-test='cart-quantity']").inner_text().strip()
    log.info(f"[CART_ADD] Added '{product_title}' (qty {quantity}) to cart (badge: {current_badge_count})")

    # Dismiss any active toast notification if present so it does not block navigation
    toast_close = page.locator("div.toast button.btn-close, [role='alert'] button")
    if toast_close.count() > 0 and toast_close.first.is_visible():
        try:
            toast_close.first.click()
            log.info("[CART_ADD] Dismissed active confirmation toast overlay.")
        except Exception:
            pass


def navigate_to_cart(
    page: Page,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Navigate directly to the cart / checkout view and wait for cart table rendering."""
    log = logger or logging.getLogger("ncare_rpa")
    checkout_url = f"{base_url.rstrip('/')}/checkout"
    log.info(f"[CART_VIEW] Navigating to {checkout_url}...")

    page.goto(checkout_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)
    log.info("[CART_VIEW] Cart table loaded successfully.")


def validate_cart_items(
    page: Page,
    logger: Optional[logging.Logger] = None,
) -> List[Dict[str, Any]]:
    """Inspect cart table rows, validate price * quantity arithmetic, and return row data."""
    log = logger or logging.getLogger("ncare_rpa")
    log.info("[CART_VALIDATION] Verifying cart line items and calculated totals...")

    rows = page.locator("tbody tr").all()
    validated_items = []
    calculated_subtotal = 0.0

    for idx, row in enumerate(rows):
        cells = row.locator("td").all()
        if len(cells) < 4:
            continue

        item_title = cells[0].inner_text().strip()

        # Quantity input or text in column 2
        qty_input = cells[1].locator("input")
        if qty_input.count() > 0:
            quantity = int(qty_input.input_value() or "1")
        else:
            quantity = int(re.sub(r"\D", "", cells[1].inner_text()) or "1")

        unit_price = parse_numeric_currency(cells[2].inner_text())
        displayed_total = parse_numeric_currency(cells[3].inner_text())
        expected_total = round(unit_price * quantity, 2)

        # Assert mathematical accuracy
        assert abs(displayed_total - expected_total) < 0.02, (
            f"Arithmetic discrepancy for '{item_title}': unit_price ({unit_price}) * "
            f"quantity ({quantity}) = {expected_total}, but table displays {displayed_total}"
        )

        calculated_subtotal += displayed_total
        validated_items.append({
            "index": idx,
            "title": item_title,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": displayed_total,
        })
        log.info(
            f"[CART_ITEM] '{item_title}' | Qty: {quantity} | Unit: ${unit_price:.2f} | "
            f"Total: ${displayed_total:.2f} (Verified)"
        )

    # Validate overall summary total using deterministic data-test attribute
    total_locator = page.locator("[data-test='cart-total']")
    if total_locator.count() > 0 and total_locator.is_visible():
        raw_footer_total = total_locator.inner_text().strip()
        cart_total = parse_numeric_currency(raw_footer_total)
        assert abs(cart_total - calculated_subtotal) < 0.02, (
            f"Cart total mismatch: sum of line items ({calculated_subtotal}) != displayed total ({cart_total})"
        )
        log.info(f"[CART_SUMMARY] Total validated: ${cart_total:.2f} matches sum of line items.")

    return validated_items


def delete_cart_item(
    page: Page,
    item_index: int = 0,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Remove a line item from the cart and verify observable row count decrement."""
    log = logger or logging.getLogger("ncare_rpa")
    initial_rows_count = page.locator("tbody tr").count()
    target_row = page.locator("tbody tr").nth(item_index)
    item_title = target_row.locator("td:first-child").inner_text().strip()

    log.info(f"[CART_DELETE] Removing item at index {item_index}: '{item_title}'...")

    del_btn = target_row.locator("a.btn-danger, button.btn-danger")
    del_btn.wait_for(state="visible", timeout=10000)
    del_btn.click()

    # Synchronize on observable row count decrease
    expected_count = initial_rows_count - 1
    page.wait_for_function(
        f"() => document.querySelectorAll('tbody tr').length === {expected_count}",
        timeout=15000,
    )
    log.info(f"[CART_DELETE] Removed '{item_title}'. Remaining items: {expected_count}")


def proceed_to_checkout_wizard(
    page: Page,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Advance from cart line items review into the multi-step checkout wizard."""
    log = logger or logging.getLogger("ncare_rpa")
    log.info("[CHECKOUT_WIZARD] Advancing from cart items to step 2...")

    proceed_btn = page.locator("[data-test='proceed-1']")
    proceed_btn.wait_for(state="visible", timeout=15000)
    proceed_btn.click()
    page.wait_for_load_state("networkidle")
    log.info("[CHECKOUT_WIZARD] Step 1 complete. Arrived at authentication step.")


def handle_checkout_auth(
    page: Page,
    user: UserProfile,
    base_url: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Ensure user is authenticated in Step 2 of the checkout wizard."""
    log = logger or logging.getLogger("ncare_rpa")
    log.info("[CHECKOUT_AUTH] Verifying user authentication in checkout wizard...")

    # Check if already authenticated
    proceed_2 = page.locator("[data-test='proceed-2']")
    if proceed_2.count() > 0 and proceed_2.is_visible():
        log.info("[CHECKOUT_AUTH] User session already active in wizard. Proceeding to billing address...")
        proceed_2.click()
        page.wait_for_load_state("networkidle")
        return

    # If unauthenticated, submit credentials within the wizard
    login_submit = page.locator("[data-test='login-submit']")
    if login_submit.count() > 0 and login_submit.is_visible():
        log.info(f"[CHECKOUT_AUTH] Submitting credentials for '{user.email}' in wizard...")
        page.locator("[data-test='email']").fill(user.email)
        page.locator("[data-test='password']").fill(user.password)
        login_submit.click()
        page.wait_for_load_state("networkidle")

    # Proceed to billing address
    proceed_2.wait_for(state="visible", timeout=15000)
    proceed_2.click()
    page.wait_for_load_state("networkidle")
    log.info("[CHECKOUT_AUTH] Authenticated and advanced to billing address")


def fill_billing_address(
    page: Page,
    user: UserProfile,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Populate and confirm billing address details in Step 3 of checkout wizard."""
    log = logger or logging.getLogger("ncare_rpa")
    log.info("[CHECKOUT_ADDRESS] Filling billing address fields...")

    country_select = page.locator("[data-test='country']")
    country_select.wait_for(state="visible", timeout=15000)
    country_select.select_option(user.country)

    page.locator("[data-test='house_number']").fill(user.house_number)
    page.locator("[data-test='postal_code']").fill(user.postal_code)
    page.locator("[data-test='street']").fill(user.street)
    page.locator("[data-test='city']").fill(user.city)
    page.locator("[data-test='state']").fill(user.state)

    proceed_3 = page.locator("[data-test='proceed-3']")
    proceed_3.wait_for(state="visible", timeout=10000)
    proceed_3.click()
    page.wait_for_load_state("networkidle")
    log.info("[CHECKOUT_ADDRESS] Billing address confirmed. Advanced to payment step")


def select_payment_and_confirm(
    page: Page,
    artifacts_dir: Path,
    payment_method: str = "Cash on Delivery",
    logger: Optional[logging.Logger] = None,
) -> str:
    """Select payment option, submit order, assert confirmation, and save screenshot."""
    log = logger or logging.getLogger("toolshop_rpa")
    log.info(f"[CHECKOUT_PAYMENT] Selecting payment method: '{payment_method}'...")

    payment_select = page.locator("[data-test='payment-method']")
    payment_select.wait_for(state="visible", timeout=15000)
    payment_select.select_option(label=payment_method)

    finish_btn = page.locator("[data-test='finish']")
    finish_btn.wait_for(state="visible", timeout=10000)
    finish_btn.click()

    # Synchronize on observable order success confirmation
    success_locator = page.locator("[data-test='payment-success-message'], .help-block:has-text('Payment was successful')")
    success_locator.first.wait_for(state="visible", timeout=15000)
    success_msg = success_locator.first.inner_text().strip()
    log.info(f"[CHECKOUT_PAYMENT] Order confirmed: '{success_msg}'")

    # Capture order confirmation screenshot artifact
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = artifacts_dir / "order_confirmation.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    log.info(f"[CHECKOUT_PAYMENT] Saved confirmation screenshot to {screenshot_path}")

    log_business_outcome(
        log,
        action="ORDER_CONFIRMATION",
        outcome="ORDER_CONFIRMED",
        details=f"Payment confirmed via {payment_method}. Screenshot saved.",
    )

    return success_msg


def handle_invoice_download(
    page: Page,
    base_url: str,
    artifacts_dir: Path,
    logger: Optional[logging.Logger] = None,
) -> Optional[Path]:
    """Check for invoice availability and download PDF if provided by application."""
    log = logger or logging.getLogger("ncare_rpa")
    log.info("[INVOICE] Checking for downloadable invoice...")

    # First check active screen for direct invoice download controls
    direct_invoice = page.locator("a:has-text('Invoice'), button:has-text('Invoice'), [data-test*='invoice']")
    if direct_invoice.count() > 0 and direct_invoice.first.is_visible():
        try:
            with page.expect_download(timeout=10000) as download_info:
                direct_invoice.first.click()
            download = download_info.value
            target_file = artifacts_dir / download.suggested_filename
            download.save_as(str(target_file))
            log.info(f"[INVOICE] Downloaded invoice to {target_file}")
            return target_file
        except Exception as exc:
            log.info(f"[INVOICE] Direct invoice download not triggered: {exc}")

    # Second check account invoice history at /account/invoices
    invoices_url = f"{base_url.rstrip('/')}/account/invoices"
    log.info(f"[INVOICE] Checking invoice history at {invoices_url}")
    page.goto(invoices_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    invoice_rows = page.locator("tbody tr")
    if invoice_rows.count() > 0:
        download_btn = invoice_rows.first.locator("a[href*='download'], a[href*='invoice'], button")
        if download_btn.count() > 0 and download_btn.first.is_visible():
            try:
                with page.expect_download(timeout=10000) as download_info:
                    download_btn.first.click()
                download = download_info.value
                target_file = artifacts_dir / download.suggested_filename
                download.save_as(str(target_file))
                log.info(f"[INVOICE] Downloaded invoice from history to {target_file}")
                return target_file
            except Exception as exc:
                log.info(f"[INVOICE] History download attempt: {exc}")

    log.info("[INVOICE] No invoice download available on this account.")
    return None
