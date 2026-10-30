"""FileID: fd425a3e-9aa9-4bb3-82f8-66ff7dc8a280"""
from vn_logger import context_logger, logger_core

LOW_STOCK_THRESHOLD = 2

_STOCK = {
    "DOCK-01": 3,
}


@context_logger('b47e48c0-a645-441a-be45-32751c682a94')
def check_stock(sku: str, quantity: int) -> bool:
    """ID: b47e48c0-a645-441a-be45-32751c682a94"""
    available = _STOCK.get(sku, 0)
    return available >= quantity


@context_logger('8a9cc864-99c6-4f9f-ae62-96c969bd2e34')
def reserve_stock(sku: str, quantity: int) -> None:
    """ID: 8a9cc864-99c6-4f9f-ae62-96c969bd2e34"""
    if not check_stock(sku, quantity):
        raise ValueError(f"Not enough stock for {sku}")

    _STOCK[sku] -= quantity
    remaining = _STOCK[sku]

    if remaining <= LOW_STOCK_THRESHOLD:
        logger_core.logger.warning(f"Only {remaining} unit(s) remaining for {sku}")


@context_logger('bb848a8d-9658-4096-8efd-6b9cb749bb4a')
def release_stock(sku: str, quantity: int) -> None:
    """ID: bb848a8d-9658-4096-8efd-6b9cb749bb4a"""
    _STOCK[sku] = _STOCK.get(sku, 0) + quantity
