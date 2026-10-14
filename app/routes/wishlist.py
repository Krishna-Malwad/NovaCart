"""Wishlist routes."""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from app.utils.helpers import (
    add_to_wishlist, remove_from_wishlist, get_wishlist_products,
    add_to_cart, wishlist_count, cart_count,
)

wishlist_bp = Blueprint("wishlist", __name__)


def _wants_json():
    return request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest"


@wishlist_bp.route("/wishlist")
def view_wishlist():
    products = get_wishlist_products()
    return render_template("wishlist.html", products=products)


@wishlist_bp.route("/wishlist/add", methods=["POST"])
def wishlist_add():
    data = request.get_json(silent=True) or request.form
    product_id = int(data.get("product_id"))
    add_to_wishlist(product_id)

    if _wants_json():
        return jsonify({"success": True, "wishlist_count": wishlist_count()})
    return redirect(request.referrer or url_for("main.home"))


@wishlist_bp.route("/wishlist/remove", methods=["POST"])
def wishlist_remove():
    data = request.get_json(silent=True) or request.form
    product_id = int(data.get("product_id"))
    remove_from_wishlist(product_id)

    if _wants_json():
        return jsonify({"success": True, "wishlist_count": wishlist_count()})
    return redirect(request.referrer or url_for("wishlist.view_wishlist"))


@wishlist_bp.route("/wishlist/move-to-cart", methods=["POST"])
def wishlist_move_to_cart():
    data = request.get_json(silent=True) or request.form
    product_id = int(data.get("product_id"))
    add_to_cart(product_id, 1)
    remove_from_wishlist(product_id)

    if _wants_json():
        return jsonify({"success": True, "cart_count": cart_count(), "wishlist_count": wishlist_count()})
    return redirect(url_for("wishlist.view_wishlist"))
