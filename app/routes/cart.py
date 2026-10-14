"""Shopping cart routes. Supports both normal form posts and JSON/AJAX calls."""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from app.utils.helpers import (
    add_to_cart, update_cart_quantity, remove_from_cart,
    get_cart_items, calculate_totals, cart_count,
)

cart_bp = Blueprint("cart", __name__)


def _wants_json():
    return request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest"


@cart_bp.route("/cart")
def view_cart():
    items = get_cart_items()
    totals = calculate_totals(items)
    return render_template("cart.html", items=items, totals=totals)


@cart_bp.route("/cart/add", methods=["POST"])
def cart_add():
    data = request.get_json(silent=True) or request.form
    product_id = int(data.get("product_id"))
    quantity = int(data.get("quantity", 1))
    add_to_cart(product_id, quantity)

    if _wants_json():
        return jsonify({"success": True, "cart_count": cart_count()})
    return redirect(request.referrer or url_for("main.home"))


@cart_bp.route("/cart/update", methods=["POST"])
def cart_update():
    data = request.get_json(silent=True) or request.form
    product_id = int(data.get("product_id"))
    quantity = int(data.get("quantity"))
    update_cart_quantity(product_id, quantity)

    if _wants_json():
        items = get_cart_items()
        totals = calculate_totals(items)
        return jsonify({"success": True, "cart_count": cart_count(), "totals": totals})
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/cart/remove", methods=["POST"])
def cart_remove():
    data = request.get_json(silent=True) or request.form
    product_id = int(data.get("product_id"))
    remove_from_cart(product_id)

    if _wants_json():
        items = get_cart_items()
        totals = calculate_totals(items)
        return jsonify({"success": True, "cart_count": cart_count(), "totals": totals})
    return redirect(url_for("cart.view_cart"))
