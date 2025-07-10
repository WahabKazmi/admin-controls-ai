import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from store.factory import Store
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI + Store Setup ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

store = Store()

# --- Pydantic Request Schema ---
class MessageRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Hello from AI WooBot"}

# --- Chat Route ---
@app.post("/chat")
async def chat(req: MessageRequest):
    msg = req.message.strip()
    print("🗣️ User asked:", msg)

    try:
        if "show all products" in msg.lower():
            df = store.fetch_products()
            return {"response": df.to_markdown(index=False)}

        elif msg.lower().startswith("create product"):
            name = price = description = None
            name_match = re.search(r"name:\s*([^,]+)", msg, re.IGNORECASE)
            price_match = re.search(r"price:\s*([\d\.]+)", msg, re.IGNORECASE)
            desc_match = re.search(r"description:\s*([^,]+)", msg, re.IGNORECASE)

            if name_match: name = name_match.group(1).strip()
            if price_match: price = float(price_match.group(1).strip())
            if desc_match: description = desc_match.group(1).strip()

            if name and price:
                resp = store.create_product(name=name, price=price, description=description or "")
                return {"response": resp.get("message")}
            return {"response": "⚠️ Please provide at least product name and price."}

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

        elif msg.lower().startswith("search category"):
            category = msg.replace("search category", "", 1).strip().lower()
            df = store.fetch_products()
            filtered = df[df["categories"].str.lower().str.contains(category)]
            return {"response": filtered.to_markdown(index=False) if not filtered.empty else "⚠️ No products found."}

        elif msg.lower().startswith("create order"):
            match = re.match(r"create order (\w+) (\d+) (\d+) ([\d\.]+)", msg, re.IGNORECASE)
            if match:
                customer, pid, qty, total = match.groups()
                resp = store.create_order(customer=customer, product_id=int(pid), quantity=int(qty), total=float(total))
                return {"response": resp.get("message")}
            return {"response": "⚠️ Format: create order John 101 2 999"}

        elif msg.lower().startswith("update order"):
            match = re.match(r"update order (\d+) status to (\w+)", msg, re.IGNORECASE)
            if match:
                oid, status = match.groups()
                resp = store.update_order_status(int(oid), status)
                return {"response": resp.get("message")}
            return {"response": "⚠️ Format: update order 1 status to completed"}

        elif msg.lower().startswith("delete order"):
            match = re.match(r"delete order (\d+)", msg, re.IGNORECASE)
            if match:
                oid = int(match.group(1))
                resp = store.delete_order(oid)
                return {"response": resp.get("message")}
            return {"response": "⚠️ Format: delete order 1"}

        elif "get all orders" in msg.lower() or "show all orders" in msg.lower():
            df = store.fetch_orders()
            return {"response": df.to_markdown(index=False)}

        else:
            return {"response": "❓ Unrecognized command. Try: show all products / create product / delete order etc."}

    except Exception as e:
        print("🔥 Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend folder
app.mount("/client", StaticFiles(directory="client", html=True), name="client")
