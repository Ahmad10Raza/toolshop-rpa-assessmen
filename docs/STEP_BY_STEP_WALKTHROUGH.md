# End-to-End Automation Step-by-Step Walkthrough Guide

## Purpose of this Guide
This document explains exactly what this automation bot does on `https://practicesoftwaretesting.com` from start to finish. It breaks down every single action, screen, click, and verification step across all four parts of the assessment in plain, practical terms so anyone can follow along.

---

## High-Level Story: What Happens When You Run the Automation

When you run `python run.py`, you can sit back and watch the browser perform four distinct operational phases:

1. **Part 1 (Account Lifecycle & 2FA):** The bot creates a brand-new user account with a unique email, logs in, turns on Two-Factor Authentication (TOTP), tests an intentional wrong password to verify security rejection, and then logs in successfully using a freshly generated 6-digit TOTP code.
2. **Part 2 (Catalog Discovery & Extraction):** The bot goes to the home page, dynamically discovers all product categories and brands from the filter sidebar, clicks through every page of the catalog, opens every single product detail page, extracts 5 key data fields, saves them into an SQLite database (`output/products.db`), and exports a clean CSV file (`output/products.csv`). If you run it again, it updates existing records instead of creating duplicate rows.
3. **Part 3 (Search, Cart & Checkout):** The bot searches for `"pliers"`, verifies that all returned items are actually pliers, adds two different products to the cart (setting one of them to quantity 3), dismisses any pop-up toast messages, goes to the cart to check all quantities and prices, removes one product, proceeds to checkout under the logged-in account, verifies the billing address matches the registration data, submits dummy payment details, captures the order confirmation, and downloads the PDF invoice to `artifacts/`.
4. **Part 4 (Reliability throughout):** The bot never uses blind pauses (`time.sleep`). If an unexpected failure occurs, it takes a screenshot, logs the technical context, returns to a known safe page (like `/` or `/auth/login`), and retries once.

---

## Part 1: Account Lifecycle with Two-Factor Authentication (TOTP)

### Step 1.1: Generate Fresh Test Credentials
- **What happens:** The bot generates a random unique email address (e.g., `user_a1b2c3d4@example.com` using a UUID) and valid personal details (name, date of birth, address, phone number, password).
- **Why:** The practice website database resets periodically, so hardcoded credentials would eventually fail. Generating a unique account ensures every run starts completely fresh.

### Step 1.2: Navigate to Registration & Fill the Form
- **URL:** `https://practicesoftwaretesting.com/auth/register`
- **Actions:**
  1. The bot navigates to `/auth/register`.
  2. It locates each form field and types the user information:
     - First Name (`[data-test="first-name"]`) -> e.g., `Jane`
     - Last Name (`[data-test="last-name"]`) -> e.g., `Doe`
     - Date of Birth (`[data-test="dob"]`) -> e.g., `1992-04-10`
     - Street (`[data-test="street"]`) -> e.g., `Industrial Way`
     - House Number (`[data-test="house_number"]`) -> e.g., `100`
     - Postal Code (`[data-test="postal_code"]`) -> e.g., `90210`
     - City (`[data-test="city"]`) -> e.g., `Beverly Hills`
     - State (`[data-test="state"]`) -> e.g., `CA`
     - Country (`[data-test="country"]`) -> selects `US`
     - Phone (`[data-test="phone"]`) -> e.g., `3105550199`
     - Email (`[data-test="email"]`) -> generated email
     - Password (`[data-test="password"]`) -> strong password
  3. The bot clicks the `"Register"` button (`[data-test="register-submit"]`).
  4. It waits for the browser to redirect to `/auth/login` or display a success banner (`div.alert-success`).

### Step 1.3: Initial Login (Without 2FA)
- **URL:** `https://practicesoftwaretesting.com/auth/login`
- **Actions:**
  1. The bot types the registered email and password.
  2. It clicks the `"Login"` button (`[data-test="login-submit"]`).
  3. It verifies that the user reaches the account dashboard by checking for the `"My account"` heading (`[data-test="page-title"]`).

