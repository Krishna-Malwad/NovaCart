"""
Product data-access helpers.
Every function here returns plain dicts (not sqlite3.Row) so templates and
JSON responses can use them interchangeably.
"""
from app.database import get_connection


def _row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    d["tags_list"] = [t.strip() for t in (d.get("tags") or "").split(",") if t.strip()]
    return d


def get_all_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_product_by_id(product_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_products_by_ids(ids):
    if not ids:
        return []
    conn = get_connection()
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"SELECT * FROM products WHERE id IN ({placeholders})", ids
    ).fetchall()
    conn.close()
    by_id = {r["id"]: _row_to_dict(r) for r in rows}
    # preserve original order & allow duplicates
    return [by_id[i] for i in ids if i in by_id]


def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    conn.close()
    return [r["category"] for r in rows]


def get_brands():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT brand FROM products ORDER BY brand").fetchall()
    conn.close()
    return [r["brand"] for r in rows]


SYNONYM_CATEGORY_MAP = {
    # Mobiles & Phones
    "phone": "Mobiles & Accessories",
    "phones": "Mobiles & Accessories",
    "smartphone": "Mobiles & Accessories",
    "smartphones": "Mobiles & Accessories",
    "mobile": "Mobiles & Accessories",
    "mobiles": "Mobiles & Accessories",
    "cellphone": "Mobiles & Accessories",
    "cellphones": "Mobiles & Accessories",
    # Shoes & Footwear
    "shoe": "Footwear",
    "shoes": "Footwear",
    "footwear": "Footwear",
    "sneaker": "Footwear",
    "sneakers": "Footwear",
    "boots": "Footwear",
    "boot": "Footwear",
    "sandals": "Footwear",
    "sandal": "Footwear",
    "loafers": "Footwear",
    "loafer": "Footwear",
    "clogs": "Footwear",
    "clog": "Footwear",
    # Computers & Laptops
    "laptop": "Computers & Laptops",
    "laptops": "Computers & Laptops",
    "computer": "Computers & Laptops",
    "computers": "Computers & Laptops",
    "pc": "Computers & Laptops",
    "macbook": "Computers & Laptops",
    # Books
    "book": "Books",
    "books": "Books",
    "novel": "Books",
    "novels": "Books",
    # Grocery
    "grocery": "Grocery",
    "groceries": "Grocery",
    # Gaming
    "gaming": "Gaming",
    # Home & Kitchen
    "kitchen": "Home & Kitchen",
    "cookware": "Home & Kitchen",
    # Beauty & Personal Care
    "beauty": "Beauty & Personal Care",
    "skincare": "Beauty & Personal Care",
    "cosmetics": "Beauty & Personal Care",
    "makeup": "Beauty & Personal Care",
    # Fashion
    "fashion": "Fashion",
    "clothes": "Fashion",
    "clothing": "Fashion",
    "apparel": "Fashion",
    # Bags & Accessories
    "bag": "Bags & Accessories",
    "bags": "Bags & Accessories",
    "backpack": "Bags & Accessories",
    "backpacks": "Bags & Accessories",
    "luggage": "Bags & Accessories",
}

AUDIO_KEYWORDS = {
    "headphone", "headphones", "earphone", "earphones",
    "earbuds", "earbud", "airpods", "airpod", "headset", "headsets", "audio"
}


