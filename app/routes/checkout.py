"""Checkout & order confirmation routes."""
import re

from flask import Blueprint, render_template, request, redirect, url_for, session

from app.utils.helpers import get_cart_items, calculate_totals, clear_cart, generate_upi_qr_base64
from app.utils.auth import current_user
from app.models.order import create_order, get_order
from app.models.product import decrement_stock

checkout_bp = Blueprint("checkout", __name__)

PHONE_PATTERN = re.compile(r"^[0-9]{10}$")
PINCODE_PATTERN = re.compile(r"^[0-9]{6}$")


@checkout_bp.route("/checkout", methods=["GET"])
def checkout():
    items = get_cart_items()
    if not items:
        return redirect(url_for("cart.view_cart"))
    totals = calculate_totals(items)
    upi_qr_base64 = generate_upi_qr_base64(totals["grand_total"])

    # Prefill the form with the logged-in user's saved details, if any
    user = current_user()
    form_values = None
    if user:
        form_values = {
            "name": user["name"],
            "address": user.get("address") or "",
            "city": user.get("city") or "",
            "state": user.get("state") or "",
            "pincode": user.get("pincode") or "",
            "phone": user.get("phone") or "",
        }

    return render_template("checkout.html", items=items, totals=totals,
                            form_values=form_values, upi_qr_base64=upi_qr_base64)


@checkout_bp.route("/checkout/place-order", methods=["POST"])
def place_order():
    items = get_cart_items()
    if not items:
        return redirect(url_for("cart.view_cart"))

    totals = calculate_totals(items)

    customer = {
        "name": request.form.get("full_name", "").strip(),
        "address": request.form.get("address", "").strip(),
        "city": request.form.get("city", "").strip(),
        "state": request.form.get("state", "").strip(),
        "pincode": request.form.get("pincode", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "payment_method": request.form.get("payment_method", "Cash on Delivery"),
    }

    if not customer["name"] or len(customer["name"]) < 2:
        return render_template(
            "checkout.html",
            items=items,
            totals=totals,
            form_error="Please enter your full name.",
            form_values=customer,
            upi_qr_base64=generate_upi_qr_base64(totals["grand_total"]),
        )

    if not PHONE_PATTERN.match(customer["phone"]):
        return render_template(
            "checkout.html",
            items=items,
            totals=totals,
            form_error="Mobile number must contain exactly 10 digits.",
            form_values=customer,
            upi_qr_base64=generate_upi_qr_base64(totals["grand_total"]),
        )

    if not customer["address"]:
        return render_template(
            "checkout.html",
            items=items,
            totals=totals,
            form_error="Please enter your delivery address.",
            form_values=customer,
            upi_qr_base64=generate_upi_qr_base64(totals["grand_total"]),
        )

    if not customer["city"]:
        return render_template(
            "checkout.html",
            items=items,
            totals=totals,
            form_error="Please enter your city.",
            form_values=customer,
            upi_qr_base64=generate_upi_qr_base64(totals["grand_total"]),
        )

    if not customer["state"]:
        return render_template(
            "checkout.html",
            items=items,
            totals=totals,
            form_error="Please enter your state.",
            form_values=customer,
            upi_qr_base64=generate_upi_qr_base64(totals["grand_total"]),
        )

    if not PINCODE_PATTERN.match(customer["pincode"]):
        return render_template(
            "checkout.html",
            items=items,
            totals=totals,
            form_error="Pincode must contain exactly 6 digits.",
            form_values=customer,
            upi_qr_base64=generate_upi_qr_base64(totals["grand_total"]),
        )

    order_items = [
        {
            "product_id": item["product"]["id"],
            "product_name": item["product"]["name"],
            "quantity": item["quantity"],
            "price": item["product"]["discounted_price"],
        }
        for item in items
    ]

    session_id = session.get("_id", "guest")
    user = current_user()
    user_id = user["id"] if user else None
    order_id = create_order(session_id, customer, totals, order_items, user_id=user_id)

    for item in order_items:
        decrement_stock(item["product_id"], item["quantity"])

    clear_cart()
    return redirect(url_for("checkout.order_confirmation", order_id=order_id))


@checkout_bp.route("/checkout/confirmation/<int:order_id>")
def order_confirmation(order_id):
    order_data = get_order(order_id)
    if not order_data:
        return redirect(url_for("main.home"))
    return render_template(
        "checkout.html",
        confirmation=True,
        order=order_data["order"],
        order_items=order_data["items"],
    )
