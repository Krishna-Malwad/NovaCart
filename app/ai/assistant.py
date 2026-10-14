"""
NOVA AI - NovaCart's natural-language shopping assistant.

This is NOT a fixed-reply chatbot. It parses free text queries to extract:
    - budget / price ceiling & floor  ("under 80000", "budget 50k", "between 20000 and 40000")
    - category                        ("laptop", "phone", "headphones", ...)
    - use-case / intent               ("for coding", "for photography", "for gaming", ...)
    - comparison intent                ("compare X and Y", "X vs Y")
    - contextual product questions     ("is this good for students?" while viewing a product)

...and then queries the real product dataset (SQLite) to build a grounded,
explainable response. There are no canned/scripted answers - every reply is
generated from whichever products actually match the parsed intent.
"""
import re

from app.models.product import get_all_products, search_products, get_product_by_id
from config import Config

CATEGORY_KEYWORDS = {
    "Computers & Laptops": ["laptop", "laptops", "notebook", "macbook", "ultrabook", "computer", "pc", "desktop"],
    "Mobiles & Accessories": ["mobile", "mobiles", "phone", "phones", "smartphone", "iphone", "android", "tablet", "tablets", "ipad", "charger", "power bank", "mouse", "keyboard"],
    "Electronics": ["electronics", "headphone", "headphones", "earphone", "earphones", "earbuds", "earbud", "airpods", "headset", "smartwatch", "smart watch", "watch", "camera", "cameras", "dslr", "mirrorless", "gopro", "speaker", "speakers", "soundbar"],
    "Fashion": ["fashion", "clothing", "clothes", "shirt", "shirts", "tshirt", "t-shirt", "kurta", "kurtas", "kurti", "saree", "sarees", "jeans", "jacket", "vest", "trousers", "dress", "ethnic"],
    "Footwear": ["shoes", "shoe", "footwear", "sneaker", "sneakers", "running shoes", "sandals", "sandal", "slippers", "clogs", "loafers", "boots", "oxford"],
    "Home & Kitchen": ["home", "kitchen", "mixer", "grinder", "mixer grinder", "air fryer", "cookware", "purifier", "kettle", "bedsheet", "comforter", "blender", "oven", "otg", "cooker", "flask", "light"],
    "Beauty & Personal Care": ["beauty", "skincare", "skin care", "sunscreen", "serum", "cleanser", "trimmer", "hair dryer", "dryer", "shampoo", "perfume", "fragrance", "night gel", "kajal", "mascara", "beard oil"],
    "Books": ["book", "books", "reading", "novel", "novels", "bestseller", "paperback", "habits", "psychology", "sapiens", "alchemist", "clean code"],
    "Sports & Fitness": ["sports", "fitness", "gym", "workout", "yoga", "yoga mat", "dumbbells", "dumbbell", "badminton", "racket", "football", "skipping rope", "cricket", "swimming"],
    "Toys & Games": ["toy", "toys", "game", "games", "lego", "monopoly", "uno", "rc car", "rubik", "nerf", "barbie", "play-doh", "catan", "puzzle"],
    "Grocery": ["grocery", "groceries", "rice", "olive oil", "oil", "almonds", "dry fruits", "honey", "tea", "coffee", "muesli", "chocolates", "salt", "yogurt"],
    "Gaming": ["gaming", "gamer", "gaming keyboard", "gaming mouse", "gaming headset", "controller", "gamepad", "ps5", "xbox", "gaming chair", "stream deck"],
    "Bags & Accessories": ["bag", "bags", "backpack", "backpacks", "luggage", "trolley", "suitcase", "wallet", "wallets", "sunglasses", "belt", "duffel", "tote"],
}

USE_CASE_KEYWORDS = {
    "coding": ["coding", "programming", "developer", "development", "code"],
    "gaming": ["gaming", "games", "gamer"],
    "student": ["student", "students", "college", "university", "study", "school"],
    "photography": ["photography", "photo", "photos", "photographer"],
    "video editing": ["video editing", "editing", "video"],
    "music": ["music", "songs", "listening", "bass"],
    "travel": ["travel", "traveling", "trip", "vacation"],
    "business": ["business", "office", "work", "formal"],
    "fitness": ["fitness", "workout", "gym", "running", "jogging", "exercise", "training"],
    "gift": ["gift", "gifts", "gifting", "birthday", "anniversary", "present"],
    "kitchen": ["cooking", "kitchen", "recipe", "food"],
    "skincare": ["skincare", "skin", "sun protection", "hydration", "glow"],
    "reading": ["reading", "knowledge", "learning", "finance"],
    "daily use": ["daily use", "everyday", "casual", "routine"],
}

