"""Database operations for product catalog persistence and CSV export."""

import csv
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Return a configured SQLite database connection with row factory enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: Path) -> None:
    """Initialize SQLite table for storing extracted catalog products."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT,
        brand TEXT,
        price REAL,
        availability_description TEXT,
        status TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """
    with get_connection(db_path) as conn:
        conn.execute(create_table_sql)
        conn.commit()


def upsert_product(db_path: Path, product: Dict[str, Any]) -> None:
    """Insert or update a product record, ensuring reruns do not duplicate rows."""
    upsert_sql = """
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
    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ON CONFLICT(product_id) DO UPDATE SET
        product_name = excluded.product_name,
        category = excluded.category,
        brand = excluded.brand,
        price = excluded.price,
        availability_description = excluded.availability_description,
        status = excluded.status,
        updated_at = datetime('now');
    """
    with get_connection(db_path) as conn:
        conn.execute(
            upsert_sql,
            (
                str(product["product_id"]),
                str(product["product_name"]),
                product.get("category"),
                product.get("brand"),
                float(product["price"]) if product.get("price") is not None else None,
                product.get("availability_description"),
                product.get("status", "SUCCESS"),
            ),
        )
        conn.commit()


def get_product(db_path: Path, product_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single product by ID, returning a dictionary or None."""
    query_sql = "SELECT * FROM products WHERE product_id = ?;"
    with get_connection(db_path) as conn:
        cursor = conn.execute(query_sql, (product_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_all_products(db_path: Path) -> List[Dict[str, Any]]:
    """Retrieve all stored products ordered by product_id."""
    query_sql = "SELECT * FROM products ORDER BY product_id ASC;"
    with get_connection(db_path) as conn:
        cursor = conn.execute(query_sql)
        return [dict(row) for row in cursor.fetchall()]


def get_product_count(db_path: Path) -> int:
    """Return the total number of unique product rows in the database."""
    query_sql = "SELECT COUNT(*) FROM products;"
    with get_connection(db_path) as conn:
        cursor = conn.execute(query_sql)
        return int(cursor.fetchone()[0])


def export_to_csv(db_path: Path, csv_path: Path) -> int:
    """Export all products from SQLite into a CSV file, returning row count."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    products = get_all_products(db_path)

    fieldnames = [
        "product_id",
        "product_name",
        "category",
        "brand",
        "price",
        "availability_description",
        "status",
        "updated_at",
    ]

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    return len(products)
