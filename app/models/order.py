"""
Order data-access helpers. Orders are persisted permanently in SQLite so the
analytics dashboard has real historical data to report on.
"""
from app.database import get_connection


def create_order(session_id, customer, totals, items, user_id=None):
    """
    customer: dict with name, address, city, pincode, phone, payment_method
    totals: dict with subtotal, gst, delivery_fee, grand_total
    items: list of dicts with product_id, product_name, quantity, price
    user_id: optional — links the order to a logged-in user's profile/order history
    Returns the new order id.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO orders
           (session_id, user_id, customer_name, address, city, state, pincode, phone,
            payment_method, subtotal, gst, delivery_fee, grand_total, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed')""",
        (
            session_id,
            user_id,
            customer["name"],
            customer["address"],
            customer["city"],
            customer.get("state", ""),
            customer["pincode"],
            customer["phone"],
            customer["payment_method"],
            totals["subtotal"],
            totals["gst"],
            totals["delivery_fee"],
            totals["grand_total"],
        ),
    )
    order_id = cur.lastrowid

    for item in items:
        cur.execute(
            """INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
               VALUES (?, ?, ?, ?, ?)""",
            (order_id, item["product_id"], item["product_name"], item["quantity"], item["price"]),
        )

    conn.commit()
    conn.close()
    return order_id


def get_order(order_id):
    conn = get_connection()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()
    conn.close()
    if order is None:
        return None
    return {"order": dict(order), "items": [dict(i) for i in items]}


def get_orders_by_user(user_id):
    """Returns all orders placed by a logged-in user, most recent first, each with its items."""
    conn = get_connection()
    orders = conn.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    result = []
    for order in orders:
        items = conn.execute(
            "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
        ).fetchall()
        result.append({"order": dict(order), "items": [dict(i) for i in items]})
    conn.close()
    return result


def get_all_orders():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_order_items_all():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM order_items").fetchall()
    conn.close()
    return [dict(r) for r in rows]
