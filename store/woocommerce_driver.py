from .base import StoreDriver
from woocommerce import API
import pandas as pd
from datetime import datetime

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

    # --- Get Last Order ---
    def get_last_order(self) -> dict:
        resp = self.wcapi.get(
            "orders",
            params={"per_page": 1, "orderby": "date", "order": "desc"}
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return {"message": "⚠️ No orders found."}
        order = data[0]
        return {
            "id": order["id"],
            "status": order["status"],
            "total": order["total"],
            "customer": order.get("billing", {}).get("first_name", "Unknown"),
            "date": order["date_created"]
        }

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
                {"id": 15}  # Change as per your store categories
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

    # --- Update Product ---
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

    # --- Out of Stock Products ---
    def get_out_of_stock_products(self) -> pd.DataFrame:
        resp = self.wcapi.get("products", params={"stock_status": "outofstock", "per_page": 50})
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return pd.DataFrame([{"message": "✅ No products are out of stock."}])
        return pd.DataFrame([{
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "stock_quantity": p.get("stock_quantity", 0)
        } for p in data])

    # --- Best Selling Product Today ---
    def get_best_selling_product_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        resp = self.wcapi.get(
            "reports/top_sellers",
            params={"date_min": today, "date_max": today, "per_page": 1}
        )
        resp.raise_for_status()
        data = resp.json()

        # Debug print for API response - remove or comment out in production
        print("DEBUG: Best selling products API response:", data)

        # WooCommerce API response might be dict with "top_sellers" or list
        if isinstance(data, dict):
            top_sellers = data.get("top_sellers") or data.get("data") or []
        else:
            top_sellers = data

        if not top_sellers:
            return {"message": "⚠️ No sales found for today."}

        best = top_sellers[0]

        return {
            "product_id": best.get("product_id"),
            "product_name": best.get("name") or best.get("product_name") or "Unknown",
            "quantity_sold": best.get("quantity") or best.get("total_sales") or 0,
            "total_sales": best.get("total") or 0
        }
