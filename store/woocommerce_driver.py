from .base import StoreDriver
from woocommerce import API
import pandas as pd

class WooCommerceDriver(StoreDriver):
    def __init__(self, *, url: str, consumer_key: str, consumer_secret: str):
        self.wcapi = API(
            url=url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3"
        )

    # --- Fetch All Orders ---
    def fetch_orders(self, **params) -> pd.DataFrame:
        resp = self.wcapi.get("orders", params=params or {"per_page": 20})
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame([{
            "id": o["id"],
            "status": o["status"],
            "total": o["total"],
            "customer": o.get("billing", {}).get("first_name", "Unknown"),
            "date": o["date_created"]
        } for o in data])

    # --- Create New Order ---
    def create_order(self, *, customer: str, product_id: int, quantity: int, total: float):
        order = {
            "status": "pending",
            "billing": {
                "first_name": customer,
                "last_name": "",
                "email": f"{customer.lower().replace(' ', '.')}_demo@example.com"
            },
            "line_items": [
                {"product_id": product_id, "quantity": quantity}
            ]
        }
        resp = self.wcapi.post("orders", data=order)
        resp.raise_for_status()
        result = resp.json()
        return {
            "id": result.get("id"),
            "message": f"🛒 Order created for {customer}, product {product_id}, quantity {quantity}, total ${total}."
        }

    # --- Update Order Status ---
    def update_order_status(self, order_id: int, new_status: str):
        resp = self.wcapi.put(f"orders/{order_id}", data={"status": new_status})
        resp.raise_for_status()
        return {
            "id": order_id,
            "message": f"✅ Order {order_id} updated to '{new_status}'."
        }

    # --- Delete Order ---
    def delete_order(self, order_id: int):
        resp = self.wcapi.delete(f"orders/{order_id}", params={"force": True})
        resp.raise_for_status()
        return {
            "id": order_id,
            "message": f"🗑️ Order {order_id} deleted successfully."
        }

    # --- Fetch All Products ---
    def fetch_products(self, **params) -> pd.DataFrame:
        resp = self.wcapi.get("products", params=params or {"per_page": 20})
        resp.raise_for_status()
        data = resp.json()
        return pd.DataFrame([{
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "status": p["status"],
            "stock_quantity": p.get("stock_quantity", 0),
            "categories": ", ".join(c["name"] for c in p.get("categories", [])),
            "description": p.get("description", ""),
            "image": p["images"][0]["src"] if p.get("images") else None
        } for p in data])

    # --- Create New Product ---
    def create_product(self, *, name: str, price: float, description: str = "", image_url: str = None):
        product = {
            "name": name,
            "type": "simple",
            "regular_price": str(price),
            "description": description,
            "status": "publish",
            "manage_stock": True,
            "stock_quantity": 10,
            "categories": [
                {"id": 15}  # You can update category ID if needed
            ]
        }

        if image_url:
            product["images"] = [{"src": image_url}]

        resp = self.wcapi.post("products", data=product)
        resp.raise_for_status()
        result = resp.json()
        return {
            "id": result.get("id"),
            "message": f"✅ Product '{name}' created with price ${price}."
        }

    # --- Update Product Fields ---
    def update_product(self, product_id: int, **fields):
        resp = self.wcapi.put(f"products/{product_id}", data=fields)
        resp.raise_for_status()
        return {
            "id": product_id,
            "message": f"✅ Product {product_id} updated: {fields}."
        }

    # --- Delete Product ---
    def delete_product(self, product_id: int):
        resp = self.wcapi.delete(f"products/{product_id}", params={"force": True})
        resp.raise_for_status()
        return {
            "id": product_id,
            "message": f"🗑️ Product {product_id} deleted successfully."
        }
