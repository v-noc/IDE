"""FileID: 9a1d2f0c-f274-409c-bf93-87eb2de3688c"""
from dataclasses import dataclass

from vn_logger import context_logger

from app.models import OrderRequest

_ORDERS: dict[str, "CompletedOrder"] = {}


@dataclass
class CompletedOrder:
    """ID: 9c135a57-76e1-4451-b661-8ce37c051c85"""
    order_id: str
    sku: str
    quantity: int
    total: float
    customer: str
    transaction_id: str


@context_logger('6932df08-3fee-42eb-bf1f-f9192f62f0d2')
def create_order(order: OrderRequest, transaction_id: str) -> CompletedOrder:
    """ID: 6932df08-3fee-42eb-bf1f-f9192f62f0d2"""
    completed = CompletedOrder(
        order_id=order.order_id,
        sku=order.sku,
        quantity=order.quantity,
        total=order.total,
        customer=order.customer,
        transaction_id=transaction_id,
    )
    _ORDERS[order.order_id] = completed
    return completed


def hello():
    """ID: 6f0fb0b8-580a-485b-97bb-541407c0d80b"""
    pass
# hello
