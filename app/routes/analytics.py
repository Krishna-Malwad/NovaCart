"""Analytics dashboard route."""
from flask import Blueprint, render_template

from app.analytics.dashboard import (
    get_kpis, get_top_products, get_revenue_by_category,
    get_monthly_sales, get_recent_orders, get_category_catalog_distribution,
)
from app.utils.auth import admin_required

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@admin_required
def dashboard():
    return render_template(
        "analytics.html",
        kpis=get_kpis(),
        top_products=get_top_products(5),
        revenue_by_category=get_revenue_by_category(),
        monthly_sales=get_monthly_sales(),
        recent_orders=get_recent_orders(10),
        catalog_distribution=get_category_catalog_distribution(),
    )
