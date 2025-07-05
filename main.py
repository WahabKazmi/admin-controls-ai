# main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_experimental.agents import create_pandas_dataframe_agent
from store.factory import Store
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to ["http://127.0.0.1:5500"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = Store()
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))

orders_df_cache = products_df_cache = None
orders_agent = products_agent = None

class MessageRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/chat")
async def chat(req: MessageRequest):
    global orders_df_cache, products_df_cache, orders_agent, products_agent
    user = req.message.lower()

    try:
        if any(keyword in user for keyword in ["product", "inventory", "stock"]):
            if products_df_cache is None:
                products_df_cache = store.fetch_products()
                products_agent = create_pandas_dataframe_agent(llm, products_df_cache,
                                                               verbose=True, allow_dangerous_code=True)
            return {"response": products_agent.run(req.message)}

        elif any(keyword in user for keyword in ["order", "customer", "sales"]):
            if orders_df_cache is None:
                orders_df_cache = store.fetch_orders()
                orders_agent = create_pandas_dataframe_agent(llm, orders_df_cache,
                                                             verbose=True, allow_dangerous_code=True)
            return {"response": orders_agent.run(req.message)}

        else:
            # Fallback: call LangChain agent that can invoke store's CRUD helpers
            # (wrap the store methods as Tools exactly as before)
            return {"response": "Sorry, I didn't understand your request. Please try asking about products or orders."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/client", StaticFiles(directory="client", html=True), name="client")
