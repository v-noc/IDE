import pydantic
from pydantic import Field

def generate_name() -> str:
    return "John Doe"

class User:
    id: int
    name: str = Field(default=generate_name())
    email: str
    @property
    def data(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }

    def get_user_name(self) -> str:
        # A local variable with a common name
        count = 1
        print(f"Accessing user: {self.name}, count is {count}")
        return self.name

class Post(pydantic.BaseModel):
    id: int
    author: User
    content: str

# A variable with a common name to test scope resolution
count = 10

def get_user_name(user: User) -> str:
    if 1 == 1:
        print("1 is 1")
        return 1
   
    return 2

print(get_user_name(User()))