### Step 1.4: Enable Two-Factor Authentication (TOTP)
- **URL:** `https://practicesoftwaretesting.com/account/profile`
- **Actions:**
  1. The bot navigates to the Profile page (`/account/profile`).
  2. It scrolls to the Two-Factor Authentication section.
  3. It extracts the raw TOTP secret key string displayed on the screen (the text next to the QR code).
  4. It stores this secret string strictly in memory (never written to disk or logs).
  5. It immediately feeds the secret into the Python `pyotp` library:
     `code = pyotp.TOTP(secret).now()`
  6. The bot enters the generated 6-digit code into the verification input (`input[data-test="totp-code"]`).
  7. It clicks the submit button (`[data-test="totp-submit"]`).
  8. It waits for the confirmation banner: `"TOTP verified and enabled successfully"`.
  9. **Known Front-End Bug Handling:** After activation, the profile page sometimes displays a warning banner stating `"Failed to load TOTP setup details"`. The bot detects this alert, logs an `[INFO]` message noting the known website bug, and continues without treating it as a failure.

### Step 1.5: Logout
- **Actions:**
  1. The bot clicks the user menu dropdown in the top navbar (`[data-test="nav-user-menu"]`).
  2. It clicks `"Sign out"` (`[data-test="nav-sign-out"]`).
  3. It verifies that the navbar now shows `"Sign in"` (`[data-test="nav-sign-in"]`).

### Step 1.6: Negative Test - Deliberate Incorrect Password
- **URL:** `https://practicesoftwaretesting.com/auth/login`
- **Actions:**
  1. The bot attempts to log in using the correct registered email, but an intentionally wrong password (`WrongPassword999!`).
  2. It clicks `"Login"`.
  3. It waits for the website error alert (`div.alert-danger`) displaying `"Invalid email or password"`.
  4. It logs this result as a business rule verification:
     `[INFO] [AUTH_NEGATIVE_TEST] EXPECTED_REJECTION: Site rejected invalid password as expected`
  5. It ensures this rejection does not crash the script, because it is an expected business outcome.

### Step 1.7: Successful Login with 2FA
- **URL:** `https://practicesoftwaretesting.com/auth/login`
- **Actions:**
  1. The bot enters the registered email and the correct password, then clicks `"Login"`.
  2. The website detects that 2FA is active and displays the second-factor prompt asking for the 6-digit code (`[data-test="totp-code"]`).
  3. The bot calculates a **brand-new, fresh** 6-digit code right at that exact second:
     `code = pyotp.TOTP(secret).now()`
  4. It enters the code and submits the form.
  5. It waits for the `"My account"` dashboard to appear, proving that the full 2FA authentication cycle is 100% functional.

---

## Part 2: Dynamic Discovery & Recursive Product Extraction

### Step 2.1: Dynamic Discovery of Filters (No Hardcoding)
- **URL:** `https://practicesoftwaretesting.com`
- **Actions:**
  1. The bot navigates to the home page.
  2. It inspects the filter sidebar on the left side of the screen.
  3. It finds all category checkboxes (`input[data-test^="category-"]`) and reads the text from their parent labels (e.g., `Hammer`, `Hand Saw`, `Wrench`, `Pliers`, `Chisels`).
  4. It finds all brand checkboxes (`input[data-test^="brand-"]`) and reads their labels (e.g., `ForgeFlex Tools`, `MightyCraft Hardware`).
  5. It logs the discovered categories and brands to prove they were discovered dynamically from the live DOM rather than hardcoded.

### Step 2.2: Recursive Crawling Through Pagination
- **Actions:**
  1. The bot begins on Catalog Page 1.
  2. It reads all product card links on the current page (`a.card`).
  3. For every product on the page:
     - The bot opens the product detail page (e.g., `/product/01M5PBBY1D6ZP1C5K1V398XS1D`).
     - It waits for the product information to render.
     - It extracts the 5 required fields:
       * **Product Name:** from `[data-test="product-name"]`
       * **Category:** from `span.badge[aria-label="category"]`
       * **Brand:** from `span.badge[aria-label="brand"]`
       * **Price:** from `[data-test="unit-price"]`
       * **Availability / Description:** from `[data-test="product-description"]`
     - It derives a unique `product_id` (from the URL or card identifier).
     - It upserts the record into the SQLite database (`output/products.db`).
     - It navigates back to the catalog or opens the next product URL.
  4. Once all products on the current page are extracted, the bot checks the pagination controls at the bottom (`ul.pagination`).
  5. If the `"Next"` button (`a[aria-label="Next"]`) is active and not disabled, the bot clicks it, waits for the next set of product cards to load, and repeats the extraction.
  6. When the last page is reached, pagination stops.

