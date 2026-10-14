"""
Analytics computations for the NovaCart dashboard.
All numbers are derived from real rows in the orders / order_items / products
tables — nothing here is hard-coded, so the dashboard updates automatically
as new orders come in through checkout.
"""
from collections import defaultdict

from app.database import get_connection


def get_kpis():
    conn = get_connection()
    revenue = conn.execute("SELECT COALESCE(SUM(grand_total), 0) FROM orders").fetchone()[0]
    order_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    customer_count = conn.execute("SELECT COUNT(DISTINCT customer_name) FROM orders").fetchone()[0]
    avg_rating = conn.execute("SELECT COALESCE(AVG(rating), 0) FROM products").fetchone()[0]
    conn.close()
    return {
        "revenue": revenue,
        "orders": order_count,
        "customers": customer_count,
        "avg_rating": round(avg_rating, 2),
    }


def get_top_products(limit=5):
    conn = get_connection()
    rows = conn.execute(
        """SELECT product_name, SUM(quantity) as units_sold, SUM(quantity * price) as revenue
           FROM order_items
           GROUP BY product_name
           ORDER BY units_sold DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_revenue_by_category():
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.category as category, SUM(oi.quantity * oi.price) as revenue
           FROM order_items oi
           JOIN products p ON p.id = oi.product_id
           GROUP BY p.category
           ORDER BY revenue DESC""",
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_sales():
    conn = get_connection()
    rows = conn.execute(
        """SELECT strftime('%Y-%m', created_at) as month, SUM(grand_total) as revenue, COUNT(*) as orders
           FROM orders
           GROUP BY month
           ORDER BY month""",
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_orders(limit=10):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_catalog_distribution():
    """How many products exist per category — useful even with zero orders."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT category, COUNT(*) as count FROM products GROUP BY category ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
