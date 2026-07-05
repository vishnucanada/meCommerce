"""Database layer — SQLite stores for products and users.

Maps to the "Databases" group in mock-diagram.png:
  * products.db  -> the product catalog (stands in for the NoSQL store)
  * users.db     -> the users table (the SQL "Users and Orders" store)

Both files live in this folder and are created + seeded with mock data on
startup (see init_databases / count_users). They're gitignored because they're
generated. Services never touch SQL directly — they call the functions here, so
the storage engine can change without editing a service.

A fresh connection is opened per call. That's the simplest thing that is safe
across FastAPI's threadpool (SQLite connections aren't shareable between
threads) and is perfectly fine at mock scale.
"""
import pathlib
import sqlite3

DB_DIR = pathlib.Path(__file__).resolve().parent
PRODUCTS_DB = DB_DIR / "products.db"
USERS_DB = DB_DIR / "users.db"

# --- Mock seed data ------------------------------------------------------
# The catalog that used to live in backend/data.py now seeds products.db.
SEED_PRODUCTS = [
    {"id": "uji", "name": "Uji Ceremonial", "region": "Kyoto · Uji",
     "grade": "ceremonial", "gradeLabel": "Ceremonial", "price": 32,
     "notes": "Sweet, deep umami, no bitterness", "label": "#eaf0d6", "dot": "#4b6b1f"},
    {"id": "okumidori", "name": "Okumidori Reserve", "region": "Kyoto · Wazuka",
     "grade": "ceremonial", "gradeLabel": "Ceremonial", "price": 38,
     "notes": "Creamy, floral, vivid green", "label": "#e2ecd0", "dot": "#3d5c18"},
    {"id": "yame", "name": "Yame Premium", "region": "Fukuoka · Yame",
     "grade": "premium", "gradeLabel": "Premium", "price": 26,
     "notes": "Balanced, nutty, smooth finish", "label": "#edf1dd", "dot": "#6a8a30"},
    {"id": "nishio", "name": "Nishio Daily", "region": "Aichi · Nishio",
     "grade": "premium", "gradeLabel": "Premium", "price": 22,
     "notes": "Bright, grassy, everyday cup", "label": "#eef2df", "dot": "#7a9a3e"},
    {"id": "culinary", "name": "Culinary Blend", "region": "Kagoshima",
     "grade": "culinary", "gradeLabel": "Culinary", "price": 18,
     "notes": "Bold, for lattes and baking", "label": "#e6ecd4", "dot": "#556b28"},
    {"id": "barista", "name": "Barista Latte", "region": "Uji blend",
     "grade": "culinary", "gradeLabel": "Culinary", "price": 20,
     "notes": "Rich, froths well, latte-ready", "label": "#e9efd8", "dot": "#607d2c"},
]


def _connect(path: pathlib.Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


# --- Schema + seeding ----------------------------------------------------
def init_databases() -> None:
    """Create tables if missing and seed products with mock data (idempotent)."""
    conn = _connect(PRODUCTS_DB)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS products (
                   id         TEXT PRIMARY KEY,
                   name       TEXT NOT NULL,
                   region     TEXT NOT NULL,
                   grade      TEXT NOT NULL,
                   gradeLabel TEXT NOT NULL,
                   price      INTEGER NOT NULL,
                   notes      TEXT NOT NULL,
                   label      TEXT NOT NULL,
                   dot        TEXT NOT NULL
               )"""
        )
        (existing,) = conn.execute("SELECT COUNT(*) FROM products").fetchone()
        if existing == 0:
            conn.executemany(
                """INSERT INTO products
                   (id, name, region, grade, gradeLabel, price, notes, label, dot)
                   VALUES (:id, :name, :region, :grade, :gradeLabel, :price, :notes, :label, :dot)""",
                SEED_PRODUCTS,
            )
        conn.commit()
    finally:
        conn.close()

    conn = _connect(USERS_DB)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id            TEXT PRIMARY KEY,
                   username      TEXT UNIQUE NOT NULL,
                   password_hash TEXT NOT NULL,
                   created_at    TEXT NOT NULL
               )"""
        )
        conn.commit()
    finally:
        conn.close()


# --- Products ------------------------------------------------------------
def query_products(grade: str | None = None) -> list[dict]:
    conn = _connect(PRODUCTS_DB)
    try:
        if grade and grade != "all":
            rows = conn.execute(
                "SELECT * FROM products WHERE grade = ? ORDER BY rowid", (grade,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM products ORDER BY rowid").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_product(product_id: str) -> dict | None:
    conn = _connect(PRODUCTS_DB)
    try:
        row = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# --- Users ---------------------------------------------------------------
def count_users() -> int:
    conn = _connect(USERS_DB)
    try:
        (n,) = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return n
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    conn = _connect(USERS_DB)
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def insert_user(user: dict) -> None:
    """Insert a user row. Raises sqlite3.IntegrityError if the username exists."""
    conn = _connect(USERS_DB)
    try:
        conn.execute(
            """INSERT INTO users (id, username, password_hash, created_at)
               VALUES (:id, :username, :password_hash, :created_at)""",
            user,
        )
        conn.commit()
    finally:
        conn.close()


def list_users() -> list[dict]:
    conn = _connect(USERS_DB)
    try:
        rows = conn.execute(
            "SELECT id, username, created_at FROM users ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
