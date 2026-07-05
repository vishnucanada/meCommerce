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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.cart_service import router as cart_router
from backend.product_service import router as products_router
from userAuth.auth_service import router as users_router

app = FastAPI(title="meCommerce API", version="0.1.0")

# CORS lets you host the frontend on a different origin (e.g. python -m http.server)
# and still call this API. Tighten allow_origins for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REST services -------------------------------------------------------
app.include_router(products_router)   # Product Service
app.include_router(cart_router)       # Cart Service
app.include_router(users_router)      # AuthN Service (add user)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Static frontend (mounted last so /api/* wins) -----------------------
FRONTEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
