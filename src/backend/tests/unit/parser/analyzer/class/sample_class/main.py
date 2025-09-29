
class GrandParent:
    def wake_up(self):
        pass


class Parent(GrandParent):
    def __init__(self):
        self.wake_up()

    def greet(self):
        pass


class Child(Parent):
    def greet(self):
        super().greet()


child = Child()
child.greet()
