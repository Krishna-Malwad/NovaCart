# NovaCart

An AI-powered e-commerce web app for electronics, inspired by Amazon and Flipkart — built with Flask, vanilla JS/CSS, and a real (if small) machine-learning recommendation engine. No Bootstrap, no Tailwind, no React — every pixel is custom.

---

## ✨ Features

- **Full shopping flow** — browse, search & filter, product detail, cart, wishlist, checkout, order confirmation
- **NOVA AI** — a natural-language shopping assistant. Ask it things like:
  - `best laptop under ₹80000`
  - `best phone for photography`
  - `headphones for gym`
  - `compare iPhone and Samsung`
  - `is this good for students?` (while viewing a product)

  NOVA parses budget, category, and use-case intent from your sentence with rule-based NLP and queries the real product database — there are no scripted/canned replies.
- **Explainable recommendations** — a TF-IDF + cosine-similarity model (scikit-learn) suggests related products on every product page, each with a **match %** and a plain-English reason ("same brand", "shared use-case: gaming", etc.)
- **Analytics dashboard** — revenue, orders, customers, average rating, top products, revenue by category, and monthly sales — all computed live from real order data in SQLite
- **100 realistic products** across 8 categories with proper brand/model pairing, INR pricing, ratings, discounts and stock levels
- Fully responsive, dark navbar + blue-accent design, rounded cards, smooth hover animations

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Templates | Jinja2 |
| Frontend | HTML5, CSS3 (custom), Vanilla JavaScript |
| Data | Pandas (dataset generation), SQLite (storage) |
| Machine Learning | scikit-learn (TF-IDF, cosine similarity) |

---

## 📦 Installation

**Requirements:** Python 3.9+

```bash
# 1. Unzip / clone the project, then move into it
cd NovaCart

# 2. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## ▶️ How to Run

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

The SQLite database (`database.db`) is created and seeded automatically from `datasets/products.csv` the first time the app starts — no manual setup needed. To regenerate the dataset from scratch, run `python scripts_gen_dataset.py` and delete `database.db` before restarting the app.

---

## 📁 Folder Structure

```
NovaCart/
├── app.py                    # Entry point — run this to start the server
├── config.py                 # Central configuration (GST rate, delivery fee, etc.)
├── requirements.txt
├── README.md
├── scripts_gen_dataset.py    # One-time generator for datasets/products.csv
│
├── app/
│   ├── __init__.py           # Flask app factory, blueprint registration
│   ├── database.py           # SQLite connection + schema + seeding
│   ├── models/
│   │   ├── product.py        # Product queries (search, filters, featured, etc.)
│   │   └── order.py          # Order persistence & retrieval
│   ├── routes/
│   │   ├── main.py           # Home page, product detail page
│   │   ├── search.py         # Search & filter page
│   │   ├── cart.py           # Cart add/update/remove
│   │   ├── wishlist.py       # Wishlist add/remove/move-to-cart
│   │   ├── checkout.py       # Checkout + order confirmation
│   │   ├── analytics.py      # Analytics dashboard route
│   │   └── api.py            # /api/nova — NOVA AI JSON endpoint
│   ├── ml/
│   │   └── recommender.py    # TF-IDF + cosine similarity recommendation engine
│   ├── ai/
│   │   └── assistant.py      # NOVA AI natural-language parsing & response logic
│   ├── analytics/
│   │   └── dashboard.py      # SQL aggregations for the analytics dashboard
│   └── utils/
│       └── helpers.py        # Session-based cart/wishlist + pricing calculations
│
├── templates/                # Jinja2 templates (base, index, product, search, cart, ...)
├── static/
│   ├── css/style.css         # All custom styling — no framework
│   ├── js/main.js            # Cart/wishlist/UI interactions
│   └── js/nova.js            # NOVA AI chat widget frontend
└── datasets/
    └── products.csv          # 100-row product dataset
```

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `products` | Full product catalogue (seeded from CSV) |
| `users` | Reserved for future login/auth support |
| `cart` | Table exists for future persistent-cart support (active cart currently lives in the Flask session for a login-free demo experience) |
| `wishlist` | Same as above |
| `orders` | Every placed order — customer info, totals, payment method |
| `order_items` | Line items belonging to each order |

> **Note on session-based cart/wishlist:** Since NovaCart has no login system (by design, to keep the demo frictionless), the *active* cart and wishlist are stored in the browser's signed session cookie rather than tied to a `user_id`. Placed **orders** are always written permanently to SQLite, which is what powers the Analytics Dashboard.

---

## 🤖 How NOVA AI Works

NOVA is a rule-based NLP assistant (not an LLM call) that:
1. Extracts a **budget** from phrases like "under 80000", "budget 50k", "between 20000 and 40000", "₹1.2 lakh"
2. Extracts a **category** from keywords (laptop, phone, headphones, camera, etc.) using word-boundary matching so "headphones" isn't mistaken for "phone"
3. Extracts a **use-case** from keywords (coding, gaming, photography, fitness, travel, etc.) matched against each product's tags
4. Detects **comparison intent** ("compare X and Y", "X vs Y") and builds a side-by-side comparison
5. Answers **contextual questions** ("is this good for students?") using whichever product page you're currently viewing
6. Falls back to a general keyword search across name/brand/category/tags/description

Every response is generated live from the SQLite product table — nothing is hard-coded.

## 🎯 How the Recommendation Engine Works

For each product, NovaCart builds a "content" string from its category, brand, tags, and description, then vectorises every product with **TF-IDF**. On any product page, it computes **cosine similarity** between the current product and all others, returning the top matches with:
- A **match %** (the similarity score, scaled to 0–100)
- A **plain-English reason** (same category / same brand / shared use-case tags)

This keeps the model simple, fast, and fully explainable — a good fit for a small catalogue and for learning purposes.

---

## 🚀 Future Scope

- User authentication (login/signup) with per-user persistent cart, wishlist, and order history
- Real payment gateway integration (Razorpay/Stripe test mode)
- Product reviews & ratings submission
- Admin panel for managing inventory and viewing analytics
- Pagination / infinite scroll on search results
- Upgrade NOVA AI to call a real LLM API for richer conversational ability
- Email notifications on order confirmation
- Dockerized deployment

---

## 📸 Screenshots

*(Add your own screenshots here after running the app locally)*

- `Homepage.png` — Hero section, featured/trending/deals
- `ProductPage.png` — Product detail with recommendations
- `SearchPage.png` — Filters and sorting
- `Cart.png` — Shopping cart with live totals
- `NovaAI.png` — NOVA AI chat widget in action
- `Analytics.png` — Analytics dashboard

---

## ⚠️ Disclaimer

This is a learning/portfolio project. It is **not** a real e-commerce store — there is no real payment processing, no real user accounts, and all product data is synthetically generated for demonstration purposes.
