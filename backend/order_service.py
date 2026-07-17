"""Order Service — turns a cart into a persisted, paid order.

Maps to the "Order Service" box in mock-diagram.png. Checkout flow:
  1. Read the server-authoritative cart (Cart Service).
  2. Charge it through the Payment Service (mock gateway).
  3. Persist the order in the SQL store ("Users and Orders" in the diagram).
  4. Clear the cart.

Totals come from the cart, never from the client, so pricing can't be tampered
with. In one process today; splittable behind the gateway later without changing
the route contract.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import cart_service, payment_service
from database import db
from userAuth.auth_service import PublicUser, optional_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


class CheckoutIn(BaseModel):
    cart_id: str
    username: str | None = None
    method: str = "card"


@router.post("", status_code=201)
def create_order(
    payload: CheckoutIn,
    user: PublicUser | None = Depends(optional_user),
):
    """Check out a cart: charge it, persist the order, then empty the cart.

    If the request carries a valid session token, the order is tied to that
    authenticated user — the token wins over any client-supplied username, the
    same way pricing is taken from the server-side cart, not the client. Guests
    (no token) can still check out with the optional `username`."""
    username = user.username if user else payload.username

    cart = cart_service.get_cart(payload.cart_id)
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")

    payment = payment_service.charge(cart["total"], payload.method)
    if payment["status"] != "captured":
        raise HTTPException(status_code=402, detail="Payment declined")

    order = {
        "id": uuid.uuid4().hex,
        "cart_id": payload.cart_id,
        "username": username,
        "items": cart["items"],
        "subtotal": cart["subtotal"],
        "shipping": cart["shipping"],
        "total": cart["total"],
        "payment_id": payment["payment_id"],
        "status": "paid",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.insert_order(order)
    cart_service.clear_cart(payload.cart_id)
    return order


@router.get("/{order_id}")
def get_order(order_id: str):
    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("")
def list_orders():
    """Demo/debug endpoint to see placed orders."""
    return db.list_orders()