def search_products(query="", category=None, min_price=None, max_price=None,
                     min_rating=None, sort_by=None):
    """
    Flexible product search/filter used by the search page and NOVA AI.
    Supports:
    - Multi-word tokenized queries (e.g. 'running shoes', 'samsung phone', 'apple laptop')
    - Case-insensitivity (LAPTOP, Laptop, LaPtOp)
    - Partial words (lap, head, sam, shoe)
    - Synonyms and category alias matching (phone -> Mobiles, shoes -> Footwear, etc.)
    - Audio keyword detection (headphones -> boAt Rockerz, JBL Tune, Sony WH-CH520, etc.)
    - Combined filtering (category, price range, min rating, sort order)
    """
    import re

    conn = get_connection()
    clean_query = (query or "").strip()

    def build_query(match_all_terms=True):
        sql = "SELECT * FROM products WHERE 1=1"
        params = []

        if clean_query:
            raw_tokens = clean_query.split()
            tokens = [re.sub(r"[^\w\-]", "", t.lower()) for t in raw_tokens]
            tokens = [t for t in tokens if t]

            if tokens:
                term_clauses = []
                for t in tokens:
                    sub_clauses = [
                        "name LIKE ?",
                        "brand LIKE ?",
                        "category LIKE ?",
                        "tags LIKE ?",
                        "description LIKE ?"
                    ]
                    sub_params = [f"%{t}%", f"%{t}%", f"%{t}%", f"%{t}%", f"%{t}%"]

                    # Check singular if plural
                    if t.endswith("s") and len(t) > 3:
                        stem = t[:-1]
                        sub_clauses.extend([
                            "name LIKE ?", "brand LIKE ?", "category LIKE ?",
                            "tags LIKE ?", "description LIKE ?"
                        ])
                        sub_params.extend([f"%{stem}%", f"%{stem}%", f"%{stem}%", f"%{stem}%", f"%{stem}%"])

                    # Category alias match
                    if t in SYNONYM_CATEGORY_MAP:
                        sub_clauses.append("category = ?")
                        sub_params.append(SYNONYM_CATEGORY_MAP[t])

                    # Audio keywords match
                    if t in AUDIO_KEYWORDS or t == "head":
                        sub_clauses.extend([
                            "name LIKE ?", "name LIKE ?", "name LIKE ?", "name LIKE ?",
                            "name LIKE ?", "name LIKE ?", "name LIKE ?", "name LIKE ?",
                            "tags LIKE ?", "tags LIKE ?"
                        ])
                        sub_params.extend([
                            "%Rockerz%", "%Tune%", "%WH-CH520%", "%HD 350BT%",
                            "%Buds%", "%AirPods%", "%Airdopes%", "%Headset%",
                            "%noise cancellation%", "%bass%"
                        ])

                    term_clauses.append(f"({' OR '.join(sub_clauses)})")
                    params.extend(sub_params)

                connector = " AND " if match_all_terms else " OR "
                sql += f" AND ({connector.join(term_clauses)})"

        if category:
            sql += " AND category = ?"
            params.append(category)

        if min_price is not None:
            sql += " AND discounted_price >= ?"
            params.append(min_price)

        if max_price is not None:
            sql += " AND discounted_price <= ?"
            params.append(max_price)

        if min_rating is not None:
            sql += " AND rating >= ?"
            params.append(min_rating)

        sort_map = {
            "price_low": "discounted_price ASC",
            "price_high": "discounted_price DESC",
            "rating": "rating DESC",
            "popularity": "reviews DESC",
        }
        sql += " ORDER BY " + sort_map.get(sort_by, "id ASC")
        return sql, params

    sql, params = build_query(match_all_terms=True)
    rows = conn.execute(sql, params).fetchall()

    # Fallback to OR matching if multi-word AND search returned 0 results
    if not rows and clean_query and len(clean_query.split()) > 1:
        sql, params = build_query(match_all_terms=False)
        rows = conn.execute(sql, params).fetchall()

    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_featured_products(limit=8):
    """High rating + heavily reviewed products for the homepage."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE rating >= 4.0 ORDER BY reviews DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_trending_products(limit=8):
    """Most-reviewed products, a different cut than 'featured'."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products ORDER BY reviews DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_deal_products(limit=8):
    """Biggest discounts first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE discount_pct > 0 ORDER BY discount_pct DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_products_by_category(category, limit=None):
    conn = get_connection()
    sql = "SELECT * FROM products WHERE category = ? ORDER BY reviews DESC"
    params = [category]
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def decrement_stock(product_id, quantity):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET stock = MAX(stock - ?, 0) WHERE id = ?", (quantity, product_id)
    )
    conn.commit()
    conn.close()
