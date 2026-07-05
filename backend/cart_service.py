"""Cart Service — server-authoritative shopping cart.

Maps to the "Cart Service" box in mock-diagram.png. The cart is keyed by a
`cart_id` the browser generates and stores in localStorage. Totals and the
shipping rule are computed here (server-side) so the frontend can't be trusted
with pricing. State is an in-memory dict for the mock; back it with the NoSQL /
Cache tier for real use.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .data import PRODUCTS_BY_ID

router = APIRouter(prefix="/api/cart", tags=["cart"])

FREE_SHIPPING_THRESHOLD = 40
FLAT_SHIPPING = 5

# cart_id -> {product_id: qty}
_carts: dict[str, dict[str, int]] = {}


class CartItemIn(BaseModel):
    product_id: str
    qty: int = Field(default=1, ge=-99, le=99)


def _render(cart_id: str) -> dict:
    """Build the full cart view: line items + computed totals."""
    items = _carts.get(cart_id, {})
    lines, subtotal = [], 0
    for pid, qty in items.items():
        product = PRODUCTS_BY_ID.get(pid)
        if not product or qty <= 0:
            continue
        line_total = product["price"] * qty
        subtotal += line_total
        lines.append({**product, "qty": qty, "line_total": line_total})

    shipping = 0 if (subtotal == 0 or subtotal >= FREE_SHIPPING_THRESHOLD) else FLAT_SHIPPING
    return {
        "cart_id": cart_id,
        "items": lines,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": subtotal + shipping,
    }


@router.get("/{cart_id}")
def get_cart(cart_id: str):
    return _render(cart_id)


@router.post("/{cart_id}/items")
def add_item(cart_id: str, item: CartItemIn):
    """Add (or, with a negative qty, decrement) a product in the cart."""
    if item.product_id not in PRODUCTS_BY_ID:
        raise HTTPException(status_code=404, detail="Product not found")
    cart = _carts.setdefault(cart_id, {})
    cart[item.product_id] = cart.get(item.product_id, 0) + item.qty
    if cart[item.product_id] <= 0:
        cart.pop(item.product_id, None)
    return _render(cart_id)


@router.delete("/{cart_id}/items/{product_id}")
def remove_item(cart_id: str, product_id: str):
    _carts.get(cart_id, {}).pop(product_id, None)
    return _render(cart_id)
