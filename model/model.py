"""Recommendation Service — content-based "similar teas" for the catalog.

Maps to the "Recommendation" box in mock-diagram.png. Given a product, it ranks
the rest of the matcha catalog by content similarity (grade + tasting notes) and
returns the closest matches. Reads the catalog through the database layer so it
stays in sync with the Product Service — no separate copy of the data.

Pure-Python cosine over a bag of words; no ML dependencies needed at mock scale.
Swap in the diagram's ML Model later without changing the caller — the
`recommend()` contract stays the same.
"""
import math
import re
from collections import Counter

from database import db

_TOKEN = re.compile(r"[a-z]+")


def _tokens(product: dict) -> Counter:
    """Bag of words for a product. Grade is weighted (repeated) so matches stay
    within the same tier (ceremonial recommends ceremonial, etc.)."""
    text = f"{product['grade']} {product['grade']} {product['notes']}"
    return Counter(_TOKEN.findall(text.lower()))


def _cosine(a: Counter, b: Counter) -> float:
    shared = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in shared)
    if not dot:
        return 0.0
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    return dot / (norm_a * norm_b)


def recommend(product_id: str, top_n: int = 2) -> list[dict]:
    """Return up to top_n catalog products most similar to product_id.

    Empty list if the product is unknown or nothing overlaps."""
    target = db.get_product(product_id)
    if target is None:
        return []
    target_vec = _tokens(target)
    scored = [
        (_cosine(target_vec, _tokens(other)), other)
        for other in db.query_products()
        if other["id"] != product_id
    ]
    scored.sort(key=lambda s: s[0], reverse=True)
    return [product for score, product in scored[:top_n] if score > 0]
