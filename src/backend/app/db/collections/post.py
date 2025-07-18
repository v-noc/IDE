from ..orm import CollectionManager
from ...models.post import Post, NewPost
from ...models.user import User

class PostCollectionManager(CollectionManager[Post]):
    def __init__(self):
        super().__init__("posts", Post)

    def create_for_user(self, user: User, post_data: NewPost) -> Post:
        """
        Creates a post and explicitly links it to the author.
        This is a helper method to ensure the author_key is set correctly.
        """
        # In a real app, you might create a UserCreatesPost edge here as well.
        post = Post(author_key=user.key, **post_data.model_dump())
        return self.create(post)
