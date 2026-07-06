"""Recommendation Service — "you might also like" for the catalog.

Maps to the "Recommendation" box in mock-diagram.png. A thin REST wrapper over
the content-based recommender in model/model.py; it reads the catalog via the
database layer, so it never holds its own copy of the products.
"""
from fastapi import APIRouter

from model.model import recommend

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/{product_id}")
def recommendations(product_id: str, limit: int = 2):
    """Return products similar to product_id (empty list if it's unknown)."""
    return recommend(product_id, top_n=limit)
