"""Application configuration settings for nCare RPA assessment."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    """Holds configuration parameters with environment variable fallbacks."""
    base_url: str = os.getenv("BASE_URL", "https://practicesoftwaretesting.com")
    headless: bool = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    timeout_ms: int = int(os.getenv("BROWSER_TIMEOUT_MS", "15000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    output_dir: Path = BASE_DIR / "output"
    artifacts_dir: Path = BASE_DIR / "artifacts"
    db_path: Path = BASE_DIR / os.getenv("DB_PATH", "output/products.db")
    csv_path: Path = BASE_DIR / os.getenv("CSV_PATH", "output/products.csv")
    log_file: Path = BASE_DIR / os.getenv("LOG_FILE", "artifacts/run.log")

    # User profile & credentials configuration
    user_first_name: str = os.getenv("USER_FIRST_NAME", "Jane")
    user_last_name: str = os.getenv("USER_LAST_NAME", "Doe")
    user_dob: str = os.getenv("USER_DOB", "1992-04-15")
    user_street: str = os.getenv("USER_STREET", "Industrial Way")
    user_house_number: str = os.getenv("USER_HOUSE_NUMBER", "42")
    user_postal_code: str = os.getenv("USER_POSTAL_CODE", "10001")
    user_city: str = os.getenv("USER_CITY", "New York")
    user_state: str = os.getenv("USER_STATE", "NY")
    user_country: str = os.getenv("USER_COUNTRY", "US")
    user_phone: str = os.getenv("USER_PHONE", "5551234567")
    user_email_prefix: str = os.getenv("USER_EMAIL_PREFIX", "ncare")
    user_email_domain: str = os.getenv("USER_EMAIL_DOMAIN", "example.com")
    user_base_password: str = os.getenv("USER_BASE_PASSWORD", "SecurePass2026!")
    wrong_test_password: str = os.getenv("WRONG_TEST_PASSWORD", "WrongPassword999!")

    # Payment Configuration
    payment_method: str = os.getenv("PAYMENT_METHOD", "Cash on Delivery")
    bank_account_name: str = os.getenv("BANK_ACCOUNT_NAME", "Jane Doe")
    bank_account_number: str = os.getenv("BANK_ACCOUNT_NUMBER", "123456789")

    def ensure_directories(self) -> None:
        """Ensure required output and artifact directories exist on disk."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)


def get_settings(headed_override: bool = False) -> Settings:
    """Return an initialized Settings instance, applying optional CLI overrides."""
    settings = Settings()
    if headed_override:
        settings.headless = False
    settings.ensure_directories()
    return settings