NUM_WORD_MULTIPLIER = [
    (r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)s?", 100000),
    (r"(\d+(?:\.\d+)?)\s*k\b", 1000),
]


def _extract_numbers_in_rupees(text):
    """Find all monetary amounts in free text and normalise to plain rupees."""
    text_l = text.lower().replace(",", "")
    amounts = []

    consumed_spans = []
    for pattern, multiplier in NUM_WORD_MULTIPLIER:
        for m in re.finditer(pattern, text_l):
            amounts.append(float(m.group(1)) * multiplier)
            consumed_spans.append(m.span())

    # Plain numbers (₹80000, 80000, rs 80000) not already consumed by k/lakh matches
    for m in re.finditer(r"(?:₹|rs\.?|inr)?\s*(\d{3,7})(?!\s*(?:k\b|lakh|lac))", text_l):
        span = m.span()
        overlap = any(span[0] >= s and span[1] <= e for s, e in consumed_spans)
        if not overlap:
            amounts.append(float(m.group(1)))

    return sorted(set(amounts))


def _extract_budget(text):
    """Returns (min_price, max_price) or (None, None) if no budget mentioned."""
    text_l = text.lower()
    amounts = _extract_numbers_in_rupees(text)
    if not amounts:
        return None, None

    if re.search(r"\bunder\b|\bbelow\b|\bless than\b|\bwithin\b|\bupto\b|\bup to\b", text_l):
        return None, int(amounts[-1])
    if re.search(r"\babove\b|\bover\b|\bmore than\b|\bgreater than\b", text_l):
        return int(amounts[0]), None
    if re.search(r"\bbetween\b", text_l) and len(amounts) >= 2:
        return int(amounts[0]), int(amounts[-1])
    if re.search(r"\bbudget\b", text_l):
        return None, int(amounts[-1])
    if len(amounts) == 1:
        # A bare number with no qualifier -> treat as an approximate ceiling
        return None, int(amounts[0])
    return int(amounts[0]), int(amounts[-1])


def _extract_category(text):
    text_l = text.lower()
    ordered_categories = [
        "Gaming", "Bags & Accessories", "Home & Kitchen", "Beauty & Personal Care",
        "Sports & Fitness", "Toys & Games", "Grocery", "Footwear", "Fashion", "Books",
        "Computers & Laptops", "Mobiles & Accessories", "Electronics"
    ]
    for category in ordered_categories:
        for kw in CATEGORY_KEYWORDS[category]:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_l):
                return category
    return None


def _extract_use_cases(text):
    text_l = text.lower()
    found = []
    for tag, keywords in USE_CASE_KEYWORDS.items():
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_l):
                found.append(tag)
                break
    return found


def _is_comparison(text):
    text_l = text.lower()
    return bool(re.search(r"\bcompare\b|\bvs\.?\b|\bversus\b|\bor\b.*better", text_l))


def _split_comparison_terms(text):
    text_l = re.sub(r"\bcompare\b", "", text.lower())
    parts = re.split(r"\bvs\.?\b|\bversus\b|\band\b", text_l)
    parts = [p.strip() for p in parts if p.strip()]
    return parts[:2]


def _find_best_match(term):
    results = search_products(query=term)
    if not results:
        return None
    results.sort(key=lambda p: (p["rating"], p["reviews"]), reverse=True)
    return results[0]


def _format_product_line(p):
    return (f"{p['name']} ({p['brand']}) - {Config.CURRENCY_SYMBOL}{p['discounted_price']:,} "
            f"| {p['rating']}★ ({p['reviews']} reviews)")


