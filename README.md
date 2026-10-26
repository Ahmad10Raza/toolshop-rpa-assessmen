# Toolshop RPA Automation

Automated end-to-end Python RPA bot for [Practice Software Testing (Toolshop)](https://practicesoftwaretesting.com). Built with Playwright, PyOTP for 2FA handling, and SQLite for structured data persistence.

---

## Demo Video


https://github.com/user-attachments/assets/7e6584be-ada1-42c5-980d-1da6a3354b66

> **Backup Link:** [Watch / Download HD Demo on Google Drive](https://drive.google.com/file/d/1JIciahGe4bJuEBCI4yPwzIhq3ldo-WKS/view?usp=sharing)

---

## Quick Start

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Google Chrome or Chromium

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/Ahmad10Raza/toolshop-rpa-assessmen.git
cd toolshop-rpa-assessmen

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies and Playwright browser
pip install -r requirements.txt
playwright install chromium

# Copy environment variables
cp .env.example .env
```

### 3. Run the Bot
```bash
# Default unattended run (headless)
python run.py

# Visible run (opens maximized browser window with human-observable pacing)
python run.py --headed

# Fast run (crawls only 2 catalog pages)
python run.py --headed --max-pages 2

# Run unit tests
pytest tests/test_database.py tests/test_utilities.py
```

---

## What the Bot Does

The automation runs sequentially from start to finish without manual input:

1. **Part 1 — Account Registration & 2FA:**
   - Generates a fresh, unique user profile (`testuser_<timestamp>@example.com`).
   - Fills the registration form and validates account creation.
   - Logs in with password only, opens the profile page, reads the TOTP secret into memory, computes the 6-digit verification code with `pyotp`, and activates 2FA.
   - Logs out, submits a wrong password to verify rejection is captured as a normal business outcome, then logs in successfully with correct credentials and a freshly computed TOTP code.

2. **Part 2 — Catalog Scraping & Persistence:**
   - Discovers dynamic categories and brands directly from sidebar filters (no hardcoding).
   - Traverses pagination page by page, opening product details in secondary tabs to extract titles, categories, brands, prices, and descriptions.
   - Performs idempotent upserts into SQLite (`output/products.db`) and exports all records to CSV (`output/products.csv`).

3. **Part 3 — Search, Cart & Checkout:**
   - Searches for `"pliers"` and verifies all returned cards match the query.
   - Adds 2 different products to the cart (one with quantity 3, one with quantity 1) and handles toast popups.
   - Opens `/checkout` and verifies that unit prices multiplied by quantities match the displayed line totals and cart grand total.
   - Removes the first item from the cart and verifies table totals recalculate properly.
   - Completes the 4-step checkout wizard, enters matching billing address details, selects the payment method configured in `.env`, confirms the order, and saves `artifacts/order_confirmation.png`.
   - Checks invoice history for downloadable PDF attachments.

---

## Production TOTP Storage Defense

> **Assessment Prompt Question:** *Where would the secret be stored in production, and who should be able to read it?*

In a production enterprise deployment, TOTP shared secrets should never be committed to source code, hardcoded in configuration files, or written to log files. They should be stored in an enterprise secrets manager (such as AWS Secrets Manager, HashiCorp Vault, or CyberArk) with KMS envelope encryption.

At runtime, the unattended RPA worker authenticates using short-lived IAM machine roles or mTLS certificates, fetches the secret directly into volatile memory, computes the instantaneous one-time passcode, and immediately discards the in-memory secret. Access policies must enforce least privilege so only the specific automated execution role can read the secret, with audit logging (e.g., AWS CloudTrail) tracking every access request.

---

## Key Design & Reliability Decisions

- **No Fixed Sleeps:** The bot contains zero `time.sleep()` calls. Synchronization relies entirely on observable DOM and network states: `wait_for(state="visible")`, URL route changes, Angular API responses (`page.expect_response`), and navbar badge count changes (`page.wait_for_function`).
- **Safe-Anchor Recovery (Part 4):** Rather than blindly clicking a failing element in a loop, `utils/retry.py` captures a failure screenshot to `artifacts/`, re-navigates to a clean anchor URL (such as `/auth/login`) to reset the DOM state, and retries the action once.
- **Idempotent Data Handling:** Database writes use SQLite `INSERT ... ON CONFLICT(product_id) DO UPDATE`. Rerunning the bot updates existing rows rather than creating duplicate product entries.
- **Multi-Tab Catalog Crawl:** Product detail pages are opened in secondary browser tabs and closed immediately. This keeps the main catalog tab pinned to its active pagination state and avoids expensive full-page reloads.
- **Deterministic Selectors:** All interactions target stable `data-test` attributes (e.g. `[data-test="search-query"]`, `[data-test="add-to-cart"]`, `[data-test="payment-success-message"]`).

---

## Demo Site Quirks Handled Gracefully

1. **Profile TOTP Banner Quirk:** After activating 2FA, the demo site occasionally renders a false `"Failed to load TOTP setup details"` banner due to an internal state reload. The bot detects this banner, logs it factually as an expected front-end quirk, and moves on without crashing.
2. **Invoice History Behavior:** The demo Toolshop backend does not automatically generate downloadable PDF invoice files for simulated demo purchases. The bot checks `/account/invoices`, logs the availability status cleanly, and proceeds.
3. **Periodic Demo Database Resets:** Because the demo database wipes test accounts periodically, the bot is self-contained: each run registers its own fresh user, sets up 2FA, and builds cart state from scratch.

---

## Repository Structure

```
.
├── run.py                       # CLI orchestrator (runs Part 1, 2, 3A, 3B end to end)
├── config/
│   └── settings.py              # Settings dataclass and .env loader
├── tasks/
│   ├── account.py               # User generation and account registration
│   ├── authentication.py        # Login, TOTP activation, logout, negative tests
│   ├── catalog.py               # Filter discovery, pagination crawl, CSV export
│   └── checkout.py              # Search, cart math validation, checkout wizard
├── utils/
│   ├── database.py              # SQLite connection, idempotent upsert, CSV export
│   ├── logger.py                # Console and artifacts/run.log dual logger
│   └── retry.py                 # Safe-anchor retry recovery and screenshot capture
├── tests/
│   ├── test_database.py         # Unit tests for SQLite schema and upsert logic
│   ├── test_utilities.py        # Unit tests for settings, logger, and retry engine
│   ├── test_account_lifecycle.py # Integration test for Part 1
│   ├── test_catalog_extraction.py # Integration test for Part 2
│   ├── test_search_and_cart.py   # Integration test for Part 3A
│   └── test_checkout_workflow.py # Integration test for Part 3B
├── output/
│   ├── products.db              # Scraped SQLite catalog database
│   └── products.csv             # 1-to-1 CSV export of catalog records
├── artifacts/
│   ├── run.log                  # Execution log with timestamped business outcomes
│   ├── order_confirmation.png   # Full-page screenshot of confirmed order
│   └── toolshop_demo.mp4        # Compressed HD video demo
├── docs/
│   ├── STEP_BY_STEP_WALKTHROUGH.md # Step-by-step implementation guide
│   └── dom_selectors.md         # Catalog of verified DOM selectors
├── .env.example                 # Configuration template
├── requirements.txt             # Project dependencies
└── pytest.ini                   # Pytest configuration
```

---

## Configuration Variables (`.env`)

| Variable | Default Value | Description |
|---|---|---|
| `BASE_URL` | `https://practicesoftwaretesting.com` | Target website root URL |
| `HEADLESS` | `true` | Browser mode (`true` or `false`) |
| `BROWSER_TIMEOUT_MS` | `15000` | Default Playwright locator timeout (ms) |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`INFO`, `DEBUG`) |
| `DB_PATH` | `output/products.db` | Destination SQLite database file path |
| `CSV_PATH` | `output/products.csv` | Destination CSV export file path |
| `LOG_FILE` | `artifacts/run.log` | Persistent log file path |
| `USER_FIRST_NAME` | `Jane` | Test user first name |
| `USER_LAST_NAME` | `Doe` | Test user last name |
| `USER_EMAIL_PREFIX` | `ncare` | Prefix for unique dynamic registration emails |
| `USER_EMAIL_DOMAIN` | `example.com` | Domain for generated test accounts |
| `USER_BASE_PASSWORD` | `SecurePass2026!` | Password used for registered test user |
| `WRONG_TEST_PASSWORD`| `WrongPassword999!` | Invalid password used for negative assertion |
| `PAYMENT_METHOD` | `Cash on Delivery` | Payment method (`Cash on Delivery`, `Bank Transfer`) |
| `BANK_ACCOUNT_NAME` | `Jane Doe` | Account name when selecting Bank Transfer |
| `BANK_ACCOUNT_NUMBER` | `1234567890` | Account number when selecting Bank Transfer |
