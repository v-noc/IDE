from ..orm import CollectionManager
from ...models.user import User

class UserCollectionManager(CollectionManager[User]):
    def __init__(self):
        super().__init__("users", User)

    def find_by_email(self, email: str) -> User | None:
        """Example of a custom method"""
        cursor = self._collection.find({"email": email}, limit=1)
        if cursor.count() > 0:
            return self.model(**cursor.next())
        return None
