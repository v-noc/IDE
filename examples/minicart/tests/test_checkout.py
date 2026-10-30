"""FileID: b4f3332c-0e1e-42f0-a4b7-867b90fa7f0d"""
import pytest

from app import gateway, inventory
from app.checkout import checkout_order
from app.models import OrderRequest


@pytest.fixture(autouse=True)
def reset_state():
    """ID: e93c4288-c505-4ba0-911a-3753c4e9e650"""
    inventory._STOCK["DOCK-01"] = 3
    gateway._ATTEMPTS.clear()
    yield


def test_checkout_recovers_from_gateway_timeout():
    """ID: 49791007-7d67-401f-ab57-a6f821adbcb2"""
    order = OrderRequest(
        order_id="test-1",
        sku="DOCK-01",
        quantity=2,
        unit_price=49.00,
        customer="tester",
    )

    completed = checkout_order(order)

    assert completed.transaction_id
    assert gateway._ATTEMPTS["test-1"] == 2
    assert inventory._STOCK["DOCK-01"] == 1


def test_checkout_out_of_stock():
    """ID: e87b5c89-97f0-4ac7-b1b5-d10cbb95767e"""
    order = OrderRequest(
        order_id="test-2",
        sku="DOCK-01",
        quantity=10,
        unit_price=49.00,
        customer="tester",
    )

    with pytest.raises(ValueError):
        checkout_order(order)
