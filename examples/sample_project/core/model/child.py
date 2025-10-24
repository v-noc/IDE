from .parent import Parent, Uncle


class Child(Parent, Uncle):

    def __init__(self, name: str):
        super().__init__(name)

    def get_name(self) -> str:
        return self.name

    def set_name(self, name) -> str:
        self.name = name

    def fly(self):
        pass
