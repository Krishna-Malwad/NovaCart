"""
One-time generator script for datasets/products.csv
Creates 100 realistic electronics products across 8 categories.
Run: python3 scripts_gen_dataset.py
"""
import csv
import random

random.seed(7)

IMAGES = {
    "Laptops": [
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600",
        "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=600",
        "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600",
        "https://images.unsplash.com/photo-1602080858428-57174f9431cf?w=600",
    ],
    "Mobiles": [
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600",
        "https://images.unsplash.com/photo-1592286927505-1def25115558?w=600",
        "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600",
        "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=600",
        "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=600",
    ],
    "Tablets": [
        "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600",
        "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?w=600",
        "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=600",
        "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?w=600",
    ],
    "Accessories": [
        "https://images.unsplash.com/photo-1625948515291-69613efd103f?w=600",
        "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?w=600",
        "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600",
        "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600",
    ],
    "Headphones": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600",
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600",
        "https://images.unsplash.com/photo-1524678606370-a47ad25cb82a?w=600",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600",
        "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600",
    ],
    "Smart Watches": [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600",
        "https://images.unsplash.com/photo-1544117519-31a4b719223d?w=600",
        "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=600",
        "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600",
    ],
    "Cameras": [
        "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600",
        "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=600",
        "https://images.unsplash.com/photo-1502982720700-bfff97568df6?w=600",
        "https://images.unsplash.com/photo-1519183071298-a2962be96f83?w=600",
    ],
    "Speakers": [
        "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600",
        "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600",
        "https://images.unsplash.com/photo-1589003077984-894e133dabab?w=600",
        "https://images.unsplash.com/photo-1558537348-c0f8e733989d?w=600",
    ],
}

# (brand, series) pairs -> realistic, correctly matched product names
BRAND_SERIES = {
    "Laptops": [
        ("Dell", "Inspiron 15"), ("HP", "Pavilion 14"), ("Lenovo", "IdeaPad Slim 5"),
        ("ASUS", "Vivobook 15"), ("Acer", "Aspire 7"), ("Apple", "MacBook Air M2"),
        ("MSI", "Katana 15"), ("Lenovo", "ThinkPad E14"), ("ASUS", "ZenBook 14"),
        ("Acer", "Predator Helios 16"), ("Dell", "XPS 13"), ("HP", "Victus 15"),
    ],
    "Mobiles": [
        ("Samsung", "Galaxy M14"), ("Apple", "iPhone 14"), ("OnePlus", "Nord CE 3"),
        ("Xiaomi", "Redmi Note 13"), ("Realme", "Narzo 60"), ("Vivo", "V29"),
        ("Google", "Pixel 7a"), ("Samsung", "Galaxy S23"), ("Apple", "iPhone 15"),
        ("OnePlus", "12R"), ("Xiaomi", "13 Pro"), ("Realme", "GT 6"), ("Vivo", "T3x"),
    ],
    "Tablets": [
        ("Apple", "iPad 10th Gen"), ("Samsung", "Galaxy Tab A9"), ("Lenovo", "Tab M10"),
        ("Xiaomi", "Pad 6"), ("Realme", "Pad X"), ("Apple", "iPad Air"),
    ],
    "Accessories": [
        ("Logitech", "Wireless Mouse M185"), ("boAt", "Airdopes 141"),
        ("Anker", "PowerCore 10000mAh"), ("Portronics", "USB-C Hub 6-in-1"),
        ("Zebronics", "Wired Keyboard K120"), ("HP", "65W Fast Charger"),
        ("Logitech", "K380 Keyboard"), ("Anker", "PowerLine USB-C Cable"),
    ],
    "Headphones": [
        ("boAt", "Rockerz 450"), ("JBL", "Tune 510BT"), ("Sony", "WH-CH520"),
        ("Sennheiser", "HD 350BT"), ("Noise", "Buds VS104"), ("Skullcandy", "Indy Evo"),
        ("Apple", "AirPods 3rd Gen"), ("boAt", "Rockerz 550"), ("JBL", "C100SI"),
    ],
    "Smart Watches": [
        ("Noise", "ColorFit Pulse 2"), ("boAt", "Wave Call"), ("Apple", "Watch SE"),
        ("Samsung", "Galaxy Watch 6"), ("Fire-Boltt", "BSW003"), ("Amazfit", "Bip 3 Pro"),
        ("Noise", "ColorFit Ultra"),
    ],
    "Cameras": [
        ("Canon", "EOS 1500D"), ("Nikon", "D3500 DSLR"), ("Sony", "Alpha a6100"),
        ("Fujifilm", "X-T200 Mirrorless"), ("GoPro", "HERO11 Black"), ("Canon", "EOS M50"),
    ],
    "Speakers": [
        ("JBL", "Flip 6"), ("boAt", "Stone 350"), ("Sony", "SRS-XB13"),
        ("Zebronics", "Zeb-County"), ("Marshall", "Emberton II"), ("JBL", "Go 3"),
    ],
}

