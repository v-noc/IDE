from .collections.user import UserCollectionManager
from .collections.post import PostCollectionManager
from .orm import EdgeManager
from ..models.follows import Follows

class DatabaseService:
    """
    A central service that provides access to all database collection and edge managers.
    """
    def __init__(self):
        self.users = UserCollectionManager()
        self.posts = PostCollectionManager()
        self.follows = EdgeManager("follows", Follows)

# A single instance of the service to be used as a dependency
db_service = DatabaseService()
