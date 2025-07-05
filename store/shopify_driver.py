# store/shopify_driver.py   (simplified example)
from .base import StoreDriver
import shopify
import pandas as pd

class ShopifyDriver(StoreDriver):
    def __init__(self, *, shop_url: str, token: str):
        shopify.Session.setup(api_key="dummy", secret="dummy")
        self.session = shopify.Session(shop_url, "2024-10", token)
        shopify.ShopifyResource.activate_session(self.session)