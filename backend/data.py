"""In-memory product catalog.

In the target architecture (see mock-diagram.png) the Product Service reads this
from the NoSQL database. For the mock it's a plain Python list so the app runs
with zero external dependencies. Swap `PRODUCTS` for a real DB query later
without touching product_service.py's route signatures.
"""

PRODUCTS = [
    {"id": "uji", "name": "Uji Ceremonial", "region": "Kyoto · Uji",
     "grade": "ceremonial", "gradeLabel": "Ceremonial", "price": 32,
     "notes": "Sweet, deep umami, no bitterness", "label": "#eaf0d6", "dot": "#4b6b1f"},
    {"id": "okumidori", "name": "Okumidori Reserve", "region": "Kyoto · Wazuka",
     "grade": "ceremonial", "gradeLabel": "Ceremonial", "price": 38,
     "notes": "Creamy, floral, vivid green", "label": "#e2ecd0", "dot": "#3d5c18"},
    {"id": "yame", "name": "Yame Premium", "region": "Fukuoka · Yame",
     "grade": "premium", "gradeLabel": "Premium", "price": 26,
     "notes": "Balanced, nutty, smooth finish", "label": "#edf1dd", "dot": "#6a8a30"},
    {"id": "nishio", "name": "Nishio Daily", "region": "Aichi · Nishio",
     "grade": "premium", "gradeLabel": "Premium", "price": 22,
     "notes": "Bright, grassy, everyday cup", "label": "#eef2df", "dot": "#7a9a3e"},
    {"id": "culinary", "name": "Culinary Blend", "region": "Kagoshima",
     "grade": "culinary", "gradeLabel": "Culinary", "price": 18,
     "notes": "Bold, for lattes and baking", "label": "#e6ecd4", "dot": "#556b28"},
    {"id": "barista", "name": "Barista Latte", "region": "Uji blend",
     "grade": "culinary", "gradeLabel": "Culinary", "price": 20,
     "notes": "Rich, froths well, latte-ready", "label": "#e9efd8", "dot": "#607d2c"},
]

# id -> product, for O(1) lookups by the Cart Service.
PRODUCTS_BY_ID = {p["id"]: p for p in PRODUCTS}
