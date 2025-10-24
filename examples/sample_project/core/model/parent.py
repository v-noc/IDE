
class GrandParent:
    def get_name(self):
        pass

    def walk(self):
        pass

    def sleep(self):
        pass


class Uncle(GrandParent):
    def get_name(self):
        pass

    def walk(self):
        pass

    def run(self):
        pass


class Parent(GrandParent):
    def __init__(self, name: str):
        self.name = name

    def get_name(self):
        return self.name
