"""Homepage, product detail page, and static-ish pages."""
from flask import Blueprint, render_template, abort

from app.models.product import (
    get_featured_products, get_trending_products, get_deal_products,
    get_product_by_id, get_categories,
)
from app.ml.recommender import get_recommendations
from app.utils.helpers import cart_count, wishlist_count
from app.utils.auth import current_user, is_admin

main_bp = Blueprint("main", __name__)


@main_bp.app_context_processor
def inject_globals():
    """Makes cart/wishlist counts, category list, and auth state available in every template."""
    return {
        "nav_cart_count": cart_count(),
        "nav_wishlist_count": wishlist_count(),
        "nav_categories": get_categories(),
        "nav_user": current_user(),
        "nav_is_admin": is_admin(),
    }


@main_bp.route("/")
def home():
    return render_template(
        "index.html",
        deals=get_deal_products(8),
        trending=get_trending_products(8),
        recommended=get_featured_products(8),
        categories=get_categories(),
    )


@main_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        abort(404)
    recommendations = get_recommendations(product_id)
    return render_template("product.html", product=product, recommendations=recommendations)
