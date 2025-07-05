# store/base.py
from abc import ABC, abstractmethod
import pandas as pd
from typing import Any, Dict

class StoreDriver(ABC):
    """Interface every e-commerce backend must implement."""

    # ---------- Orders ----------
    @abstractmethod
    def fetch_orders(self, **params) -> pd.DataFrame: ...
    @abstractmethod
    def create_order(self, *, customer: str, product_id: int,
                     quantity: int, total: float) -> Dict[str, Any]: ...
    @abstractmethod
    def update_order_status(self, order_id: int, new_status: str) -> Dict[str, Any]: ...

    # ---------- Products ----------
    @abstractmethod
    def fetch_products(self, **params) -> pd.DataFrame: ...
    @abstractmethod
    def create_product(self, *, name: str, price: float,
                       description: str = "") -> Dict[str, Any]: ...
    @abstractmethod
    def update_product(self, product_id: int, **fields) -> Dict[str, Any]: ...