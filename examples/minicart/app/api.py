"""FileID: 28b4fae1-e32e-41d5-bbab-6c16e0ae958d"""
from fastapi import FastAPI, HTTPException
from vn_logger import context_logger

from app.checkout import checkout_order
from app.models import OrderRequest

app = FastAPI(title="MiniCart")


@app.post("/checkout")
@context_logger('b76b0712-b1bb-4bae-b5cf-e06d2941f80a')
def checkout(order: OrderRequest):
    """ID: b76b0712-b1bb-4bae-b5cf-e06d2941f80a"""
    try:
        completed = checkout_order(order)
    except TimeoutError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return completed
