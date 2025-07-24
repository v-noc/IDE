# src/backend/tests/unit/core/parser/sample_project/models/user.py

class User:
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name
