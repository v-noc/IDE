"""FileID: a323aca0-3843-46a7-a707-1f43f6f56ca4"""
from dataclasses import dataclass

from vn_logger import context_logger


@dataclass
class OrderRequest:
    """ID: f1611996-feed-4ea7-99b8-87803ace2f3b"""
    order_id: str
    sku: str
    quantity: int
    unit_price: float
    customer: str

    @property
    @context_logger('f1d3b837-67b6-47d9-9400-51131f15f3d7')
    def total(self) -> float:
        """ID: f1d3b837-67b6-47d9-9400-51131f15f3d7"""
        return round(self.unit_price * self.quantity, 2)
