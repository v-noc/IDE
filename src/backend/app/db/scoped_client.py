# app/db/scoped_client.py
from contextlib import asynccontextmanager
from app.db.async_terminus_client import AsyncClient
from app.db.context import DbTarget


@asynccontextmanager
async def scoped_client(base: AsyncClient, target: DbTarget):
    """
    Creates a shallow clone and applies db/branch/ref.
    Assumes clone shares httpx session with base (your AsyncClient.clone does).
    """
    c = base.clone()
    c.db = target.db
    c.branch = target.branch
    c.ref = target.ref
    c.team = target.team
    c.repo = target.repo
    try:
        yield c
    finally:
        # Do NOT close base session here (clone shares it).
        # If in the future clone gets its own session, close it here.
        pass
