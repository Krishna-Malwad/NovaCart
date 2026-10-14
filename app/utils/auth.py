"""
Session-based authentication helpers.

Once a user logs in, we store their user_id in the Flask session (the same
signed cookie already used for cart/wishlist). This keeps the whole app
consistent — no separate token system needed for a project of this size.
"""
import re
from functools import wraps

from flask import session, redirect, url_for, request, flash

from app.models.user import get_user_by_id
from config import Config

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_user(user_id):
    session["user_id"] = user_id
    session.modified = True


def logout_user():
    session.pop("user_id", None)
    session.modified = True


def current_user():
    """Returns the logged-in user's dict, or None if not logged in."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)


def is_logged_in():
    return "user_id" in session


def is_admin():
    """True only if the logged-in user's email is on the admin whitelist in config.py."""
    user = current_user()
    if not user:
        return False
    admin_emails = {e.lower() for e in Config.ADMIN_EMAILS}
    return user["email"].lower() in admin_emails


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login", next=request.path))
        if not is_admin():
            flash("You don't have access to that page.", "error")
            return redirect(url_for("main.home"))
        return view_func(*args, **kwargs)
    return wrapped


def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email or ""))
