"""FileID: da94c0ec-bba5-407b-8ef9-48de20405791"""
from vn_logger import context_logger, logger_core

from app.inventory import check_stock, release_stock, reserve_stock
from app.models import OrderRequest
from app.orders import CompletedOrder, create_order
from app.payments import charge_payment


@context_logger('859e6adb-30a8-48eb-ae59-0976b9b9d25a')
def checkout_order(order: OrderRequest) -> CompletedOrder:
    """ID: 859e6adb-30a8-48eb-ae59-0976b9b9d25a"""
    if not check_stock(order.sku, order.quantity):
        raise ValueError(f"Out of stock: {order.sku}")

    reserve_stock(order.sku, order.quantity)

    try:
        transaction_id = charge_payment(order)
    except TimeoutError:
        cancel_checkout(order)
        raise

    return create_order(order, transaction_id)


@context_logger('160580fd-4a9d-4dd0-882a-b494388e2894')
def cancel_checkout(order: OrderRequest) -> None:
    """ID: 160580fd-4a9d-4dd0-882a-b494388e2894"""
    release_stock(order.sku, order.quantity)
