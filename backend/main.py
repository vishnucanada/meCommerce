"""meCommerce API — application entrypoint.

Wires the REST services together and (for convenient local dev) also serves the
static frontend. Run from the repo root:

    pip install -r backend/requirements.txt
    uvicorn backend.main:app --reload

Then open http://localhost:8000  (interactive API docs at /docs).

Architecture note: each router below maps to a separate service box in
mock-diagram.png. Here they run in one process for simplicity; splitting them
into independent services behind the API Gateway later is a deployment change,
not a code rewrite — the routes stay identical.
"""
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.cart_service import router as cart_router
from backend.order_service import router as orders_router
from backend.payment_service import router as payments_router
from backend.product_service import router as products_router
from backend.recommendation_service import router as recommendations_router
from database import db
from userAuth import auth_service
from userAuth.auth_service import auth_router, router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the SQLite databases and seed them with mock data before serving.
    db.init_databases()            # products.db (+ catalog), users.db schema
    auth_service.seed_mock_users()  # mock accounts in users.db
    yield


app = FastAPI(title="meCommerce API", version="0.1.0", lifespan=lifespan)

# CORS lets you host the frontend on a different origin (e.g. python -m http.server)
# and still call this API. Tighten allow_origins for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REST services -------------------------------------------------------
app.include_router(products_router)         # Product Service
app.include_router(cart_router)             # Cart Service
app.include_router(users_router)            # AuthN Service (add user)
app.include_router(recommendations_router)  # Recommendation Service
app.include_router(payments_router)         # Payment Service
app.include_router(orders_router)           # Order Service


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Static frontend (mounted last so /api/* wins) -----------------------
FRONTEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
