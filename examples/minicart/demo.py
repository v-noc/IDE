"""FileID: e876b196-226f-4997-8f3a-cac4d01b51d6"""
from vn_logger import context_logger, configure_logger

from app.checkout import checkout_order
from app.models import OrderRequest


def main():
    """ID: e4efd15c-958e-47c5-abb3-7ffd7c7920da"""

    order = OrderRequest(
        order_id="1042",
        sku="DOCK-01",
        quantity=2,
        unit_price=49.00,
        customer="demo-customer",
    )

    completed = checkout_order(order)
    print(f"Checkout succeeded: {completed}")


if __name__ == "__main__":
    configure_logger('http://127.0.0.1:8050/api/v1/jsonrpc',
                     'ProjectSchema/minicart')
    main()
