"""Payment Service — mock card authorization + capture.

Maps to the "Payment Service" box in mock-diagram.png. A real deployment calls an
external payment gateway (through the External APIs / Event Bus); here we mock the
authorize -> capture handshake so the Order Service has something to call. Any
positive amount is captured; pass method="declined" to exercise the failure path.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/payments", tags=["payments"])


class PaymentIn(BaseModel):
    amount: float
    method: str = "card"


def charge(amount: float, method: str = "card") -> dict:
    """Mock authorize + capture. Returns a payment record whose status is
    'captured' on success, or 'declined' for a non-positive amount or
    method='declined'."""
    captured = amount > 0 and method != "declined"
    return {
        "payment_id": uuid.uuid4().hex,
        "amount": amount,
        "method": method,
        "status": "captured" if captured else "declined",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("")
def create_payment(payload: PaymentIn):
    """Charge a payment directly. Also called in-process by the Order Service."""
    return charge(payload.amount, payload.method)
