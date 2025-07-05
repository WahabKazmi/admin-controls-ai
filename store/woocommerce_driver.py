# store/woocommerce_driver.py
from .base import StoreDriver
from woocommerce import API
import pandas as pd

class WooCommerceDriver(StoreDriver):
    def __init__(self, *, url: str, consumer_key: str, consumer_secret: str):
        self.wcapi = API(url=url, consumer_key=consumer_key,
                         consumer_secret=consumer_secret, version="wc/v3")

    # ---- Orders ----
    def fetch_orders(self, **params) -> pd.DataFrame:
        resp = self.wcapi.get("orders", params=params or {"per_page": 20})
        data = resp.json()
        return pd.DataFrame([{
            "id": o["id"],
            "status": o["status"],
            "total": o["total"],
            "customer": o.get("billing", {}).get("first_name", "Unknown"),
            "date": o["date_created"],
        } for o in data])

    def create_order(self, *, customer: str, product_id: int,
                     quantity: int, total: float):
        order = {
            "status": "pending",
            "billing": {"first_name": customer, "last_name": "",
                        "email": f"{customer.lower().replace(' ', '.')}_demo@example.com"},
            "line_items": [{"product_id": product_id, "quantity": quantity}],
            "total": total,
        }
        resp = self.wcapi.post("orders", order)
        resp.raise_for_status()
        return resp.json()

    def update_order_status(self, order_id: int, new_status: str):
        resp = self.wcapi.put(f"orders/{order_id}", data={"status": new_status})
        resp.raise_for_status()
        return resp.json()

    # ---- Products ----
    def fetch_products(self, **params):
        resp = self.wcapi.get("products", params=params or {"per_page": 20})
        data = resp.json()
        return pd.DataFrame([{
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "status": p["status"],
            "stock_quantity": p.get("stock_quantity", 0),
            "categories": ", ".join(c["name"] for c in p.get("categories", [])),
        } for p in data])

    def create_product(self, *, name: str, price: float, description: str = ""):
        product = {"name": name, "type": "simple", "regular_price": str(price),
                   "description": description, "status": "publish"}
        resp = self.wcapi.post("products", product)
        resp.raise_for_status()
        return resp.json()

    def update_product(self, product_id: int, **fields):
        resp = self.wcapi.put(f"products/{product_id}", data=fields)
        resp.raise_for_status()
        return resp.json()
