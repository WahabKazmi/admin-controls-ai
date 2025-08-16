from .base import StoreDriver
import pandas as pd
import requests

class ShopifyDriver(StoreDriver):
    def __init__(self, *, shop_url: str, access_token: str):
        self.base_url = f"https://{shop_url}/admin/api/2023-04"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }

    # ---------- PRODUCTS ----------
    def fetch_products(self, **params) -> pd.DataFrame:
        url = f"{self.base_url}/products.json"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json().get("products", [])
        return pd.DataFrame([{
            "id": p["id"],
            "name": p["title"],
            "price": p["variants"][0]["price"] if p["variants"] else None,
            "status": "active",
            "stock_quantity": p["variants"][0].get("inventory_quantity", 0),
            "categories": ", ".join(p.get("tags", "").split(",")),
            "description": p.get("body_html", ""),
            "image": p["image"]["src"] if p.get("image") else None
        } for p in data])

    def create_product(self, *, name: str, price: float, description: str = "", image_url: str = None):
        product_data = {
            "product": {
                "title": name,
                "body_html": description,
                "variants": [{"price": str(price)}]
            }
        }

        if image_url:
            product_data["product"]["images"] = [{"src": image_url}]

        url = f"{self.base_url}/products.json"
        response = requests.post(url, headers=self.headers, json=product_data)
        response.raise_for_status()
        result = response.json().get("product", {})
        return {
            "id": result.get("id"),
            "message": f"✅ Product '{name}' created with price ${price}."
        }

    def update_product(self, product_id: int, **fields):
        url = f"{self.base_url}/products/{product_id}.json"
        update_data = {"product": {"id": product_id}}

        if "price" in fields:
            update_data["product"]["variants"] = [{"price": str(fields["price"])}]
            del fields["price"]

        update_data["product"].update(fields)

        response = requests.put(url, headers=self.headers, json=update_data)
        response.raise_for_status()
        return {
            "id": product_id,
            "message": f"✅ Product {product_id} updated: {fields}."
        }

    def delete_product(self, product_id: int):
        url = f"{self.base_url}/products/{product_id}.json"
        response = requests.delete(url, headers=self.headers)

        if response.status_code == 200:
            return {
                "id": product_id,
                "message": f"🗑️ Product {product_id} deleted successfully."
            }
        elif response.status_code == 404:
            return {
                "id": product_id,
                "message": f"⚠️ Product {product_id} not found."
            }
        else:
            response.raise_for_status()

    # ---------- ORDERS ----------
    def fetch_orders(self, **params) -> pd.DataFrame:
        url = f"{self.base_url}/orders.json"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json().get("orders", [])
        return pd.DataFrame([{
            "id": o["id"],
            "status": o["financial_status"],
            "total": o["total_price"],
            "customer": o.get("customer", {}).get("first_name", "Unknown"),
            "date": o["created_at"]
        } for o in data])

    def create_order(self, *, customer: str, product_id: int, quantity: int, total: float):
        # Step 1: Get variant ID from product
        product_url = f"{self.base_url}/products/{product_id}.json"
        product_resp = requests.get(product_url, headers=self.headers)
        product_resp.raise_for_status()
        product_data = product_resp.json().get("product", {})
        variants = product_data.get("variants", [])

        if not variants:
            raise ValueError("❌ No variants found for this product.")

        variant_id = variants[0]["id"]

        # Step 2: Try to get customer ID by first name
        customers_url = f"{self.base_url}/customers/search.json?query=first_name:{customer}"
        cust_resp = requests.get(customers_url, headers=self.headers)
        cust_resp.raise_for_status()
        customers = cust_resp.json().get("customers", [])

        if customers:
            customer_id = customers[0]["id"]
            customer_data = {"id": customer_id}
        else:
            customer_data = {"first_name": customer}  # guest

        # Step 3: Create the order
        order_data = {
            "order": {
                "line_items": [{"variant_id": variant_id, "quantity": quantity}],
                "customer": customer_data,
                "financial_status": "pending"
            }
        }

        url = f"{self.base_url}/orders.json"
        response = requests.post(url, headers=self.headers, json=order_data)
        response.raise_for_status()
        result = response.json().get("order", {})
        return {
            "id": result.get("id"),
            "message": f"🛒 Order created for {customer}, product {product_id}, quantity {quantity}, total ${total}."
        }

    def update_order_status(self, order_id: int, new_status: str):
        url = f"{self.base_url}/orders/{order_id}.json"
        update_data = {
            "order": {
                "id": order_id,
                "financial_status": new_status
            }
        }
        response = requests.put(url, headers=self.headers, json=update_data)
        if response.status_code == 404:
            return {
                "id": order_id,
                "message": f"⚠️ Order {order_id} not found."
            }
        response.raise_for_status()
        return {
            "id": order_id,
            "message": f"✅ Order {order_id} updated to '{new_status}'."
        }

    def delete_order(self, order_id: int):
        url = f"{self.base_url}/orders/{order_id}.json"
        response = requests.delete(url, headers=self.headers)

        if response.status_code == 200:
            return {
                "id": order_id,
                "message": f"🗑️ Order {order_id} deleted successfully."
            }
        elif response.status_code == 404:
            return {
                "id": order_id,
                "message": f"⚠️ Order {order_id} not found."
            }
        else:
            response.raise_for_status()
