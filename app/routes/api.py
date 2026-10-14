"""JSON API routes — currently just the NOVA AI assistant endpoint."""
from flask import Blueprint, request, jsonify

from app.ai.assistant import ask_nova

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/nova", methods=["POST"])
def nova_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    context_product_id = data.get("context_product_id")
    if context_product_id is not None:
        try:
            context_product_id = int(context_product_id)
        except (TypeError, ValueError):
            context_product_id = None

    result = ask_nova(message, context_product_id)

    return jsonify({
        "reply": result["reply"],
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "brand": p["brand"],
                "category": p["category"],
                "price": p["discounted_price"],
                "original_price": p["original_price"],
                "discount_pct": p["discount_pct"],
                "rating": p["rating"],
                "reviews": p["reviews"],
                "image": p["image"],
            }
            for p in result["products"]
        ],
    })
