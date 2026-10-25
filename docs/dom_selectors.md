# Target Website DOM Structure & Selector Catalog (All Parts 1 to 4)

## Overview
This document catalogs every Document Object Model (DOM) element, selector, and interaction hook on [Practice Software Testing (Toolshop)](https://practicesoftwaretesting.com).

All selectors were extracted and verified by launching Playwright Chromium against the live website and querying rendered elements. The site is an Angular single-page application (SPA).

---

## Global Navigation Elements (Used Across All Parts)

The top navigation bar persists across all pages:

| Element Description | Tag | Verified Locator / Selector | Role / Interaction |
|---|---|---|---|
| Navbar container | `<nav>` | `nav.navbar` | Base header container |
| Brand Home Link | `<a>` | `a.navbar-brand` | Click to return to `/` |
| Home Nav Link | `<a>` | `[data-test="nav-home"]` | Direct anchor to `/` |
| Categories Dropdown | `<a>` | `[data-test="nav-categories"]` | Opens category sub-menu |
| Sign-In Link | `<a>` | `[data-test="nav-sign-in"]` | Navigates to `/auth/login` |
| User Profile Menu | `<a>` | `[data-test="nav-user-menu"]` | Rendered only when signed in |
| Sign-Out Link | `<a>` | `[data-test="nav-sign-out"]` | Located inside user profile menu |
| Cart Link & Counter | `<a>` | `[data-test="nav-cart"]` | Navigates to `/checkout` |
| Cart Item Counter Badge | `<span>` | `[data-test="cart-quantity"]` | Number of items currently in cart |

---

## Part 1: Account Registration, Authentication & 2FA Selectors

### 1.1 Registration Form (`/auth/register`)
The registration form uses split street address fields (`street` and `house_number`) and `postal_code`:

| Form Field | Element Tag | Selector | Value / Action |
|---|---|---|---|
| First Name | `<input type="text">` | `[data-test="first-name"]` | Type first name |
| Last Name | `<input type="text">` | `[data-test="last-name"]` | Type last name |
| Date of Birth | `<input type="date">` | `[data-test="dob"]` | Type date (`YYYY-MM-DD`) |
| Street Address | `<input type="text">` | `[data-test="street"]` | Type street name |
| House Number | `<input type="text">` | `[data-test="house_number"]` | Type house number |
| Postal Code | `<input type="text">` | `[data-test="postal_code"]` | Type postal code |
| City | `<input type="text">` | `[data-test="city"]` | Type city |
| State | `<input type="text">` | `[data-test="state"]` | Type state |
| Country | `<select>` | `[data-test="country"]` | Select option (e.g. `US`) |
| Phone Number | `<input type="tel">` | `[data-test="phone"]` | Type telephone digits |
| Email Address | `<input type="email">` | `[data-test="email"]` | Type generated unique email |
| Password | `<input type="password">` | `[data-test="password"]` | Type account password |
| Register Submit Button | `<button>` | `[data-test="register-submit"]` | Click to submit form |
| Registration Success Alert | `<div>` | `div.alert-success` | Verifies account creation |

### 1.2 Login Form (`/auth/login`)
| Element Description | Element Tag | Selector | Role / Interaction |
|---|---|---|---|
| Email Input | `<input type="email">` | `[data-test="email"]` | Enter registered email |
| Password Input | `<input type="password">` | `[data-test="password"]` | Enter valid or wrong password |
| Login Submit Button | `<button>` | `[data-test="login-submit"]` | Click to submit login |
| Error Alert (Wrong Password) | `<div>` | `div.alert-danger` | Contains `"Invalid email or password"` |
| 2FA Code Input Prompt | `<input type="text">` | `[data-test="totp-code"]` | Appears after password submission |
| 2FA Submit Button | `<button>` | `[data-test="totp-submit"]` | Submits 6-digit TOTP code |
| Account Dashboard Title | `<h1>` | `[data-test="page-title"]` | Contains `"My account"` |

### 1.3 Profile & TOTP Setup Section (`/account/profile`)
| Element Description | Element Tag | Selector | Role / Interaction |
|---|---|---|---|
| Profile Navigation Link | `<a>` | `[data-test="nav-profile"]` | Located in user profile menu |
| Two-Factor Heading | `<h3>` | `h3:has-text("Two-Factor")` | Locates 2FA section |
| Secret Key Text Element | `<span>` / `<div>` | `[data-test="totp-secret"]` or text node | Extracted strictly into memory |
| TOTP Code Input Field | `<input>` | `input[data-test="totp-code"]` | Enter `pyotp.now()` code |
| Enable TOTP Submit Button | `<button>` | `button[data-test="totp-submit"]` | Submits code to verify setup |
| TOTP Success Banner | `<div>` | `div.alert-success` | Contains `"TOTP verified and enabled successfully"` |
| Known UI Quirk Banner | `<div>` | `div.alert-danger` | Contains `"Failed to load TOTP setup details"` (Logged as warning, not failure) |

---

## Part 2: Dynamic Filter Discovery, Recursive Crawl & Catalog Selectors

### 2.1 Dynamic Sidebar Filters (`/`)
Filters are dynamic and must never be hardcoded:

| Filter Element | Element Tag | Selector | Extraction / Interaction |
|---|---|---|---|
| Categories Checkbox Input | `<input type="checkbox">` | `input[data-test^="category-"]` | Checkbox input element |
| Category Name Label | `<label>` | `label:has(input[data-test^="category-"])` | Extract `.inner_text().strip()` |
| Brands Checkbox Input | `<input type="checkbox">` | `input[data-test^="brand-"]` | Checkbox input element |
| Brand Name Label | `<label>` | `label:has(input[data-test^="brand-"])` | Extract `.inner_text().strip()` |
| Filters Reset Button | `<button>` | `[data-test="filters-reset"]` | Clears all applied facet filters |

### 2.2 Product Catalog Grid & Pagination
| Element Description | Element Tag | Selector | Role / Interaction |
|---|---|---|---|
| Product Card Link | `<a>` | `a.card` | Click/navigate to product detail |
| Product Card Title | `<h5>` | `h5[data-test="product-name"]` | Product title on grid card |
| Product Card Price | `<span>` | `span[data-test="product-price"]` | Unit price on grid card |
| Pagination Container | `<ul>` | `ul.pagination` | Bottom pagination container |
| Page Number Links | `<a>` | `ul.pagination li.page-item a` | Specific numbered page |
| Next Page Button | `<a>` | `ul.pagination li.page-item:not(.disabled) a[aria-label="Next"]` | Click to advance to next page |
| Next Page Disabled Check | `<li>` | `ul.pagination li.page-item.disabled a[aria-label="Next"]` | Signals end of catalog traversal |

### 2.3 Product Detail Page (`/product/{id}`)
Extracts the 5 required fields per product:

| Extracted Field | Element Tag | Selector | Extracted Value |
|---|---|---|---|
| 1. Product Name | `<h1>` | `[data-test="product-name"]` | e.g., `Combination Pliers` |
| 2. Category | `<span>` | `span.badge[aria-label="category"]` | e.g., `Pliers` |
| 3. Brand | `<span>` | `span.badge[aria-label="brand"]` | e.g., `ForgeFlex Tools` |
| 4. Price | `<span>` | `[data-test="unit-price"]` | e.g., `14.15` |
| 5. Description | `<p>` | `[data-test="product-description"]` | Full product description string |

---

## Part 3: Search, Cart Operations & Authenticated Checkout Selectors

### 3.1 Search Bar Controls (`/`)
| Control Description | Element Tag | Selector | Action |
|---|---|---|---|
| Search Query Input | `<input type="text">` | `[data-test="search-query"]` | Type `"pliers"` |
| Search Submit Button | `<button>` | `[data-test="search-submit"]` | Click or press Enter |
| Search Reset Button | `<button>` | `[data-test="search-reset"]` | Clears active search filter |

### 3.2 Product Detail Cart Controls (`/product/{id}`)
| Control Description | Element Tag | Selector | Action |
|---|---|---|---|
| Quantity Input Field | `<input type="number">` | `[data-test="quantity"]` | Clear and type quantity (e.g. `3`) |
| Increase Quantity Button | `<button>` | `[data-test="increase-quantity"]` | Click to increment quantity by 1 |
| Decrease Quantity Button | `<button>` | `[data-test="decrease-quantity"]` | Click to decrement quantity by 1 |
| Add to Cart Button | `<button>` | `[data-test="add-to-cart"]` | Click to add item to cart |
| Toast Notification Alert | `<div>` | `div.toast`, `[role="alert"]` | Pop-up confirmation; wait and dismiss |
| Toast Close Button | `<button>` | `div.toast button.btn-close` | Dismisses blocking toast overlay |

### 3.3 Cart Table & Modification (`/checkout`)
| Element Description | Element Tag | Selector | Action |
|---|---|---|---|
| Cart Table Rows | `<tr>` | `tbody tr` | Iterates over each item in cart |
| Line Item Product Title | `<td>` | `tbody tr td:first-child` | Text of product in cart row |
| Line Item Quantity Input | `<input>` | `input[data-test="product-quantity"]` | Value represents current item quantity |
| Line Item Unit Price | `<td>` | `tbody tr td:nth-child(2)` | Displayed unit price |
| Line Item Total | `<td>` | `tbody tr td:nth-child(3)` | Displayed `price * quantity` |
| Delete Item Button | `<button>` / `<a>` | `button.btn-danger`, `a.btn-danger` | Click to remove line item |
| Cart Subtotal Summary | `<td>` | `tfoot tr td:last-child` | Total price of all remaining items |
| Continue Shopping Button | `<a>` | `[data-test="continue-shopping"]` | Returns to catalog |
| Proceed to Checkout Button 1 | `<button>` | `[data-test="proceed-1"]` | Advances to sign-in / address step |

### 3.4 Multi-Step Checkout Wizard
| Wizard Step | Element Description | Selector | Action |
|---|---|---|---|
| **Step 1: Sign-In** | Active session acknowledgement | Handled via existing session | Clicks `[data-test="proceed-2"]` |
| **Step 2: Address** | Street verification field | `[data-test="street"]` | Verify matches registered street |
| **Step 2: Address** | House number field | `[data-test="house_number"]` | Verify matches registered house number |
| **Step 2: Address** | City verification field | `[data-test="city"]` | Verify matches registered city |
| **Step 2: Address** | State verification field | `[data-test="state"]` | Verify matches registered state |
| **Step 2: Address** | Postal code verification field | `[data-test="postal_code"]` | Verify matches registered postal code |
| **Step 2: Address** | Proceed to payment button | `[data-test="proceed-3"]` | Advances to payment step |
| **Step 3: Payment** | Payment method dropdown | `select[data-test="payment-method"]` | Select `"Bank Transfer"` or `"Credit Card"` |
| **Step 3: Payment** | Credit card number field | `[data-test="credit_card_number"]` | Dummy value `4111111111111111` |
| **Step 3: Payment** | Expiration date field | `[data-test="expiration_date"]` | Dummy value `12/2028` |
| **Step 3: Payment** | CVV field | `[data-test="cvv"]` | Dummy value `123` |
| **Step 3: Payment** | Cardholder name field | `[data-test="card_holder_name"]` | Dummy value `Jane Doe` |
| **Step 4: Finish** | Confirm & place order button | `button[data-test="finish"]` | Submits order |
| **Step 4: Confirm** | Order confirmation alert | `[data-test="order-confirmation"]` | Contains `"Payment was successful"` |
| **Step 4: Confirm** | Order ID element | Text containing `ORD-` or order reference | Extracted for invoice lookup |

### 3.5 Bonus: Invoices Page (`/account/invoices`)
| Element Description | Element Tag | Selector | Action |
|---|---|---|---|
| Invoices Table | `<table>` | `table` on `/account/invoices` | Container for invoice rows |
| Invoice Row Matching Order | `<tr>` | `tr:has-text("{order_id}")` | Identifies completed order |
| Invoice Download Link | `<a>` | `a:has-text("Invoice")` | Triggers download of invoice PDF |

---

## Part 4: Reliability Hooks, Observable States & Recovery Anchors

Part 4 defines the selectors and rules for state synchronization and error recovery across all pages:

### 4.1 Observable State Synchronization (Zero Sleep Strategy)
| Desired State | Playwright Locator Strategy | Replaces Unsafe Fixed Sleep |
|---|---|---|
| Page Navigation Settled | `page.wait_for_load_state("networkidle")` | No `time.sleep()` |
| Angular Route Rendered | `page.locator("[data-test='...']").wait_for(state="visible")` | No `wait_for_timeout(3000)` |
| Reactive Toast Dismissed | `page.locator("div.toast").wait_for(state="detached")` | No blind delay before next click |
| Catalog Products Loaded | `page.locator("a.card").first.wait_for(state="visible")` | Waits for grid rendering |
| Item Removed from Cart | `page.locator("tr:has-text('{name}')").wait_for(state="detached")` | Verifies deletion directly in DOM |

### 4.2 Known Anchor URLs for Recovery
When a step encounters an unhandled state, the bot navigates back to a verified anchor URL to re-synchronize:

| Workflow Area | Anchor URL | Observable Anchor Target |
|---|---|---|
| Catalog / Scraping | `https://practicesoftwaretesting.com/` | `page.locator("a.card").first` |
| Authentication | `https://practicesoftwaretesting.com/auth/login` | `page.locator("[data-test='login-submit']")` |
| Shopping Cart | `https://practicesoftwaretesting.com/checkout` | `page.locator("[data-test='proceed-1']")` |
| User Profile | `https://practicesoftwaretesting.com/account/profile` | `page.locator("h3:has-text('Profile')")` |

### 4.3 Diagnostic Failure Artifacts
- Screenshot hook: `page.screenshot(path="artifacts/{step_name}_failure.png", full_page=True)`
- Structured log hook: Writes sanitized context and stack trace to `artifacts/run.log`
