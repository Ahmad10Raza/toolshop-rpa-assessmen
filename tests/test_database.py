"""Unit tests for SQLite database operations, idempotency, and CSV export."""

import csv
import tempfile
from pathlib import Path
import pytest
from utils.database import (
    init_database,
    upsert_product,
    get_product,
    get_all_products,
    get_product_count,
    export_to_csv,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Fixture providing a temporary SQLite database path."""
    db_file = tmp_path / "test_products.db"
    init_database(db_file)
    return db_file


def test_init_database(temp_db: Path):
    """Verify table creation and empty initial count."""
    count = get_product_count(temp_db)
    assert count == 0


def test_upsert_new_product(temp_db: Path):
    """Verify inserting a new product record."""
    product = {
        "product_id": "01TEST_A",
        "product_name": "Combination Pliers",
        "category": "Pliers",
        "brand": "ForgeFlex Tools",
        "price": 14.15,
        "availability_description": "High quality pliers",
        "status": "SUCCESS",
    }
    upsert_product(temp_db, product)

    assert get_product_count(temp_db) == 1
    stored = get_product(temp_db, "01TEST_A")
    assert stored is not None
    assert stored["product_name"] == "Combination Pliers"
    assert stored["price"] == 14.15
    assert stored["brand"] == "ForgeFlex Tools"


def test_idempotent_upsert_does_not_duplicate(temp_db: Path):
    """Verify that updating an existing product updates the row rather than creating duplicates."""
    initial_product = {
        "product_id": "01TEST_A",
        "product_name": "Initial Pliers",
        "category": "Pliers",
        "brand": "Brand One",
        "price": 10.00,
        "availability_description": "Initial description",
        "status": "SUCCESS",
    }
    upsert_product(temp_db, initial_product)
    assert get_product_count(temp_db) == 1

    # Insert same product_id with changed details
    updated_product = {
        "product_id": "01TEST_A",
        "product_name": "Updated Pliers",
        "category": "Pliers",
        "brand": "Brand One Updated",
        "price": 12.50,
        "availability_description": "Updated description",
        "status": "SUCCESS",
    }
    upsert_product(temp_db, updated_product)

    # Row count must remain 1 (idempotency criterion)
    assert get_product_count(temp_db) == 1

    # Verify updated values
    stored = get_product(temp_db, "01TEST_A")
    assert stored["product_name"] == "Updated Pliers"
    assert stored["price"] == 12.50
    assert stored["brand"] == "Brand One Updated"


def test_export_to_csv(temp_db: Path, tmp_path: Path):
    """Verify CSV export produces valid headers and matching rows."""
    p1 = {
        "product_id": "P01",
        "product_name": "Hammer",
        "category": "Hand Tools",
        "brand": "BrandA",
        "price": 9.99,
        "availability_description": "Steel hammer",
        "status": "SUCCESS",
    }
    p2 = {
        "product_id": "P02",
        "product_name": "Pliers",
        "category": "Hand Tools",
        "brand": "BrandB",
        "price": 14.50,
        "availability_description": "Grip pliers",
        "status": "SUCCESS",
    }
    upsert_product(temp_db, p1)
    upsert_product(temp_db, p2)

    csv_file = tmp_path / "test_export.csv"
    exported_count = export_to_csv(temp_db, csv_file)
    assert exported_count == 2
    assert csv_file.exists()

    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["product_id"] == "P01"
    assert rows[0]["product_name"] == "Hammer"
    assert rows[1]["product_id"] == "P02"
    assert rows[1]["product_name"] == "Pliers"