### Step 2.3: SQLite Storage & Idempotency
- **Actions:**
  1. Every product is inserted using SQLite's upsert syntax:
     ```sql
     INSERT INTO products (product_id, product_name, category, brand, price, availability_description, status, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, 'SUCCESS', datetime('now'))
     ON CONFLICT(product_id) DO UPDATE SET
         product_name=excluded.product_name,
         category=excluded.category,
         brand=excluded.brand,
         price=excluded.price,
         availability_description=excluded.availability_description,
         updated_at=datetime('now');
     ```
  2. If the script is run a second time, it updates the existing records instead of inserting duplicate rows.

### Step 2.4: CSV Export
- **Actions:**
  1. After the catalog crawl finishes, the bot reads all rows from `output/products.db`.
  2. It writes them out cleanly to `output/products.csv` with standard column headers.

---

## Part 3: Search, Cart Operations & Authenticated Checkout

### Step 3.1: Search for "pliers" & Relevance Validation
- **URL:** `https://practicesoftwaretesting.com`
- **Actions:**
  1. The bot navigates to the home page.
  2. It types `"pliers"` into the search input (`[data-test="search-query"]`).
  3. It clicks the search button (`[data-test="search-submit"]`).
  4. It waits for the search results grid to update.
  5. It iterates through all returned products and checks whether each product's title contains the word `"plier"` or `"pliers"` (case-insensitive).
  6. If a product matches, it logs an confirmation; if any product does not contain the term, it logs a warning identifying the non-matching item.

### Step 3.2: Add Two Different Products to Cart (One with Quantity 3)
- **Actions:**
  1. **Product 1 (Quantity 3):**
     - The bot opens the detail page of the first selected product (e.g., `Combination Pliers`).
     - It sets the quantity input (`[data-test="quantity"]`) to `3` (either by typing `3` or clicking the increase button twice).
     - It clicks the `"Add to cart"` button (`[data-test="add-to-cart"]`).
     - **Toast Handling:** A pop-up toast message appears in the corner (`div.toast` / alert) saying the item was added. The bot explicitly waits for this toast and dismisses it so it does not block subsequent clicks.
  2. **Product 2 (Quantity 1):**
     - The bot opens the detail page of a second, different product (e.g., `Bolt Cutters` or `Slip Joint Pliers`).
     - It leaves the default quantity at `1`.
     - It clicks `"Add to cart"`.
     - It waits for and handles the toast confirmation.

### Step 3.3: Cart Validation & Item Deletion
- **URL:** `https://practicesoftwaretesting.com/checkout`
- **Actions:**
  1. The bot clicks the cart icon in the top navbar (`[data-test="nav-cart"]`) or navigates to `/checkout`.
  2. It inspects the line items table (`tbody tr`):
     - It verifies that Product 1 has quantity `3` and its line total equals `unit_price * 3`.
     - It verifies that Product 2 has quantity `1` and its line total equals `unit_price * 1`.
     - It verifies that the cart subtotal matches the sum of the two line totals.
  3. **Delete One Item:**
     - The bot clicks the delete/trash button (`button.btn-danger` or `a.btn-danger`) next to Product 2.
     - It waits for Product 2 to disappear from the DOM.
     - It verifies that the remaining table contains only Product 1 with quantity 3, and that the subtotal has automatically recalculated.

