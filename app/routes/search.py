"""Search & filter page."""
from flask import Blueprint, render_template, request

from app.models.product import search_products, get_categories

search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
def search():
    query = request.args.get("q", "", type=str).strip()
    category = request.args.get("category", "", type=str) or None
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_rating = request.args.get("min_rating", type=float)
    sort_by = request.args.get("sort", "") or None

    results = search_products(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by,
    )

    return render_template(
        "search.html",
        query=query,
        results=results,
        categories=get_categories(),
        selected_category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by,
        result_count=len(results),
    )