PRICE_RANGE = {
    "Laptops": (28000, 145000), "Mobiles": (9000, 130000), "Tablets": (12000, 75000),
    "Accessories": (399, 4500), "Headphones": (799, 25000), "Smart Watches": (1499, 35000),
    "Cameras": (24000, 95000), "Speakers": (1299, 22000),
}

TAGS = {
    "Laptops": ["coding", "programming", "student", "gaming", "business", "portable", "video editing", "multitasking"],
    "Mobiles": ["photography", "gaming", "camera", "student", "budget", "flagship", "battery life"],
    "Tablets": ["reading", "student", "drawing", "entertainment", "portable", "note-taking"],
    "Accessories": ["office", "productivity", "everyday use", "travel"],
    "Headphones": ["music", "bass", "travel", "gym", "calls", "noise cancellation"],
    "Smart Watches": ["fitness", "health tracking", "sports", "everyday use", "calls"],
    "Cameras": ["photography", "vlogging", "travel", "professional", "content creation"],
    "Speakers": ["music", "party", "outdoor", "home", "bass"],
}

DESC_TEMPLATES = {
    "Laptops": "The {brand} {series} is built for {tag}, featuring a crisp display, all-day battery life and fast storage for smooth multitasking.",
    "Mobiles": "The {brand} {series} delivers a vibrant display, a capable camera system and long-lasting battery, ideal for {tag}.",
    "Tablets": "The {brand} {series} is a lightweight tablet great for {tag}, with a large display and long battery backup.",
    "Accessories": "The {brand} {series} is a durable accessory designed for {tag}, combining convenience with dependable everyday performance.",
    "Headphones": "The {brand} {series} offers rich sound, deep bass and a comfortable fit, perfect for {tag}.",
    "Smart Watches": "The {brand} {series} tracks your health and fitness in style, ideal for {tag}, with an always-on display.",
    "Cameras": "The {brand} {series} captures stunning detail and color, a favorite among enthusiasts for {tag}.",
    "Speakers": "The {brand} {series} delivers punchy, room-filling sound, built for {tag} with long battery life.",
}

rows = []
pid = 1
CATS = list(BRAND_SERIES.keys())
per_cat = 100 // len(CATS)
target_counts = {c: per_cat for c in CATS}
remaining = 100 - per_cat * len(CATS)
for c in CATS[:remaining]:
    target_counts[c] += 1

for cat in CATS:
    n = target_counts[cat]
    pairs = BRAND_SERIES[cat]
    for i in range(n):
        brand, series = pairs[i % len(pairs)]
        name = f"{brand} {series}"
        low, high = PRICE_RANGE[cat]
        original_price = random.randint(low, high)
        original_price = round(original_price / 10) * 10
        discount_pct = random.choice([0, 5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40])
        discounted_price = int(original_price * (100 - discount_pct) / 100)
        rating = round(random.uniform(3.4, 4.9), 1)
        reviews = random.randint(23, 8600)
        stock = random.randint(0, 250)
        tags = random.sample(TAGS[cat], k=min(3, len(TAGS[cat])))
        tag_str = ", ".join(tags)
        desc = DESC_TEMPLATES[cat].format(brand=brand, series=series, tag=tags[0])
        image = IMAGES[cat][i % len(IMAGES[cat])]
        rows.append({
            "id": pid,
            "name": name,
            "brand": brand,
            "category": cat,
            "original_price": original_price,
            "discount_pct": discount_pct,
            "discounted_price": discounted_price,
            "rating": rating,
            "reviews": reviews,
            "stock": stock,
            "tags": tag_str,
            "description": desc,
            "image": image,
        })
        pid += 1

with open("datasets/products.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} products -> datasets/products.csv")
