import os
import re
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from store.factory import Store
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime

# --- Load environment variables ---
load_dotenv()

# --- FastAPI app ---
app = FastAPI(title="WooCommerce AI Bot", version="1.0")

# --- CORS settings (frontend connect karne ke liye) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI model setup ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# --- WooCommerce store instance ---
store = Store()

# --- Request Schema ---
class MessageRequest(BaseModel):
    message: str

# --- Root route ---
@app.get("/")
async def root():
    return {"message": "WooCommerce AI Bot is running ✅"}

# =====================================================
# 📌 BUTTONS WALA API (Frontend buttons ke liye)
# =====================================================

@app.get("/api/products")
async def get_products(limit: int = 20):
    """Show All Products button ka API"""
    try:
        df = store.fetch_products(per_page=limit)
        return {"success": True, "count": len(df), "data": df.to_dict(orient="records")}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/orders")
async def get_orders(limit: int = 20):
    """Show All Orders button ka API"""
    try:
        df = store.fetch_orders(per_page=limit)
        return {"success": True, "count": len(df), "data": df.to_dict(orient="records")}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/orders/last")
async def get_last_order():
    """Show Last Order button ka API"""
    try:
        df = store.fetch_orders(per_page=1)
        if df.empty:
            return {"success": False, "error": "No orders found"}
        return {"success": True, "data": df.iloc[0].to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/products/best-selling")
async def get_best_selling_product_today():
    """Best Selling Product button ka API"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        best_selling = store.get_best_selling_product_today()
        if "message" in best_selling:
            return {"success": False, "error": best_selling["message"]}
        
        # Format data for frontend
        data = {
            "id": best_selling.get("product_id"),
            "name": best_selling.get("product_name"),
            "quantity_sold": best_selling.get("quantity_sold"),
            "total_sales": best_selling.get("total_sales"),
            # You can add SKU or price here if you want, but API must provide it
        }
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/products/out-of-stock")
async def get_out_of_stock_products():
    """Out of Stock Products button ka API"""
    try:
        df = store.fetch_products()
        if df.empty:
            return {"success": False, "error": "No products found"}
        out_of_stock = df[df["status"] == "outofstock"]
        return {"success": True, "count": len(out_of_stock), "data": out_of_stock.to_dict(orient="records")}
    except Exception as e:
        return {"success": False, "error": str(e)}

# =====================================================
# 📌 CHAT COMMAND API
# =====================================================
@app.post("/chat")
async def chat(req: MessageRequest):
    msg = req.message.strip()
    print("🗣️ User asked:", msg)

    try:
        if "show all products" in msg.lower():
            df = store.fetch_products()
            return {"response": df.to_markdown(index=False)}

        elif msg.lower().startswith("create product"):
            name_match = re.search(r"name:\s*([^,]+)", msg, re.IGNORECASE)
            price_match = re.search(r"price:\s*([\d\.]+)", msg, re.IGNORECASE)
            desc_match = re.search(r"description:\s*([^,]+)", msg, re.IGNORECASE)
            image_match = re.search(r"image:\s*(https?://[^\s,]+)", msg, re.IGNORECASE)

            name = name_match.group(1).strip() if name_match else None
            price = float(price_match.group(1).strip()) if price_match else None
            description = desc_match.group(1).strip() if desc_match else ""
            image = image_match.group(1).strip() if image_match else None

            if name and price:
                resp = store.create_product(name=name, price=price, description=description, image_url=image)
                return {"response": resp.get("message")}
            return {"response": "⚠️ Please provide product name and price."}

        elif msg.lower().startswith("update product"):
            match = re.match(r"update product (\d+) with (\w+)=([^\n]+)", msg, re.IGNORECASE)
            if match:
                pid, field, val = match.groups()
                val = val.strip('"\' ')
                if field == "price":
                    field = "regular_price"
                resp = store.update_product(int(pid), **{field: val})
                return {"response": f"✅ Product {pid} updated: {field} = {val}"}
            return {"response": "⚠️ Format: update product 123 with price=999"}

        elif msg.lower().startswith("delete product"):
            match = re.match(r"delete product (\d+)", msg, re.IGNORECASE)
            if match:
                pid = int(match.group(1))
                resp = store.delete_product(pid)
                return {"response": resp.get("message")}
            return {"response": "⚠️ Format: delete product 123"}

        elif "get all orders" in msg.lower() or "show all orders" in msg.lower():
            df = store.fetch_orders()
            return {"response": df.to_markdown(index=False)}

        elif msg.lower().startswith("create order"):
            match = re.match(r"create order (\w+) (\d+) (\d+) ([\d\.]+)", msg, re.IGNORECASE)
            if match:
                customer, pid, qty, total = match.groups()
                resp = store.create_order(customer=customer, product_id=int(pid), quantity=int(qty), total=float(total))
                return {"response": resp.get("message")}
            return {"response": "⚠️ Format: create order John 101 2 999"}

        elif msg.lower().startswith("delete order"):
            match = re.match(r"delete order\s+#?(\d+)", msg, re.IGNORECASE)
            if match:
                order_id = int(match.group(1))
                resp = store.delete_order(order_id)
                return {"response": resp.get("message")}
            return {"response": "⚠️ Format: delete order #1001"}

        else:
            response = await llm.ainvoke(msg)
            return {"response": response.content}

    except Exception as e:
        print("🔥 Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# --- Mount frontend static files ---
app.mount("/client", StaticFiles(directory="client", html=True), name="client")


# import os
# import re
# from fastapi import FastAPI, HTTPException, Query
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from store.factory import Store
# from langchain_google_genai import ChatGoogleGenerativeAI
# import pandas as pd

# load_dotenv()

# app = FastAPI()

# # --- CORS ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- AI + Store Setup ---
# llm = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     google_api_key=os.getenv("GOOGLE_API_KEY")
# )

# store = Store()

# # --- Request Schema ---
# class MessageRequest(BaseModel):
#     message: str

# class ProductCreateRequest(BaseModel):
#     name: str
#     price: float
#     description: str = ""
#     image_url: str = None
#     inventory: int = 10

# class OrderCreateRequest(BaseModel):
#     customer: str
#     product_id: int
#     quantity: int
#     total: float

# @app.get("/")
# async def root():
#     return {"message": "Shopify AI Assistant is running"}

# # --- Direct API Endpoints for UI Buttons ---
# @app.get("/api/products")
# async def get_products(
#     category: str = None,
#     status: str = None,
#     limit: int = 20
# ):
#     """Direct endpoint for products listing (used by UI buttons)"""
#     try:
#         params = {"per_page": limit}
#         if category:
#             params["category"] = category
#         if status:
#             params["status"] = status
            
#         df = store.fetch_products(**params)
        
#         # Convert DataFrame to list of dicts for JSON response
#         products = []
#         for _, row in df.iterrows():
#             product = {
#                 "id": row.get("id"),
#                 "name": row.get("name"),
#                 "price": row.get("price"),
#                 "status": row.get("status", "active"),
#                 "stock_quantity": row.get("stock_quantity", 0),
#                 "categories": row.get("categories", ""),
#                 "description": row.get("description", ""),
#                 "image": row.get("image")
#             }
#             products.append(product)
            
#         return {
#             "success": True,
#             "count": len(products),
#             "data": products
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }

# @app.post("/api/products/create")
# async def create_product_api(req: ProductCreateRequest):
#     """Direct endpoint for product creation (used by UI buttons)"""
#     try:
#         resp = store.create_product(
#             name=req.name,
#             price=req.price,
#             description=req.description,
#             image_url=req.image_url
#         )
        
#         # Update inventory if needed
#         if req.inventory > 0:
#             store.update_product(
#                 product_id=resp.get("id"),
#                 stock_quantity=req.inventory
#             )
            
#         return {
#             "success": True,
#             "message": resp.get("message"),
#             "product_id": resp.get("id")
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }

# @app.get("/api/orders")
# async def get_orders(
#     status: str = None,
#     limit: int = 20,
#     recent_days: int = None
# ):
#     """Direct endpoint for orders listing (used by UI buttons)"""
#     try:
#         params = {"per_page": limit}
#         if status:
#             params["status"] = status
            
#         df = store.fetch_orders(**params)
        
#         # Filter recent orders if requested
#         if recent_days:
#             recent_date = pd.Timestamp.now() - pd.Timedelta(days=recent_days)
#             df = df[pd.to_datetime(df['date']) >= recent_date]
        
#         # Convert DataFrame to list of dicts for JSON response
#         orders = []
#         for _, row in df.iterrows():
#             order = {
#                 "id": row.get("id"),
#                 "status": row.get("status"),
#                 "total": row.get("total"),
#                 "customer": row.get("customer", "Unknown"),
#                 "date": row.get("date"),
#                 "product_id": row.get("product_id", "")
#             }
#             orders.append(order)
            
#         return {
#             "success": True,
#             "count": len(orders),
#             "data": orders
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }

# @app.post("/api/orders/create")
# async def create_order_api(req: OrderCreateRequest):
#     """Direct endpoint for order creation (used by UI buttons)"""
#     try:
#         resp = store.create_order(
#             customer=req.customer,
#             product_id=req.product_id,
#             quantity=req.quantity,
#             total=req.total
#         )
        
#         return {
#             "success": True,
#             "message": resp.get("message"),
#             "order_id": resp.get("id")
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }

# @app.get("/api/store/stats")
# async def get_store_stats():
#     """Endpoint for dashboard statistics"""
#     try:
#         # Get products count
#         products_df = store.fetch_products(per_page=1)
#         products_count = len(products_df)
        
#         # Get orders count
#         orders_df = store.fetch_orders(per_page=1)
#         orders_count = len(orders_df)
        
#         # Get recent orders (last 7 days)
#         recent_date = pd.Timestamp.now() - pd.Timedelta(days=7)
#         recent_orders_df = store.fetch_orders()
#         recent_orders_count = len(recent_orders_df[pd.to_datetime(recent_orders_df['date']) >= recent_date])
        
#         return {
#             "success": True,
#             "data": {
#                 "products_count": products_count,
#                 "orders_count": orders_count,
#                 "recent_orders_count": recent_orders_count
#             }
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e)
#         }

# # --- Chat Endpoint (for text commands) ---
# @app.post("/chat")
# async def chat(req: MessageRequest):
#     msg = req.message.strip()
#     print("🗣️ User asked:", msg)

#     try:
#         if "show all products" in msg.lower() or "list products" in msg.lower():
#             df = store.fetch_products()
#             return {
#                 "response": df.to_markdown(index=False),
#                 "type": "products"
#             }

#         elif msg.lower().startswith("create product"):
#             # ... (keep your existing product creation logic)
#             pass

#         elif msg.lower().startswith("update product"):
#             # ... (keep your existing product update logic)
#             pass

#         elif msg.lower().startswith("delete product"):
#             # ... (keep your existing product deletion logic)
#             pass

#         elif "search category" in msg.lower():
#             # ... (keep your existing category search logic)
#             pass

#         elif "show all orders" in msg.lower() or "list orders" in msg.lower():
#             df = store.fetch_orders()
#             return {
#                 "response": df.to_markdown(index=False),
#                 "type": "orders"
#             }

#         elif msg.lower().startswith("create order"):
#             # ... (keep your existing order creation logic)
#             pass

#         elif msg.lower().startswith("update order"):
#             # ... (keep your existing order update logic)
#             pass

#         elif msg.lower().startswith("delete order"):
#             # ... (keep your existing order deletion logic)
#             pass

#         else:
#             # Fallback to AI for other queries
#             response = await llm.ainvoke(msg)
#             return {
#                 "response": response.content,
#                 "type": "ai"
#             }

#     except Exception as e:
#         print("🔥 Error:", str(e))
#         raise HTTPException(status_code=500, detail=str(e))

# # Mount frontend
# app.mount("/client", StaticFiles(directory="client", html=True), name="client")