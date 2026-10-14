"""
Database layer for NovaCart.

Uses plain sqlite3 (no ORM) to keep things simple and easy to read for
students, while still following good practice: a single connection helper,
parameterised queries everywhere, and a clear schema definition.
"""
import csv
import sqlite3

from config import Config

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    original_price INTEGER NOT NULL,
    discount_pct INTEGER NOT NULL DEFAULT 0,
    discounted_price INTEGER NOT NULL,
    rating REAL NOT NULL DEFAULT 0,
    reviews INTEGER NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    tags TEXT,
    description TEXT,
    image TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    city TEXT,
    pincode TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE IF NOT EXISTS wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id INTEGER,
    customer_name TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    pincode TEXT NOT NULL,
    phone TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    subtotal INTEGER NOT NULL,
    gst INTEGER NOT NULL,
    delivery_fee INTEGER NOT NULL,
    grand_total INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Confirmed',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);
"""


def get_connection():
    """Return a new sqlite3 connection with row access by column name."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(reset=False):
    """
    Create tables if they don't exist and seed the products table from the
    CSV dataset. Safe to call every time the app starts.
    """
    import os
    import shutil

    # Automatic safety backup before any schema or data sync
    if os.path.exists(Config.DATABASE_PATH):
        backup_path = Config.DATABASE_PATH + ".backup"
        if not os.path.exists(backup_path):
            try:
                shutil.copy2(Config.DATABASE_PATH, backup_path)
            except Exception:
                pass

    conn = get_connection()
    cur = conn.cursor()

    if reset:
        cur.executescript(
            "DROP TABLE IF EXISTS order_items;"
            "DROP TABLE IF EXISTS orders;"
            "DROP TABLE IF EXISTS wishlist;"
            "DROP TABLE IF EXISTS cart;"
            "DROP TABLE IF EXISTS products;"
            "DROP TABLE IF EXISTS users;"
        )

    cur.executescript(SCHEMA)
    conn.commit()

    _migrate_schema(conn)

    # Sync products if products table has fewer items than the expanded CSV or reset requested
    csv_count = 0
    try:
        with open(Config.PRODUCTS_CSV, newline="", encoding="utf-8") as f:
            csv_count = max(0, sum(1 for _ in f) - 1)
    except Exception:
        csv_count = 0

    row_count = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if row_count < csv_count or reset:
        _seed_products(conn)

    _seed_admin(conn)

    conn.close()


def _table_columns(conn, table):
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _migrate_schema(conn):
    """
    Upgrade older database.db tables in place, adding new columns
    so existing user profiles and orders are preserved.
    """
    user_cols = _table_columns(conn, "users")
    if "password_hash" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    for col in ("phone", "address", "city", "state", "pincode"):
        if col not in user_cols:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")

    order_cols = _table_columns(conn, "orders")
    if "user_id" not in order_cols:
        conn.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER")
    if "state" not in order_cols:
        conn.execute("ALTER TABLE orders ADD COLUMN state TEXT")

    conn.commit()


def _seed_products(conn):
    """Load datasets/products.csv into the products table via upsert."""
    with open(Config.PRODUCTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                int(row["id"]),
                row["name"],
                row["brand"],
                row["category"],
                int(row["original_price"]),
                int(row["discount_pct"]),
                int(row["discounted_price"]),
                float(row["rating"]),
                int(row["reviews"]),
                int(row["stock"]),
                row["tags"],
                row["description"],
                row["image"],
            )
            for row in reader
        ]

    conn.executemany(
        """INSERT OR REPLACE INTO products
           (id, name, brand, category, original_price, discount_pct,
            discounted_price, rating, reviews, stock, tags, description, image)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    print(f"[NovaCart] Synchronized {len(rows)} products in database.")


def _seed_admin(conn):
    """Seed default admin user if not present."""
    from werkzeug.security import generate_password_hash
    cur = conn.cursor()
    row = cur.execute("SELECT id FROM users WHERE email = 'admin@novacart.com'").fetchone()
    if not row:
        pw_hash = generate_password_hash("admin123")
        cur.execute(
            """INSERT INTO users (name, email, password_hash, phone, address, city, state, pincode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("NovaCart Admin", "admin@novacart.com", pw_hash, "9876543210", "NovaCart HQ", "Mumbai", "Maharashtra", "400001")
        )
        conn.commit()
        print("[NovaCart] Default admin user initialized (admin@novacart.com).")


