"""
User data-access helpers for authentication and profile management.
Passwords are never stored in plain text — only a salted hash
(werkzeug's generate_password_hash, which ships with Flask already).
"""
from werkzeug.security import generate_password_hash, check_password_hash

from app.database import get_connection


def _row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    d.pop("password_hash", None)  # never leak the hash to templates/session
    return d


def create_user(name, email, password, phone="", address="", city="", state="", pincode=""):
    """Creates a new user with a hashed password. Returns the new user id."""
    password_hash = generate_password_hash(password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO users (name, email, password_hash, phone, address, city, state, pincode)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, email.lower().strip(), password_hash, phone, address, city, state, pincode),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None  # includes password_hash for login check


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def email_exists(email):
    return get_user_by_email(email) is not None


def verify_password(user_row, password):
    """user_row must include password_hash (i.e. came from get_user_by_email)."""
    if not user_row or not user_row.get("password_hash"):
        return False
    return check_password_hash(user_row["password_hash"], password)


def update_profile(user_id, name, phone, address, city, state, pincode):
    conn = get_connection()
    conn.execute(
        """UPDATE users SET name = ?, phone = ?, address = ?, city = ?, state = ?, pincode = ?
           WHERE id = ?""",
        (name, phone, address, city, state, pincode, user_id),
    )
    conn.commit()
    conn.close()
