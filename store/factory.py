# store/factory.py
import os
from .woocommerce_driver import WooCommerceDriver
from .shopify_driver   import ShopifyDriver
from .base import StoreDriver

def get_driver() -> StoreDriver:
    store_type = os.getenv("STORE_TYPE", "woocommerce")
    if store_type == "woocommerce":
        return WooCommerceDriver(
            url=os.getenv("WC_URL"),
            consumer_key=os.getenv("WC_CONSUMER_KEY"),
            consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
        )
    elif store_type == "shopify":
        return ShopifyDriver(
            shop_url=os.getenv("SHOP_URL"),
            token=os.getenv("SHOP_TOKEN"),
        )
    else:
        raise ValueError(f"Unsupported STORE_TYPE={store_type}")

class Store:
    """Thin façade used everywhere else."""
    def __init__(self, driver: StoreDriver | None = None):
        self._driver = driver or get_driver()

    # Orders
    def fetch_orders(self, **kw):           return self._driver.fetch_orders(**kw)
    def create_order(self, **kw):           return self._driver.create_order(**kw)
    def update_order_status(self, *args, **kw): return self._driver.update_order_status(*args, **kw)

    # Products
    def fetch_products(self, **kw):         return self._driver.fetch_products(**kw)
    def create_product(self, **kw):         return self._driver.create_product(**kw)
    def update_product(self, *args, **kw):  return self._driver.update_product(*args, **kw)
