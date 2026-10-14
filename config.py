"""
NovaCart configuration.
Central place for app-wide settings so nothing is hard-coded across modules.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("NOVACART_SECRET_KEY")

    DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
    PRODUCTS_CSV = os.path.join(BASE_DIR, "datasets", "products.csv")

    # Business rules
    GST_RATE = 0.18          # 18% GST applied on subtotal
    FREE_DELIVERY_THRESHOLD = 499   # orders above this get free delivery
    STANDARD_DELIVERY_FEE = 49

    CURRENCY_SYMBOL = "₹"

    # Recommendation engine
    RECOMMENDATION_COUNT = 6

    # Admin access — only accounts signed up with one of these emails can view
    # the Analytics Dashboard. Change this to your own account's email.
    # Comparison is case-insensitive.
    ADMIN_EMAILS = [
        "admin@novacart.com",   # <-- CHANGE THIS to the email you sign up with
    ]
