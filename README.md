# meCommerce
meCommerce or Mini E-Commerce is a mini project aimed to demonstrate solutions architect principles in a monolithic repository. The idea uses a mock diagram to mimic the internal application of a e-Commerce website would function.
![Mock Diagram](https://github.com/vishnucanada/meCommerce/blob/main/mock-diagran.png?raw=1)

## Running locally

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload      # run from the repo root
```

Then open **http://localhost:8000** (interactive API docs at **/docs**).

## How it's wired

The frontend is presentation-only and talks to the backend over a REST API —
it holds no product data or pricing of its own. Each backend router maps to a
service box in `mock-diagram.png`:

| Folder                        | Role in the diagram        | Endpoints |
|-------------------------------|----------------------------|-----------|
| `frontend/`                   | Frontend (Web)             | Static `index.html`; calls `/api/*` via `fetch()` |
| `backend/product_service.py`  | Product Service            | `GET /api/products`, `GET /api/products/{id}` |
| `backend/cart_service.py`     | Cart Service               | `GET/POST /api/cart/{cart_id}`, item add/remove |
| `userAuth/auth_service.py`    | User Auth (AuthN)          | `POST /api/users` (add user), `GET /api/users` |
| `backend/main.py`             | API Gateway + Web Server   | Mounts the routers and serves the frontend |

Data stores are in-memory for the mock; swap them for the NoSQL / SQL tiers in
the diagram without changing the route contracts. For now everything runs in one
process; each service can later be split into its own deployable behind the
gateway — that's a deployment change, not a code rewrite.
