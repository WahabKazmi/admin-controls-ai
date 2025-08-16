from abc import ABC, abstractmethod
import pandas as pd

class StoreDriver(ABC):
    # ----- Products -----
    @abstractmethod
    def fetch_products(self, **params) -> pd.DataFrame:
        pass

    @abstractmethod
    def create_product(self, *, name: str, price: float, description: str = "", image_url: str = None):
        pass

    @abstractmethod
    def update_product(self, product_id: int, **fields):
        pass

    @abstractmethod
    def delete_product(self, product_id: int):
        pass

    # ----- Orders -----
    @abstractmethod
    def fetch_orders(self, **params) -> pd.DataFrame:
        pass

    @abstractmethod
    def create_order(self, *, customer: str, product_id: int, quantity: int, total: float):
        pass

    @abstractmethod
    def update_order_status(self, order_id: int, new_status: str):
        pass

    @abstractmethod
    def delete_order(self, order_id: int):
        pass

    # ----- Reports -----
    @abstractmethod
    def get_best_selling_product_today(self):
        """
        Return dict with keys:
        - product_id
        - product_name
        - quantity_sold
        - total_sales
        or a dict with 'message' key in case of no data/error.
        """
        pass
