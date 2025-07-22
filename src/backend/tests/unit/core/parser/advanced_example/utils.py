from .models.models import User

def get_user_name(user: User) -> str:
    # A local variable with a common name
    count = 1
    print(f"Accessing user: {user.name}, count is {count}")
    return user.name

def some_other_function():
    # This function is not used in main, to show we can track that
    pass