### Step 3.4: Authenticated Checkout Wizard
- **Actions:**
  1. **Step 1 (Proceed from Cart):**
     - The bot clicks `"Proceed to checkout"` (`[data-test="proceed-1"]`).
  2. **Step 2 (Sign-in Check):**
     - The site checks if the user is signed in. Because the bot is already authenticated from Part 1, it confirms the active session and clicks `"Proceed to checkout"` (`[data-test="proceed-2"]`).
  3. **Step 3 (Billing Address Verification):**
     - The checkout page displays the billing address fields (`street`, `house_number`, `city`, `state`, `postal_code`).
     - The bot reads these fields and compares them against the user profile generated in Part 1.
     - It asserts that the address matches and logs a confirmation:
       `[INFO] [CHECKOUT_ADDRESS] VERIFIED: Billing address matches registered user details`
     - It clicks `"Proceed to checkout"` (`[data-test="proceed-3"]`).
  4. **Step 4 (Payment Method Selection):**
     - The bot selects a payment method from the dropdown (`select[data-test="payment-method"]`), such as `"Bank Transfer"` or `"Credit Card"`.
     - If required by the method, it fills standard dummy payment details (e.g., dummy card number `4111111111111111`, expiration, CVV).
     - It clicks the finish/confirm button (`button[data-test="finish"]`).
  5. **Step 5 (Order Confirmation):**
     - The bot waits for the confirmation screen displaying `"Payment was successful"` or `[data-test="order-confirmation"]`.
     - It extracts the generated Order ID string.
     - It saves a full-page confirmation screenshot to `artifacts/order_confirmation.png`.

### Step 3.5: Bonus - Invoice Download
- **URL:** `https://practicesoftwaretesting.com/account/invoices`
- **Actions:**
  1. The bot navigates to the account's invoices page.
  2. It locates the row matching the newly completed order.
  3. If an invoice download button/link is provided by the site, the bot hooks Playwright's download event (`page.expect_download()`), clicks the link, and saves the file to `artifacts/invoice_{order_id}.pdf`.
  4. If the demo endpoint does not provide an invoice download, the bot logs an informative message and moves on without failing the core checkout.

---

## Part 4: Reliability Requirements Applied Across All Steps

Reliability is not a separate step at the end; it runs actively inside every part of the automation:

### 1. Zero Fixed Sleeps
- The bot never uses `time.sleep(5)` or `page.wait_for_timeout(3000)`.
- It always waits for observable browser conditions:
  - Element visibility: `locator.wait_for(state="visible")`
  - URL route changes: `page.wait_for_url(...)`
  - Network quiescence: `page.wait_for_load_state("networkidle")`

### 2. Failure Screenshots
- If any action fails unexpectedly, a global handler immediately captures a screenshot of the exact browser state and saves it to `artifacts/{step_name}_failure.png`.

### 3. One-Step Known-Anchor Recovery
- Rather than blindly clicking the same broken button repeatedly, the bot logs the issue, navigates back to a known stable page (e.g., `/` for catalog, `/auth/login` for auth, `/checkout` for cart), verifies that the page is loaded, and retries the operation once.

### 4. Structured Dual Logging
- Every single step outputs a timestamped log to both the terminal console and `artifacts/run.log`.
- Format: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [module] Message`
- Expected business outcomes (like an incorrect password being rejected) are clearly distinguished from technical errors.

### 5. Headless by Default with Debug Flag
- Running `python run.py` executes quietly in headless mode.
- Running `python run.py --headed` opens the visible browser window so you can watch every click in real time.

---

## Summary Mapping Table

| Assessment Part | Key Pages Visited | Critical Action Performed | Verified Outcome |
|---|---|---|---|
| **Part 1** | `/auth/register`, `/auth/login`, `/account/profile` | Register user, turn on TOTP, test bad password, log in with TOTP | Reaches account dashboard with 2FA active |
| **Part 2** | `/`, `/product/{id}` | Discover filters, crawl pagination, extract 5 fields per product | `output/products.db` (upserted) and `output/products.csv` |
| **Part 3** | `/`, `/product/{id}`, `/checkout`, `/account/invoices` | Search "pliers", add 2 items (qty 3 on one), verify cart, complete checkout | Order confirmed, screenshot saved, invoice downloaded |
| **Part 4** | Global (all pages) | State waits, failure screenshots, anchor retries, dual logging | Reliable, unattended single-command run (`python run.py`) |
