from typing import Optional
from .models import models
from . import utils as u

# A global variable with a common name
count: int = 0

def create_post(author: models.User, content: Optional[str]) -> models.Post:
    global count
    post = models.Post()
    post.id = 1
    post.author = author
    post.content = content
    count += 1
    return post

def user_not_found(user: models.User) -> bool:
    print(f"User not found: {user.id}")
    return True

def main():
    user = models.User()
    user.id = 101
    user.name = "Alice"
    user.email = "alice@example.com"

    username = u.get_user_name(user)
    print(f"Username from util: {username}")

    if username == "Bob":
        user_not_found(user)
        
    elif username.startswith("A"):
        print("Username starts with A")
        print(f"User: {user.get_user_name()}")

    post = create_post(user, "Hello, world!")
    print(f"Created post: {post.id} by {post.author.name}")
    print(f"Total posts created: {count}")

   

if __name__ == "__main__":
    main()
