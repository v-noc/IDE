from fastapi import FastAPI
from .api import users, root
from .db.client import get_db

app = FastAPI()

app.include_router(root.router)
app.include_router(users.router, prefix="/users", tags=["users"])
