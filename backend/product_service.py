"""Product Service — read-only catalog endpoints.

Maps to the "Product Service" box in mock-diagram.png. The frontend calls these
to render the grid; it never sees the data source.
"""
from fastapi import APIRouter, HTTPException

from .data import PRODUCTS, PRODUCTS_BY_ID

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def list_products(grade: str | None = None):
    """Return the catalog, optionally filtered by grade (ceremonial/premium/culinary)."""
    if grade and grade != "all":
        return [p for p in PRODUCTS if p["grade"] == grade]
    return PRODUCTS


@router.get("/{product_id}")
def get_product(product_id: str):
    product = PRODUCTS_BY_ID.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
