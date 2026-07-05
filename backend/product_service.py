"""Product Service — read-only catalog endpoints.

Maps to the "Product Service" box in mock-diagram.png. Reads from products.db
via the database layer; the frontend never sees the data source.
"""
from fastapi import APIRouter, HTTPException

from database import db

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def list_products(grade: str | None = None):
    """Return the catalog, optionally filtered by grade (ceremonial/premium/culinary)."""
    return db.query_products(grade)


@router.get("/{product_id}")
def get_product(product_id: str):
    product = db.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
