from .parent import Parent


class Child(Parent):
    def __init__(self, name: str):
        super().__init__(name)
