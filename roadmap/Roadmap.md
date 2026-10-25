# nCare RPA Developer Take-Home Assignment: Complete Roadmap

Your approach is sensible: **Python + Playwright + Robocorp Framework (RPA Framework)** is a good stack for this assignment. It lets you demonstrate browser automation, Python programming, exception handling, database operations, logging, and end-to-end process design without introducing an unnecessarily complicated architecture.

However, there's one important thing to understand before you start: **the objective is not simply to make the automation work. It is to build something you can explain confidently in your next interview.**

I've reviewed your uploaded assessment. It requires a single-command, unattended automation covering account registration, TOTP-based two-factor authentication, recursive product extraction, SQLite and CSV storage, search, cart operations, checkout, and reliability handling. The evaluator explicitly prioritizes reliability, clean reruns, and the complete 2FA cycle. RPA-TakeHome-Assessment RPA-TakeHome-Assessment

I'll structure the roadmap around five goals:

1. Complete the assignment in a manageable order.
2. Use Playwright and clean automation patterns without unnecessary abstractions.
3. Adhere to production RPA best practices while keeping the implementation understandable and maintainable.
4. Test every stage before moving forward.
5. Deliver a professional repository that you can defend in an interview.

---

## 1. First, understand exactly what you're building

The target website is [Practice Software Testing — Toolshop](https://practicesoftwaretesting.com).

Your automation will behave like a person using the website, but it must execute deterministically through the browser UI.

### The four assignment modules

| Module | What you must implement | Priority |
|---|---|---|
| Part 1: Account lifecycle and 2FA | Register, log in, enable TOTP, test an invalid password, log in using TOTP | Critical |
| Part 2: Product extraction | Discover categories and brands, traverse pagination, extract product details, store data in SQLite and CSV | High |
| Part 3: Shopping workflow | Search for pliers, add products, validate cart, remove an item, complete checkout | High |
| Part 4: Reliability | Logging, screenshots, retries, configuration, headless execution, clean reruns | Critical throughout |

The assignment has a five-day submission window and recommends approximately four to six focused hours. Treat that as the employer's estimate, not a guarantee: you may need additional time to learn Robocorp, understand the website, and troubleshoot the public demo environment. RPA-TakeHome-Assessment

### The most important restrictions

Your implementation must respect these requirements:

- Use the browser UI for every required website interaction.
- Do not call the site's REST API directly.
- Do not use vision-based automation or AI-generated selectors at runtime.
- Discover categories and brands from the website instead of hardcoding their values.
- Generate a fresh TOTP code when needed, using the secret captured during setup.
- Use observable browser states rather than fixed sleeps.
- Retry failed steps by returning to a known page and recovering deliberately.
- Make the automation headless by default, with a flag to watch it run.

These aren't optional design preferences. They are explicit assessment criteria. RPA-TakeHome-Assessment RPA-TakeHome-Assessment

---

# 2. Recommended technology stack

I recommend the following stack for your project.

| Responsibility | Technology | Why it fits |
|---|---|---|
| Programming language | Python | Required by the assessment |
| Browser automation | Playwright | Reliable locators, browser contexts, navigation, downloads |
| RPA framework | Robocorp / RPA Framework | Reusable automation tasks and RPA-oriented project structure |
| TOTP authentication | `pyotp` | Generates time-based one-time passwords |
| Database | SQLite | Built into Python and sufficient for this project |
| CSV export | Python `csv` module | Simple, dependency-light export |
| Configuration | Environment variables and `.env` | Keeps settings out of source code |
| Logging | Python `logging` | Timestamped console and file logs |
| Validation | Python assertions or explicit validation functions | Verifies business outcomes |
| Testing | `pytest` | Tests business logic and data-handling functions |
| Version control | Git | Tracks changes and supports a clean submission |

Useful official references:

- [Playwright for Python](https://playwright.dev/python/)
- [Robocorp documentation](https://robocorp.com/docs)
- [RPA Framework documentation](https://rpaframework.org/)
- [pyotp documentation](https://pyauth.github.io/pyotp/)
- [Python SQLite documentation](https://docs.python.org/3/library/sqlite3.html)

## One architectural decision to make early

**Use Playwright as the browser engine and Robocorp's RPA Framework for selected supporting tasks, where it adds value.**

Do not force every operation through a Robocorp wrapper merely to demonstrate that you used the framework.

For example:
- Playwright: browser navigation, form submission, locators, page validation and downloads.
- Python: TOTP generation, data validation and orchestration.
- SQLite: persistent product records.
- Python logging: execution records and error context.
- RPA Framework: selected file-handling or other RPA-oriented operations, if they simplify the implementation.

Before coding, verify that your chosen Robocorp libraries and Playwright version work together in your Python environment.

Your final implementation should have one entry point, such as `python run.py`, that executes the workflow from start to finish.

---

# 3. Project architecture: Keep it professional but not overengineered

This is where I would be particularly careful.

You want the code to reflect a **competent mid-level Python/RPA developer**: someone who understands functions, modules, reusable browser operations, exception handling, and database interactions.

You do not need enterprise architecture, a complicated dependency injection system, a custom automation engine, or dozens of classes.

## Recommended project structure

Start with this structure:

```text
ncare-rpa-assessment/
│
├── run.py
├── requirements.txt
├── robot.yaml
├── conda.yaml
├── .env.example
├── .gitignore
├── README.md
│
├── config/
│   └── settings.py
│
├── tasks/
│   ├── account.py
│   ├── authentication.py
│   ├── catalog.py
│   └── checkout.py
│
├── utils/
│   ├── browser.py
│   ├── database.py
│   ├── logger.py
│   └── helpers.py
│
├── output/
│   ├── products.db
│   └── products.csv
│
├── artifacts/
│   ├── run.log
│   └── order_confirmation.png
│
└── tests/
    ├── test_authentication.py
    └── test_database.py
```

This is a starting point, not a requirement to create every file immediately. Add modules only when they are useful.

### What each module should do

| File | Responsibility |
|---|---|
| `run.py` | Parse command-line arguments and orchestrate the workflow |
| `config/settings.py` | Read environment variables and application settings |
| `tasks/account.py` | Register a new account and verify registration |
| `tasks/authentication.py` | Handle login, TOTP setup, logout and authentication validation |
| `tasks/catalog.py` | Discover categories and brands, traverse products and extract details |
| `tasks/checkout.py` | Search, cart operations, checkout and order confirmation |
| `utils/browser.py` | Create and configure the Playwright browser |
| `utils/database.py` | Initialize SQLite, upsert product records and export CSV |
| `utils/logger.py` | Configure structured logging |
| `utils/helpers.py` | Shared helpers that are genuinely needed |
| `tests/` | Test isolated business logic and data operations |

**Important:** You can use ordinary Python modules for the automation logic. You do not need to turn every function into a Robocorp task. Use Robocorp's task configuration and execution conventions where they help, but keep the application logic straightforward.

---

# 4. The complete implementation roadmap

I recommend completing the project in nine stages.

The order matters. You should not start by asking an AI agent to generate the entire repository and then spend hours debugging everything simultaneously.

Instead, build one working layer at a time.

## Stage 0 — Analyze the assignment and establish coding rules

**Estimated time: 20–30 minutes**

Before opening your editor, ask your AI coding agent to analyze the requirements and produce a plan.

Do not let it generate the implementation yet.

### Step 1: Break the assignment into individual operations

Your checklist should contain the following.

**Account lifecycle**
- [ ] Generate a unique email address.
- [ ] Register an account with complete details.
- [ ] Verify registration.
- [ ] Log in without 2FA.
- [ ] Open the profile and enable TOTP.
- [ ] Capture the TOTP secret.
- [ ] Generate and submit a valid TOTP code.
- [ ] Handle the known profile-page banner.
- [ ] Log out.
- [ ] Attempt an incorrect password and handle the rejection normally.
- [ ] Log in with the correct password and a fresh TOTP code.

**Product extraction**
- [ ] Discover categories from the filter sidebar.
- [ ] Discover brands from the filter sidebar.
- [ ] Traverse the complete catalog through pagination.
- [ ] Open every product detail page.
- [ ] Extract all five required fields.
- [ ] Save products to SQLite.
- [ ] Export the database contents to CSV.
- [ ] Run the process twice without creating duplicates.

**Shopping workflow**
- [ ] Search for `pliers`.
- [ ] Validate the relevance of each result.
- [ ] Add two different products to the cart.
- [ ] Set one product's quantity to three.
- [ ] Handle toast messages.
- [ ] Validate cart contents, quantities and line totals.
- [ ] Remove one product.
- [ ] Verify its removal.
- [ ] Complete checkout while logged in.
- [ ] Verify the billing address.
- [ ] Select a payment method.
- [ ] Complete the order with dummy details.
- [ ] Capture the order confirmation.
- [ ] Attempt the invoice-download bonus if supported.

**Reliability**
- [ ] Use explicit browser-state waits.
- [ ] Save screenshots on failure.
- [ ] Log failures with context.
- [ ] Retry a failed step once using a known page.
- [ ] Keep credentials out of source code.
- [ ] Run headlessly by default.
- [ ] Support a headed/debug mode.
- [ ] Produce the required deliverables.

This list becomes your acceptance-test checklist.

### Step 2: Establish coding standards and architectural principles

Follow these core software engineering principles throughout implementation:

- Straightforward Python that a developer with roughly one to three years of experience could reasonably maintain.
- Functions with descriptive names and a single clear responsibility.
- Small, reusable helpers rather than unnecessary abstraction.
- Classes only where they provide a practical benefit.
- No decorative comments, emojis, or verbose docstrings explaining obvious code.
- No unnecessary design patterns or heavy frameworks.
- No artificial complexity to make the implementation look sophisticated.
- Explicit error handling at meaningful boundaries.
- Meaningful variable names and consistent formatting.
- Deterministic Playwright locators targeting stable `data-test` attributes.
- No fabricated test results or claims that unexecuted code works.
- Keep credentials and TOTP secrets out of source code and logs. Generate a fresh TOTP code at the moment of authentication.
- Implement explicit validation, structured logging, failure screenshots, safe-anchor recovery, and database upserts.

This prompt gives the agent clear boundaries while keeping you involved in the technical decisions.

---

## Stage 1 — Environment setup and browser smoke test

**Estimated time: 30–45 minutes**

Do not begin with account registration or the database. First establish that the automation environment works.

### Step 1: Create the project directory

```bash
mkdir ncare-rpa-assessment
cd ncare-rpa-assessment

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
```

Since you're working on Ubuntu, this is a straightforward starting point.

### Step 2: Install the required libraries

Start with the following direct dependencies:

```bash
pip install playwright pyotp python-dotenv rpaframework pytest
```

Install the Playwright browser:

```bash
playwright install chromium
```

If the browser reports missing system dependencies, follow the Playwright installation instructions for Linux.

**Robocorp compatibility check:** Before freezing your dependencies, verify that your selected RPA Framework packages and Playwright work with the Python version you intend to use. If Robocorp's task environment introduces compatibility issues, choose a supported Python version rather than trying to force incompatible packages together.

Generate an initial dependency file:

```bash
pip freeze > requirements.txt
```

Review it before submission; a curated dependency file is preferable to including unrelated packages from your environment.

### Step 3: Create a browser smoke test

Your first goal is simply to open the website, confirm that the page loads, and close the browser.

For example:

```python
from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            "https://practicesoftwaretesting.com",
            wait_until="domcontentloaded",
        )

        print("Page title:", page.title())
        print("Current URL:", page.url)

        browser.close()


if __name__ == "__main__":
    main()
```

This is a smoke test, not your final browser architecture.

Run it:

```bash
python smoke_test.py
```

Verify:
- The browser starts successfully.
- The page loads.
- The title and URL are printed.
- The browser closes cleanly.

### Step 4: Inspect the actual website

Before writing locators, inspect the live page using Playwright.

Your AI agent can help you examine the DOM and propose selectors. Verify those selectors against the real page.

For example, use Playwright's locator inspection facilities to examine:
- Registration form fields.
- Login fields.
- Profile navigation.
- TOTP setup elements.
- Product filters.
- Pagination controls.
- Product detail fields.
- Search results.
- Cart controls.
- Checkout fields.

Do not assume the website's current DOM matches an older tutorial or an AI-generated example.

**Stage 1 completion criterion:** You can launch Chromium, access the site, inspect its DOM and run the script reliably.

---

# Stage 2 — Account lifecycle and TOTP authentication

**Estimated time: 60–90 minutes**

This is the most important stage of the assignment.

The employer explicitly calls out the complete 2FA cycle as a major evaluation criterion. Make it work before investing significant time in catalog extraction or checkout.

## 2.1 Generate a unique account for every run

Your account should have a unique email address, a valid password and the complete profile information required by the registration form.

A reasonable approach is to generate an email address using a timestamp or UUID.

For example:

```python
import uuid


def generate_unique_email():
    identifier = uuid.uuid4().hex[:12]
    return f"ncare_{identifier}@example.com"
```

This demonstrates the idea, but `example.com` is a reserved example domain and will not provide a usable inbox.

For the actual assessment, choose a unique address format accepted by the demo site's registration form. Do not assume that every arbitrary email domain will work.

Generate the other profile fields using valid dummy values.

Keep the password in memory or in a protected per-run state file. Do not print it in the logs.

## 2.2 Implement registration

Create a function along these lines:

```python
def register_account(page, account_details):
    ...
```

Its responsibilities should be limited to:
1. Navigate to the registration page.
2. Fill in the required fields.
3. Submit the form.
4. Wait for an observable success condition.
5. Verify that registration succeeded.
6. Return a useful result or raise an appropriate exception.

Do not assume that clicking the submit button means registration succeeded.

Possible success indicators include:
- A confirmation message.
- A redirect to a login page.
- A visible success notification.

Inspect the live website and choose a reliable condition.

## 2.3 Implement normal login

Create a separate function:

```python
def login(page, email, password):
    ...
```

Initially, log in without 2FA.

Verify that you reach the expected account page before proceeding.

Separating login from registration allows you to reuse the same login function later, when TOTP is required.

## 2.4 Enable TOTP

This is the central technical exercise.

The intended flow is:

1. Navigate to the profile page.
2. Locate the TOTP setup section.
3. Read the displayed secret key.
4. Store the secret in memory.
5. Generate a current six-digit TOTP code using `pyotp`.
6. Enter the code in the setup form.
7. Submit it.
8. Verify the success message.
9. Handle the known profile-page banner without incorrectly marking the whole workflow as failed.

The essential Python operation is:

```python
import pyotp

totp = pyotp.TOTP(secret)
code = totp.now()
```

The code changes with time, normally every 30 seconds.

Do not generate the code at the start of the entire workflow and reuse it several minutes later. Generate it immediately before submitting the relevant authentication form.

### Handle the known profile-page issue

The assignment warns that after enabling TOTP, the profile page may display:

`Failed to load TOTP setup details`

This is a known front-end issue.

Your automation should distinguish between:
- The successful TOTP activation confirmation.
- The subsequent profile-page warning.

If the site confirms activation successfully, the warning should be logged as an observed application issue rather than automatically treated as a failed activation.

Do not suppress unrelated errors just because the assessment mentions this particular banner.

## 2.5 Test an incorrect password

Log out, then attempt to log in with the registered email and an incorrect password.

This is an expected business outcome, not an unexpected application failure.

Your logs should distinguish between the two:

```text
INFO | Registration | SUCCESS
INFO | Login | SUCCESS
INFO | TOTP setup | SUCCESS
INFO | Negative login test | EXPECTED_REJECTION
```

These are illustrative log entries, not evidence of an actual run.

The wrong-password attempt should:
- Detect the site's actual rejection message.
- Record the expected rejection.
- Avoid crashing the complete workflow.
- Leave the automation in a known state.

## 2.6 Test login with TOTP

Finally:
1. Log in using the correct credentials.
2. Detect the 2FA prompt.
3. Generate a fresh TOTP code from the captured secret.
4. Submit the code.
5. Verify that you reach the authenticated account page.

Do not mark the stage complete until this final step works.

### Suggested test checklist

| Test | Expected result |
|---|---|
| Register a fresh account | Registration succeeds |
| Login without 2FA | Account page appears |
| Enable TOTP | Site confirms activation |
| Profile shows known banner | Banner is logged; workflow continues when appropriate |
| Wrong password | Rejection detected without crashing |
| Correct password and TOTP | Authenticated account page appears |
| Run again with new account details | A new registration is attempted successfully |

**Stage 2 completion criterion:** The entire account lifecycle works from a clean start, including successful TOTP-protected login.

---

# Stage 3 — Recursive product extraction

**Estimated time: 60–90 minutes**

Once authentication works, implement the catalog extraction module.

The objective is not simply to scrape the product listing page. You must discover categories and brands dynamically, traverse the catalog and visit every product detail page.

## 3.1 Discover categories and brands

Begin at the product catalog.

Inspect the filter sidebar and identify:
- The category filter.
- The brand filter.
- The elements that represent their available options.

Extract the options from the live page.

For example, your functions might be:

```python
def discover_categories(page):
    ...


def discover_brands(page):
    ...
```

These are function contracts, not selectors. The actual locators must be based on the site's DOM.

Do not create a manually maintained list of category or brand names.

You may store the discovered values in the database or log them for debugging.

## 3.2 Traverse the catalog

The assignment explicitly requires walking the catalog through pagination.

Your logic should resemble:

```text
Open catalog
    |
    v
Read current page's product links
    |
    v
Visit each product detail page
    |
    v
Extract required fields
    |
    v
Save or update product in SQLite
    |
    v
Check for another catalog page
    |
    +---- Yes ----> Continue
    |
    +---- No -----> Finish extraction
```

The implementation should not depend on an assumed number of pages.

A robust approach is to:
1. Read the current page's product links.
2. Visit each product detail page.
3. Extract the required fields.
4. Save each record.
5. Return to a known catalog state.
6. Determine whether a next page exists and is enabled.
7. Continue until pagination is exhausted.

If the site provides stable product URLs or identifiers in the page DOM, use them to identify products.

Be careful with browser history and page navigation. Opening a product detail page and returning with the Back button can sometimes restore an unexpected page state. Verify that your catalog pagination position is preserved before proceeding.

## 3.3 Extract the five required fields

Every product record must contain:

| Field | Meaning |
|---|---|
| `product_name` | Displayed product name |
| `category` | Product category |
| `brand` | Product brand |
| `price` | Product price |
| `availability_description` | Availability or description information required by the assessment |

The assessment uses the wording **availability/description**. Inspect the product detail page and determine how the site presents that information.

If the site does not provide one of the fields for a particular product, handle it explicitly rather than silently fabricating a value.

Also, normalize prices consistently. Store prices in a suitable numeric representation, such as integer minor units or a fixed-precision decimal representation, rather than relying on floating-point arithmetic for financial values.

## 3.4 Implement SQLite storage

The assessment allows you to choose the schema.

A practical starting point is:

```sql
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT,
    brand TEXT,
    price TEXT,
    availability_description TEXT,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

Here, `product_id` should represent a stable identifier obtained from the actual product page or a stable product URL.

The `status` field can track the processing outcome, for example:
- `SUCCESS`
- `FAILED`

You can refine the schema after inspecting the website.

The important requirement is that the same product should not create a new database row every time the automation runs.

Use SQLite's `INSERT ... ON CONFLICT DO UPDATE` pattern to update an existing product.

Conceptually:

```sql
INSERT INTO products (
    product_id,
    product_name,
    category,
    brand,
    price,
    availability_description,
    status,
    updated_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(product_id) DO UPDATE SET
    product_name = excluded.product_name,
    category = excluded.category,
    brand = excluded.brand,
    price = excluded.price,
    availability_description = excluded.availability_description,
    status = excluded.status,
    updated_at = excluded.updated_at;
```

This is the foundation of an idempotent extraction process.

### One important detail about failed products

If a product fails to load, consider how you record the failure.

Do not overwrite a previously valid product record with empty data merely because a later extraction attempt failed.

You can log the failed attempt separately or maintain a dedicated extraction-status record. For this assignment, choose the simplest design that preserves valid data and clearly records failures.

## 3.5 Export CSV

After extraction, export the stored records to a CSV file.

Use the database as the source of truth, rather than building the CSV from a separate in-memory list that could become inconsistent with SQLite.

Your expected outputs might look like:

```text
output/
├── products.db
└── products.csv
```

Use a predictable schema and column order.

## 3.6 Test idempotency

Run the extraction twice.

Compare the results.

For example:

```sql
SELECT COUNT(*) FROM products;
```

Then check whether duplicate product IDs exist:

```sql
SELECT product_id, COUNT(*)
FROM products
GROUP BY product_id
HAVING COUNT(*) > 1;
```

The second query should return no rows.

The total row count should remain stable if the catalog has not changed and all products are being processed successfully.

If the catalog changes between runs, the count may legitimately change.

**Stage 3 completion criterion:** The catalog is discovered dynamically, products are extracted through browser navigation, the data is saved correctly, and rerunning the extraction does not duplicate products.

---

# Stage 4 — Search and cart operations

**Estimated time: 45–60 minutes**

Now implement the shopping workflow.

This stage is easier to debug if account authentication and catalog extraction are already working.

## 4.1 Search for pliers

Enter the search term:

```text
pliers
```

Submit the search and wait for the actual results to appear.

Extract the displayed product names and validate relevance.

A simple validation might normalize case and whitespace and then check whether the term appears in the product name.

However, be careful: the assignment asks you to verify that every result is relevant, not merely to check whether the exact string appears in the title.

For this assessment, implement a deterministic rule that is easy to explain. Record any suspicious result for review rather than using a runtime AI model to classify products.

Your log might contain:

```text
INFO | Search | Query: pliers
INFO | Search validation | Result count: <actual count>
```

Replace the placeholder with the real result count during execution.

## 4.2 Select two different products

Choose two distinct products from the actual website.

Before adding them to the cart, capture:
- Product identifier or URL.
- Displayed name.
- Unit price.
- Requested quantity.

Use one product with quantity three.

For example, your internal order data could have this structure:

```python
cart_items = [
    {
        "product_id": "actual-product-id-1",
        "quantity": 3,
    },
    {
        "product_id": "actual-product-id-2",
        "quantity": 1,
    },
]
```

These identifiers are illustrative. Use real products discovered during execution.

## 4.3 Add the products to the cart

For each product:
1. Open the product detail page.
2. Set the quantity where the site supports it.
3. Add the product to the cart.
4. Detect and handle any toast or confirmation banner.
5. Verify the action succeeded.

Avoid assuming that a successful click guarantees a successful addition.

## 4.4 Validate the cart

Open the cart and compare the actual state against the intended state.

Validate:
- Product identity.
- Quantity.
- Unit price.
- Line total.
- Any displayed subtotal, where appropriate.

For a simple line item:

\[
\text{Expected line total} =
\text{Unit price} \times \text{Quantity}
\]

Account for the website's displayed currency precision and any applicable rounding.

Do not simply assert that the cart page is visible.

## 4.5 Remove one product

Remove one of the two products.

Then verify:
- The removed product no longer appears.
- The remaining product is still present.
- The remaining quantity is correct.
- The cart total has been recalculated appropriately.

**Stage 4 completion criterion:** Search validation, two-product cart handling, quantity validation and removal all work reliably.

---

# Stage 5 — Checkout and order confirmation

**Estimated time: 45–60 minutes**

This stage must use the account created earlier.

The assessment specifically asks you to check out while logged in, confirm the billing address, select a payment method and complete an order with dummy details.

## 5.1 Verify the billing address

Read the billing address presented at checkout.

Compare it with the address used during registration.

Normalize harmless differences such as surrounding whitespace, but do not silently ignore meaningful discrepancies.

If the website requires a billing-address selection or additional address entry, implement the flow based on the actual page.

## 5.2 Select a payment method

Inspect the available payment options.

Select a method supported by the practice site and complete the form using appropriate dummy details.

Do not assume a particular payment provider or form structure without inspecting the page.

If the demo site behaves unexpectedly, record the issue and investigate before changing your automation.

## 5.3 Complete the order

After submitting checkout, wait for an observable confirmation.

Capture:
- Order confirmation text.
- Order number, if provided.
- Confirmation page URL.
- Any other information useful for verifying success.

Save the relevant confirmation evidence in `artifacts/` or another clearly documented output location.

## 5.4 Implement the invoice bonus

If time permits:
1. Navigate to the account's invoices page.
2. Locate the order you just created.
3. Verify the order appears.
4. Download the invoice if the site offers it.
5. Save the file under `artifacts/`.

Use Playwright's download handling and wait for the actual download event.

Do not fabricate an invoice or claim that a download succeeded if the site does not provide the functionality.

**Stage 5 completion criterion:** The automation reaches a genuine order confirmation and preserves useful evidence of the completed checkout.

---

# Stage 6 — Implement reliability across the application

**Estimated time: 45–60 minutes**

Reliability should be introduced early, but this is the stage where you systematically verify it across all modules.

The assessment explicitly states that reliability matters as much as the happy path. RPA-TakeHome-Assessment

## 6.1 Replace fixed sleeps with observable waits

Avoid this pattern:

```python
page.wait_for_timeout(5000)
```

It waits for five seconds regardless of whether the page is ready.

Prefer observable conditions:

```python
page.get_by_role(
    "heading",
    name="My Account",
).wait_for(state="visible", timeout=10000)
```

Use locators appropriate to the real page.

Other useful conditions include:
- A URL change.
- A button becoming enabled.
- A success message becoming visible.
- A product list appearing.
- A dialog closing.
- A download event occurring.

Use `networkidle` only when it is appropriate. Some sites maintain connections or background requests that make it an unreliable general-purpose readiness condition.

The goal is to wait for the state you actually need.

## 6.2 Implement structured logging

Create a reusable logging configuration that writes to:
- The console.
- A log file.

Include timestamps, severity, step names and meaningful outcomes.

For example:

```text
2026-10-24 12:00:00 INFO Registration started
2026-10-24 12:00:05 INFO Registration succeeded
2026-10-24 12:00:08 INFO Login succeeded
2026-10-24 12:00:12 INFO TOTP setup succeeded
2026-10-24 12:00:20 INFO Invalid password rejected as expected
```

These are example entries, not actual execution records.

Never log:
- Passwords.
- TOTP secrets.
- Current TOTP codes.
- Session tokens.
- Other sensitive authentication data.

## 6.3 Screenshot on failure

When a browser step fails:
1. Capture the current URL.
2. Record the failing operation.
3. Save a screenshot in `artifacts/`.
4. Log the exception and relevant context.
5. Attempt recovery according to the retry policy.

Give screenshots useful filenames, such as:

```text
artifacts/
├── registration_failure.png
├── totp_login_failure.png
└── checkout_failure.png
```

These names illustrate a possible convention. Generate files only when the corresponding event occurs.

## 6.4 Retry once using a known page

The assessment does not want you to blindly repeat the last action.

Suppose the product extraction step fails because the browser is no longer on the expected page.

A sensible recovery procedure would be:
1. Record the failure.
2. Navigate back to the known catalog URL.
3. Wait for the catalog to become visible.
4. Re-establish the current product or pagination state.
5. Retry the operation once.
6. Mark the operation as failed if the retry also fails.

Do not use one universal recovery function that blindly replays arbitrary browser actions.

Registration, payment submission and order creation deserve particular care: repeating a non-idempotent action may create duplicate accounts or orders.

For these operations, check the observable state before deciding whether a retry is safe.

## 6.5 Separate expected outcomes from failures

This distinction is particularly important in an RPA interview.

| Event | Classification |
|---|---|
| Incorrect password rejected | Expected business outcome |
| Product page returns missing data | Extraction failure or validation failure |
| Known TOTP banner appears after successful activation | Known application issue |
| Cart quantity differs from requested quantity | Business validation failure |
| Browser crashes unexpectedly | Technical failure |
| Invoice download is not offered | Bonus unavailable, not necessarily a core failure |

A well-designed automation does not treat every unexpected business result as a Python exception, and it does not suppress genuine technical failures.

## 6.6 Headless mode and debugging mode

The default should be headless.

Support a command-line flag for visible browser execution.

For example:

```bash
python run.py
```

And:

```bash
python run.py --headed
```

This is a useful interview detail because it demonstrates that you have considered both unattended execution and interactive debugging.

---

# Stage 7 — Integrate the modules into a single workflow

**Estimated time: 30–45 minutes**

At this stage, the individual modules should work independently.

Now connect them through `run.py`.

Your orchestration should be easy to read.

Conceptually:

```text
Start application
    |
    v
Load configuration
    |
    v
Initialize logging and database
    |
    v
Launch browser
    |
    v
Register account
    |
    v
Log in and enable TOTP
    |
    v
Test invalid-password rejection
    |
    v
Log in using TOTP
    |
    v
Extract and persist product catalog
    |
    v
Export CSV
    |
    v
Search and validate pliers
    |
    v
Perform cart operations
    |
    v
Complete checkout
    |
    v
Capture order confirmation
    |
    v
Attempt invoice bonus
    |
    v
Close browser and report outcome
```

### Important implementation decision

Do not let a single exception handler swallow every error and then continue as if the entire workflow succeeded.

Instead:
- Recover from failures when recovery is appropriate.
- Stop when a critical prerequisite cannot be satisfied.
- Record optional failures without misrepresenting the overall result.
- Always clean up browser resources.

For example, a failed TOTP login should normally prevent the authenticated shopping workflow from proceeding.

An unavailable invoice download should not necessarily invalidate an otherwise successful checkout.

### Configuration

Use environment variables for settings such as:

```text
BASE_URL
HEADLESS
OUTPUT_DIR
ARTIFACTS_DIR
DATABASE_PATH
LOG_LEVEL
```

You can store non-secret defaults in a settings module.

Keep `.env` out of version control and provide a `.env.example` containing placeholders.

Do not hardcode credentials or the TOTP secret in source files.

---

# Stage 8 — Testing and rerun validation

**Estimated time: 45–60 minutes**

This stage distinguishes a script that happened to work once from a reliable automation.

## 8.1 Test individual functions

Write a small number of focused tests for logic that does not require the live website.

For example:

**Authentication-related tests**
- A valid secret produces a six-digit TOTP code.
- Missing configuration is handled correctly.
- A fresh code is requested when authentication occurs.

**Database tests**
- A product can be inserted.
- Updating the same product does not create a duplicate.
- A failed extraction does not erase a previous valid record.
- CSV export produces the expected columns.

**Data-validation tests**
- Search results are evaluated consistently.
- Prices are normalized correctly.
- Required fields are validated.

Use a temporary SQLite database for unit tests so you do not accidentally overwrite your actual run output.

## 8.2 Test the complete workflow

Run the project from a clean state.

Check the following:

| Scenario | Expected behavior |
|---|---|
| Fresh execution | Creates a new account and completes the required workflow |
| Incorrect password | Logs the expected rejection |
| Successful TOTP authentication | Reaches the account page |
| Product extraction | Visits the catalog and detail pages |
| Duplicate product encountered | Updates the existing record |
| Browser failure | Saves diagnostic information and attempts recovery |
| Headless execution | Completes without requiring manual interaction |
| Headed execution | Makes browser activity visible for debugging |
| Missing optional invoice functionality | Records the limitation without inventing a successful download |

## 8.3 Verify database idempotency separately

The account workflow and catalog workflow have different rerun requirements.

A fresh run must generate a new account because the demo database resets periodically.

The product database, however, must update existing product records instead of duplicating them.

Therefore, do not confuse:
- **Account uniqueness:** each run needs fresh registration details.
- **Product idempotency:** repeated extraction should not create duplicate product records.

You should test both behaviors independently.

## 8.4 Validate output files

After a successful run, verify that the repository contains the required deliverables:

```text
output/
├── products.db
└── products.csv

artifacts/
├── run.log
├── screenshots-if-any
└── invoice-if-available
```

You can use different filenames if your README documents them clearly.

The assessment asks for the source code, README, requirements file, SQLite output, CSV output and log file. It also encourages retaining useful failure artifacts. RPA-TakeHome-Assessment

---

# Stage 9 — README, Git repository and submission

**Estimated time: 30–45 minutes**

The final repository should be easy for a reviewer to set up and run.

## README structure

Include these sections:

1. Project overview.
2. Features implemented.
3. Technology stack.
4. Prerequisites.
5. Installation instructions.
6. Configuration.
7. How to run.
8. Headless and headed execution.
9. Project structure.
10. Database schema and idempotency.
11. Logging, screenshots and recovery behavior.
12. Known issues and limitations.
13. Production storage of TOTP secrets.
14. Testing instructions.

### The required TOTP production-storage answer

The assessment explicitly asks where the TOTP secret should be stored in production and who should be able to read it.

A good answer should explain that the secret is a sensitive authentication credential and should be stored in an approved secrets manager or secure credential vault, protected by encryption and access controls.

Access should be limited to the specific service identity or authorized personnel who require it. Access should be auditable, and the secret should not appear in source control, plaintext logs or ordinary application configuration.

For a production RPA deployment, you could discuss using the organization's approved credential vault, such as the credential-management capabilities of its RPA platform or an enterprise secrets manager.

The important principle is **least-privilege access**, not simply moving the secret into a different file.

## Git submission checklist

Before submitting, verify that:

- [ ] All required source files are included.
- [ ] `requirements.txt` is present.
- [ ] `README.md` contains setup and execution instructions.
- [ ] `.env` is excluded from Git.
- [ ] Credentials and TOTP secrets are absent from source files and logs.
- [ ] The SQLite database is included.
- [ ] The CSV export is included.
- [ ] The execution log is included.
- [ ] Useful screenshots and invoice evidence are retained when available.
- [ ] The single-command entry point works.
- [ ] No test output or README claim is fabricated.

You can use a private Git repository or a ZIP archive, depending on the employer's submission instructions.

---

# 5. A realistic implementation schedule

Because the assessment suggests four to six focused hours, I would prioritize the work rather than spend equal time on every module.

For someone learning the framework while building the project, a longer schedule may be more realistic.

| Session | Focus | Deliverable |
|---|---|---|
| 1 | Requirement analysis, environment setup, browser inspection | Working browser smoke test |
| 2 | Registration, normal login and profile navigation | Working account lifecycle foundation |
| 3 | TOTP setup, invalid-password handling and TOTP login | Complete Part 1 |
| 4 | Dynamic discovery, pagination and product detail extraction | Working catalog scraper |
| 5 | SQLite upserts and CSV export | Persistent, deduplicated catalog |
| 6 | Search, cart validation and removal | Working Part 3 shopping operations |
| 7 | Checkout, confirmation and invoice bonus | Completed order workflow |
| 8 | Recovery, logging, screenshots and integration | Reliable single-command run |
| 9 | Final regression, README and packaging | Submission-ready repository |

These are planning sessions rather than fixed time estimates. Combine them where the implementation is straightforward, and allocate more time to the website behaviors that actually cause problems.

**My priority order would be: Part 1 first, then Part 2, then Part 3, with reliability built into each stage and a final integration pass at the end.**

Do not leave logging, screenshots and error handling entirely until the final hour.

---

# 6. How to work with your AI coding agent effectively

This is probably the most important part of your implementation strategy.

You already plan to use an AI agent for writing code. That is reasonable, but the way you direct it will determine whether the project becomes easier or harder.

Use the following loop for every stage.

### Step A — Ask for analysis

Before generating code, ask the agent to identify:
- The relevant page elements.
- The inputs and outputs of the function.
- The expected success condition.
- The likely failure conditions.
- The appropriate retry behavior.

### Step B — Ask for the smallest implementation

Do not ask it to build the whole project.

Ask for one module or one clearly defined function at a time.

### Step C — Inspect the code yourself

Check:
- Whether the imports are valid.
- Whether selectors exist on the actual page.
- Whether the function has a clear responsibility.
- Whether errors are handled correctly.
- Whether credentials could leak into logs.
- Whether it has introduced unnecessary dependencies.

### Step D — Run the code

Execute the actual command and observe the result.

Do not accept a response saying that the code should work as proof that it works.

### Step E — Ask the agent to explain the implementation

For each important function, you should be able to answer:

1. What does this function do?
2. What arguments does it receive?
3. What does it return?
4. Which browser state does it expect?
5. How does it determine success?
6. What happens when the operation fails?
7. Can it be safely retried?

If you cannot answer these questions, pause before moving forward.

### Step F — Commit the working stage

Once the stage passes its tests, commit it to Git.

For example:

```bash
git add .
git commit -m "Implement account registration and login"
```

Use a separate commit for each meaningful stage.

This gives you a history of your design decisions and makes regressions easier to diagnose.

---

# 7. What your AI agent must avoid

Here is the more detailed coding policy I would give your agent after the initial analysis.

| Avoid | Prefer |
|---|---|
| One enormous `run.py` containing every operation | Small modules with clear responsibilities |
| A class for every simple function | Functions for simple operations |
| A generic framework for all possible website failures | Explicit recovery for the failure modes that matter |
| Fixed sleeps after every click | Waits for the required observable state |
| Catching every exception and continuing | Handling known failures and propagating critical errors |
| Repeating the last action blindly | Returning to a known state and verifying what happened |
| Repeated database inserts | Stable product identifiers and upserts |
| Hardcoded category and brand lists | Dynamic discovery from the website |
| Credentials in source code | Environment configuration and protected secret storage |
| Logging authentication secrets | Logging step names, outcomes and sanitized context |
| Artificially elaborate comments | Short explanations where the reasoning is not obvious |
| Complex inheritance and unnecessary design patterns | Straightforward composition and reusable functions |
| Fake successful test output | Actual execution results and honest reporting |
| Selectors invented without inspecting the DOM | Locators verified against the live website |

One more point: **do not optimize the code for looking human; optimize it for being understandable, maintainable and defensible.**

A mid-level developer can write clean code without using complicated patterns. Your implementation should reflect that.

---

# 8. Interview preparation: Be ready to explain your own project

Since you are applying for an RPA Developer position, the project can become a strong interview discussion if you understand the engineering decisions.

Prepare answers to these questions while you implement the corresponding stages.

### Python and architecture
1. Why did you separate the automation into modules?
2. Why did you use functions instead of creating many classes?
3. How does the main script orchestrate the workflow?
4. How do you propagate and handle exceptions?

### Playwright
5. Why did you choose Playwright?
6. What is the difference between a locator and an element handle?
7. How do you wait for a page to become ready?
8. How do you handle dynamic content?
9. How do you capture a screenshot when a step fails?
10. How do you debug an automation that works in headed mode but fails headlessly?

### TOTP and security
11. How does TOTP work?
12. Why does the code change every 30 seconds?
13. Why should the code be generated at login time?
14. Why must the TOTP secret be protected?
15. How do you distinguish an incorrect password from an automation failure?

### Data extraction and databases
16. How do you discover categories and brands dynamically?
17. How do you know that you have processed every catalog page?
18. What makes the database operation idempotent?
19. Why use a stable product identifier?
20. Why use SQLite instead of storing everything in CSV?

### Reliability and RPA design
21. How do you implement retries?
22. Why is blindly retrying a checkout operation dangerous?
23. How would you prevent duplicate orders?
24. What happens if the browser crashes midway through the extraction?
25. How would you adapt the project for an enterprise RPA deployment?

You do not need to memorize perfect answers in advance. Build each feature, then explain why you implemented it that way.

That approach will make the answers much easier to remember.

---

# 9. Final recommendation: What you should do first

Do not start with all four parts simultaneously.

Your first milestone should be:

**A working Python environment, a Playwright browser test, and a verified understanding of the website's actual DOM.**

Then move directly to the account lifecycle and TOTP authentication.

The reason is simple: the 2FA cycle is explicitly emphasized by the evaluator, and the remaining shopping workflow depends on being able to authenticate successfully.

Once Part 1 works, you will have a stable foundation for the rest of the assignment.

One final caution: your goal is not to produce the maximum amount of code. It is to produce a complete, reproducible and understandable automation. A smaller implementation that reliably meets the requirements is stronger than a larger implementation that only works on the happy path.

**Your immediate next action:** Open your coding agent in the project directory and give it the initial analysis prompt from Stage 0. Have it inspect the requirements and propose the implementation plan without writing code yet. Review that plan before authorizing the browser smoke test and the first implementation stage.