"""FileID: 22030937-af9b-47ef-9c67-4ca21bf605d9"""
from vn_logger import context_logger

from app.gateway import send_charge

@context_logger('b3e1bc9f-388c-48fc-b8db-6607df51ad58')
def retry_charge(order, max_attempts=2):
    """ID: 7a4e1aac-0b78-4f2c-b532-dc4dfef80dee"""
    for attempt in range(max_attempts):
        try:
            return send_charge(
                order.total,
                order.order_id
            )
        except TimeoutError:
            if attempt == max_attempts - 1:
                raise

@context_logger('b3e1bc9f-388c-48fc-b8db-6607df51ad58')
def charge_payment(order):
    """ID: b3e1bc9f-388c-48fc-b8db-6607df51ad58"""
  
    return retry_charge(order)
