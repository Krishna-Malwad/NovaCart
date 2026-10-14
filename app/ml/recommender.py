"""
NovaCart recommendation engine.

Approach (deliberately simple & explainable):
1. Build a single "content" string per product from category, brand, tags
   and description.
2. Vectorise all products with TF-IDF (scikit-learn).
3. For a given product, compute cosine similarity against every other
   product and return the top-N most similar ones.
4. Convert similarity scores into a 0-100% "match score" and generate a
   plain-English reason (shared category / brand / tags) so the
   recommendation is transparent, not a black box.

This module is intentionally re-computed at request time from the current
product list rather than persisted, since the catalogue is small (100
items) and TF-IDF on 100 short documents is essentially instant.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.product import get_all_products
from config import Config


def _build_content(product):
    tags = " ".join(product.get("tags_list", []))
    return f"{product['category']} {product['brand']} {tags} {product['description']}"


def _vectorize(products):
    corpus = [_build_content(p) for p in products]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    return matrix


def _explain(base, candidate):
    reasons = []
    if base["category"] == candidate["category"]:
        reasons.append(f"same category ({candidate['category']})")
    if base["brand"] == candidate["brand"]:
        reasons.append(f"same brand ({candidate['brand']})")
    shared_tags = set(base.get("tags_list", [])) & set(candidate.get("tags_list", []))
    if shared_tags:
        reasons.append("shared use-case: " + ", ".join(sorted(shared_tags)))
    if not reasons:
        reasons.append("similar product description")
    return "Recommended because of " + "; ".join(reasons) + "."


def get_recommendations(product_id, top_n=None):
    """
    Returns a list of dicts:
        {"product": {...}, "match_pct": int, "reason": "..."}
    ordered by similarity, excluding the source product itself.
    """
    top_n = top_n or Config.RECOMMENDATION_COUNT
    products = get_all_products()
    id_to_index = {p["id"]: i for i, p in enumerate(products)}

    if product_id not in id_to_index:
        return []

    matrix = _vectorize(products)
    idx = id_to_index[product_id]
    sims = cosine_similarity(matrix[idx], matrix).flatten()

    ranked = sorted(
        ((score, i) for i, score in enumerate(sims) if i != idx),
        key=lambda x: x[0],
        reverse=True,
    )

    base_product = products[idx]
    results = []
    for score, i in ranked[:top_n]:
        candidate = products[i]
        results.append({
            "product": candidate,
            "match_pct": round(min(score, 1.0) * 100),
            "reason": _explain(base_product, candidate),
        })
    return results


def get_similar_by_category(category, exclude_id=None, top_n=6):
    """Fallback recommender used when we just need 'more like this category'."""
    products = [p for p in get_all_products() if p["category"] == category and p["id"] != exclude_id]
    products.sort(key=lambda p: (p["rating"], p["reviews"]), reverse=True)
    return products[:top_n]
