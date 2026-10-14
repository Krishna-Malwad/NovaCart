"""Authentication routes: signup, login, logout, and the user profile page."""
from flask import Blueprint, render_template, request, redirect, url_for, session

from app.models.user import (
    create_user, get_user_by_email, verify_password, email_exists, update_profile,
)
from app.models.order import get_orders_by_user
from app.utils.auth import login_user, logout_user, login_required, current_user, is_valid_email

auth_bp = Blueprint("auth", __name__)


import re

PHONE_PATTERN = re.compile(r"^[0-9]{10}$")
PINCODE_PATTERN = re.compile(r"^[0-9]{6}$")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    errors = []
    if len(name) < 2:
        errors.append("Please enter your full name.")
    if not is_valid_email(email):
        errors.append("Please enter a valid email address.")
    if not phone or not PHONE_PATTERN.match(phone):
        errors.append("Mobile number must contain exactly 10 digits.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters long.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if not errors and email_exists(email):
        errors.append("An account with this email already exists. Try logging in instead.")

    if errors:
        return render_template(
            "signup.html",
            errors=errors,
            form_values={"name": name, "email": email, "phone": phone},
        )

    user_id = create_user(name, email, password, phone=phone)
    login_user(user_id)
    return redirect(url_for("main.home"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", next_url=request.args.get("next", ""))

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    next_url = request.form.get("next", "")

    user = get_user_by_email(email)
    if not user or not verify_password(user, password):
        return render_template(
            "login.html",
            errors=["Incorrect email or password."],
            form_values={"email": email},
            next_url=next_url,
        )

    login_user(user["id"])
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("main.home"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@auth_bp.route("/profile")
@login_required
def profile():
    user = current_user()
    orders = get_orders_by_user(user["id"])
    return render_template("profile.html", user=user, orders=orders)


@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def profile_update():
    from flask import flash
    user = current_user()
    name = request.form.get("name", "").strip() or user["name"]
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()
    pincode = request.form.get("pincode", "").strip()

    if phone and not PHONE_PATTERN.match(phone):
        flash("Mobile number must contain exactly 10 digits.", "error")
        return redirect(url_for("auth.profile"))

    if pincode and not PINCODE_PATTERN.match(pincode):
        flash("Pincode must contain exactly 6 digits.", "error")
        return redirect(url_for("auth.profile"))

    update_profile(
        user["id"],
        name=name,
        phone=phone,
        address=address,
        city=city,
        state=state,
        pincode=pincode,
    )
    flash("Profile updated successfully.", "success")
    return redirect(url_for("auth.profile"))