def _handle_comparison(text):
    terms = _split_comparison_terms(text)
    if len(terms) < 2:
        return {
            "reply": "Tell me two products or brands to compare, e.g. \"Compare iPhone and Samsung\".",
            "products": [],
        }

    p1 = _find_best_match(terms[0])
    p2 = _find_best_match(terms[1])

    if not p1 or not p2:
        return {
            "reply": f"I couldn't find a good match for one of those. Try being more specific, "
                     f"like an exact brand or product name.",
            "products": [],
        }

    lines = [f"Here's how they compare:", "", f"• {_format_product_line(p1)}", f"• {_format_product_line(p2)}", ""]

    if p1["discounted_price"] != p2["discounted_price"]:
        cheaper = p1 if p1["discounted_price"] < p2["discounted_price"] else p2
        lines.append(f"💰 {cheaper['name']} is cheaper.")
    if p1["rating"] != p2["rating"]:
        better_rated = p1 if p1["rating"] > p2["rating"] else p2
        lines.append(f"⭐ {better_rated['name']} has the higher rating.")
    if p1["reviews"] != p2["reviews"]:
        more_popular = p1 if p1["reviews"] > p2["reviews"] else p2
        lines.append(f"👥 {more_popular['name']} is more popular ({more_popular['reviews']} reviews).")

    return {"reply": "\n".join(lines), "products": [p1, p2]}


def _handle_contextual_question(text, context_product_id):
    """Handles things like 'is this good for students?' while viewing a product."""
    product = get_product_by_id(context_product_id)
    if not product:
        return None

    use_cases = _extract_use_cases(text)
    tags = product.get("tags_list", [])

    if use_cases:
        matched = [uc for uc in use_cases if uc in tags]
        if matched:
            reply = (f"Yes — the {product['name']} is well suited for {', '.join(matched)}. "
                      f"It's rated {product['rating']}★ across {product['reviews']} reviews, "
                      f"so other buyers with similar needs have been happy with it.")
        else:
            reply = (f"The {product['name']} isn't specifically marketed for {', '.join(use_cases)} — "
                      f"it's better suited for {', '.join(tags[:2]) if tags else 'general use'}. "
                      f"You may want to check other products in {product['category']} for a closer fit.")
        return {"reply": reply, "products": [product]}

    reply = (f"The {product['name']} is a {product['brand']} {product['category'].lower()[:-1] if product['category'].endswith('s') else product['category'].lower()} "
             f"rated {product['rating']}★ from {product['reviews']} reviews, priced at "
             f"{Config.CURRENCY_SYMBOL}{product['discounted_price']:,}. {product['description']}")
    return {"reply": reply, "products": [product]}


def ask_nova(message, context_product_id=None):
    """
    Main entry point. Returns:
        {"reply": str, "products": [product_dict, ...]}
    """
    if not message or not message.strip():
        return {"reply": "Ask me things like \"best laptop under ₹60000\" or \"headphones for gym\".",
                "products": []}

    text = message.strip()
    text_l = text.lower()

    # 1. Comparison intent
    if _is_comparison(text):
        return _handle_comparison(text)

    # 2. Contextual question about the product currently being viewed
    if context_product_id and re.search(r"\bthis\b|\bit\b", text_l):
        result = _handle_contextual_question(text, context_product_id)
        if result:
            return result

    # 3. General recommendation query: parse budget, category, use-case
    min_price, max_price = _extract_budget(text)
    category = _extract_category(text)
    use_cases = _extract_use_cases(text)

    results = search_products(
        query="",
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=None,
        sort_by="rating",
    )

    # Narrow further by use-case tags if we found any
    if use_cases:
        tag_filtered = [p for p in results if set(use_cases) & set(p.get("tags_list", []))]
        if tag_filtered:
            results = tag_filtered

    # If nothing structured was detected at all, fall back to free-text search
    if not category and not use_cases and min_price is None and max_price is None:
        results = search_products(query=text)

    results = sorted(results, key=lambda p: (p["rating"], p["reviews"]), reverse=True)[:6]

    if not results:
        return {
            "reply": "I couldn't find a matching product. Try a different budget, category, "
                     "or use-case — for example \"best phone under ₹30000 for photography\".",
            "products": [],
        }

    # Build an explainable reply
    reply_parts = []
    if category:
        reply_parts.append(f"Looking at {category}")
    if use_cases:
        reply_parts.append(f"for {', '.join(use_cases)}")
    if max_price:
        reply_parts.append(f"under {Config.CURRENCY_SYMBOL}{max_price:,}")
    if min_price:
        reply_parts.append(f"above {Config.CURRENCY_SYMBOL}{min_price:,}")

    intro = " ".join(reply_parts) if reply_parts else f"Based on \"{text}\""
    top = results[0]
    reply = (f"{intro}, my top pick is the {top['name']} — rated {top['rating']}★ "
             f"({top['reviews']} reviews) at {Config.CURRENCY_SYMBOL}{top['discounted_price']:,}. "
             f"I've also listed {len(results) - 1} more good alternatives below.")

    return {"reply": reply, "products": results}
