"""
Cart & wishlist are kept in the Flask session (server-signed cookie) so the
demo works instantly with no login system, while still behaving like a real
cart: quantities, totals, GST and delivery fee are all computed here.

Session shape:
    session['cart']     = {"<product_id>": quantity, ...}
    session['wishlist']  = [product_id, ...]
"""
import base64
import io

import qrcode
from flask import session

from config import Config
from app.models.product import get_products_by_ids


def get_cart_dict():
    return session.setdefault("cart", {})


def get_wishlist_list():
    return session.setdefault("wishlist", [])


def add_to_cart(product_id, quantity=1):
    cart = get_cart_dict()
    key = str(product_id)
    cart[key] = cart.get(key, 0) + quantity
    session["cart"] = cart
    session.modified = True


def update_cart_quantity(product_id, quantity):
    cart = get_cart_dict()
    key = str(product_id)
    if quantity <= 0:
        cart.pop(key, None)
    else:
        cart[key] = quantity
    session["cart"] = cart
    session.modified = True


def remove_from_cart(product_id):
    cart = get_cart_dict()
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True


def clear_cart():
    session["cart"] = {}
    session.modified = True


def get_cart_items():
    """Returns list of {product: {...}, quantity, line_total}."""
    cart = get_cart_dict()
    ids = [int(pid) for pid in cart.keys()]
    products = get_products_by_ids(ids)
    products_by_id = {p["id"]: p for p in products}

    items = []
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = products_by_id.get(pid)
        if not product:
            continue
        line_total = product["discounted_price"] * qty
        items.append({"product": product, "quantity": qty, "line_total": line_total})
    return items


def calculate_totals(items):
    subtotal = sum(item["line_total"] for item in items)
    gst = round(subtotal * Config.GST_RATE)
    delivery_fee = 0 if (subtotal == 0 or subtotal >= Config.FREE_DELIVERY_THRESHOLD) else Config.STANDARD_DELIVERY_FEE
    grand_total = subtotal + gst + delivery_fee
    return {
        "subtotal": subtotal,
        "gst": gst,
        "delivery_fee": delivery_fee,
        "grand_total": grand_total,
        "gst_rate_pct": int(Config.GST_RATE * 100),
    }


def add_to_wishlist(product_id):
    wishlist = get_wishlist_list()
    if product_id not in wishlist:
        wishlist.append(product_id)
    session["wishlist"] = wishlist
    session.modified = True


def remove_from_wishlist(product_id):
    wishlist = get_wishlist_list()
    if product_id in wishlist:
        wishlist.remove(product_id)
    session["wishlist"] = wishlist
    session.modified = True


def get_wishlist_products():
    wishlist = get_wishlist_list()
    return get_products_by_ids(wishlist)


def cart_count():
    return sum(get_cart_dict().values())


def wishlist_count():
    return len(get_wishlist_list())


def generate_upi_qr_base64(amount):
    """
    Generates a QR code image (as a base64 PNG data string) for a SIMULATED
    UPI payment. The encoded VPA ("novacart.demo@upi") is intentionally not a
    real, registered UPI ID — this is a checkout demo, not a live payment
    gateway, so the QR is for visual realism only and cannot move real money
    even if scanned for real.
    """
    upi_string = (
        f"upi://pay?pa=novacart.demo@upi&pn=NovaCart&am={amount}"
        f"&cu=INR&tn=NovaCart%20Order%20Payment"
    )
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(upi_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B1220", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
