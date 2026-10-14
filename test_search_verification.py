"""
Comprehensive verification test script for NovaCart Search
Tests all user-mandated searches:
- laptop, phone, mobile, Samsung, Apple, Nike
- shoes, running shoes, headphones, books, gaming, kitchen, beauty, grocery
- LAPTOP, Laptop, LaPtOp
- partial words: lap, head, sam, shoe
- search + filters: laptop + price, shoes + rating, Samsung + category, sorting
- empty search, no-result search
"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.models.product import search_products, get_all_products

def run_tests():
    all_products = get_all_products()
    print(f"Total catalog products: {len(all_products)}")

    tests = [
        # (Query, Category, MinPrice, MaxPrice, MinRating, SortBy, ExpectedMinResults, Description)
        ("laptop", None, None, None, None, None, 1, "laptop search"),
        ("phone", None, None, None, None, None, 1, "phone search (synonym Mobiles)"),
        ("mobile", None, None, None, None, None, 1, "mobile search"),
        ("Samsung", None, None, None, None, None, 1, "Samsung brand search"),
        ("Apple", None, None, None, None, None, 1, "Apple brand search"),
        ("Nike", None, None, None, None, None, 1, "Nike brand search"),
        ("shoes", None, None, None, None, None, 1, "shoes search (synonym Footwear)"),
        ("running shoes", None, None, None, None, None, 1, "running shoes (multi-word)"),
        ("headphones", None, None, None, None, None, 1, "headphones search (audio keywords)"),
        ("books", None, None, None, None, None, 1, "books search"),
        ("gaming", None, None, None, None, None, 1, "gaming search"),
        ("kitchen", None, None, None, None, None, 1, "kitchen search"),
        ("beauty", None, None, None, None, None, 1, "beauty search"),
        ("grocery", None, None, None, None, None, 1, "grocery search"),
        # Case variations
        ("LAPTOP", None, None, None, None, None, 1, "LAPTOP (uppercase)"),
        ("Laptop", None, None, None, None, None, 1, "Laptop (title case)"),
        ("LaPtOp", None, None, None, None, None, 1, "LaPtOp (mixed case)"),
        # Partial words
        ("lap", None, None, None, None, None, 1, "lap (partial for laptop)"),
        ("head", None, None, None, None, None, 1, "head (partial for headphone/headset)"),
        ("sam", None, None, None, None, None, 1, "sam (partial for Samsung)"),
        ("shoe", None, None, None, None, None, 1, "shoe (partial / singular)"),
        # Empty and whitespace
        ("", None, None, None, None, None, len(all_products), "empty search -> full catalog"),
        ("   ", None, None, None, None, None, len(all_products), "whitespace search -> full catalog"),
        # No results
        ("xyznonexistentterm123", None, None, None, None, None, 0, "nonexistent query -> 0 results"),
        # Search + Filter combinations
        ("laptop", None, 30000, 80000, None, None, 1, "laptop + price range (30k-80k)"),
        ("shoes", None, None, None, 4.2, None, 1, "shoes + rating (>=4.2)"),
        ("Samsung", "Mobiles & Accessories", None, None, None, None, 1, "Samsung + category filter"),
        ("laptop", None, None, None, None, "price_low", 1, "laptop + sort price_low"),
        ("laptop", None, None, None, None, "price_high", 1, "laptop + sort price_high"),
        ("running shoes", None, None, None, None, "rating", 1, "running shoes + sort rating"),
    ]

    all_passed = True
    print("\n" + "="*80)
    print(f"{'TEST DESCRIPTION':<35} | {'QUERY':<18} | {'RESULTS':<8} | {'STATUS'}")
    print("="*80)

    for q, cat, min_p, max_p, min_r, sort_b, expected_min, desc in tests:
        res = search_products(
            query=q,
            category=cat,
            min_price=min_p,
            max_price=max_p,
            min_rating=min_r,
            sort_by=sort_b
        )
        count = len(res)
        
        if desc == "nonexistent query -> 0 results":
            passed = (count == 0)
        elif desc in ("empty search -> full catalog", "whitespace search -> full catalog"):
            passed = (count == expected_min)
        else:
            passed = (count >= expected_min)

        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"{desc:<35} | {q:<18} | {count:<8} | {status}")

    print("="*80)
    if all_passed:
        print("ALL SEARCH VERIFICATION TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME TESTS FAILED - INSPECT LOGS ABOVE.")
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
