from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Data validation model for incoming request data
class Product(BaseModel):
    name: str
    price: float
    in_stock: bool

# Simulated in-memory database
database = {
    1: {"name": "Laptop", "price": 999.99, "in_stock": True},
    2: {"name": "Mouse", "price": 24.99, "in_stock": False}
}

# 1. READ ALL (GET)
@app.get("/products")
def get_all_products():
    return database

# 2. READ ONE (GET)
@app.get("/products/{product_id}")
def get_product(product_id: int):
    if product_id not in database:
        raise HTTPException(status_code=404, detail="Product not found")
    return database[product_id]

# 3. CREATE (POST)
@app.post("/products")
def create_product(product: Product):
    new_id = max(database.keys()) + 1 if database else 1
    database[new_id] = product.model_dump()
    return {"message": "Product created successfully", "id": new_id, "data": database[new_id]}

# 4. UPDATE (PUT)
@app.put("/products/{product_id}")
def update_product(product_id: int, product: Product):
    if product_id not in database:
        raise HTTPException(status_code=404, detail="Product not found")
    database[product_id] = product.model_dump()
    return {"message": f"Product {product_id} updated successfully", "data": database[product_id]}

# 5. DELETE (DELETE)
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    if product_id not in database:
        raise HTTPException(status_code=404, detail="Product not found")
    deleted_item = database.pop(product_id)
    return {"message": f"Product {product_id} deleted successfully", "deleted": deleted_item}
