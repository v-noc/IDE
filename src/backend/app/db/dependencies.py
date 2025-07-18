from .orm import CollectionManager
from ..models.user import User

def get_user_collection() -> CollectionManager[User]:
    return CollectionManager("users", User)
