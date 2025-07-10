import os
from .woocommerce_driver import WooCommerceDriver
# from .shopify_driver import ShopifyDriver  # Uncomment if using Shopify

class Store:
    def __init__(self):
        backend = os.getenv("STORE_BACKEND", "woocommerce").lower()

        if backend == "woocommerce":
            self.driver = WooCommerceDriver(
                url=os.getenv("WC_URL"),
                consumer_key=os.getenv("WC_CONSUMER_KEY"),
                consumer_secret=os.getenv("WC_CONSUMER_SECRET")
            )
        # elif backend == "shopify":
        #     self.driver = ShopifyDriver(
        #         shop_url=os.getenv("SHOPIFY_URL"),
        #         access_token=os.getenv("SHOPIFY_TOKEN")
        #     )
        else:
            raise ValueError(f"❌ Unsupported store backend: {backend}")

    def fetch_products(self, **params):
        return self.driver.fetch_products(**params)

    def create_product(self, **kwargs):
        return self.driver.create_product(**kwargs)

    def update_product(self, product_id: int, **fields):
        return self.driver.update_product(product_id, **fields)

    def delete_product(self, product_id: int):
        return self.driver.delete_product(product_id)

    def fetch_orders(self, **params):
        return self.driver.fetch_orders(**params)

    def create_order(self, **kwargs):
        return self.driver.create_order(**kwargs)

    def update_order_status(self, order_id: int, new_status: str):
        return self.driver.update_order_status(order_id, new_status)

    def delete_order(self, order_id: int):
        return self.driver.delete_order(order_id)
