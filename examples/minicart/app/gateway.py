"""FileID: 8b53c33c-fa23-47a0-a59c-d4aec850f446"""
from vn_logger import context_logger, logger_core

# Tracks how many times each order has hit the gateway, so the demo is
# deterministic: the first attempt for any order always times out.
_ATTEMPTS: dict[str, int] = {}


@context_logger('bfdab727-f72c-4156-89ac-83e3673c23fa')
def send_charge(amount: float, order_id: str) -> str:
    """ID: bfdab727-f72c-4156-89ac-83e3673c23fa"""
    attempt = _ATTEMPTS.get(order_id, 0) + 1
    _ATTEMPTS[order_id] = attempt

    if attempt == 1:
        logger_core.logger.error(f"Payment gateway timeout for order {order_id}")
        raise TimeoutError(f"Gateway timeout for order {order_id}")

    return f"txn_{order_id}_{attempt}"
