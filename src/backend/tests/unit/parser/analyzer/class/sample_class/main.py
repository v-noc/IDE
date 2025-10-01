def call_back():
    print("call_back")


class GrandParent:
    def wake_up(self):
        pass


class Parent(GrandParent):
    def __init__(self, callback):
        self.callback = callback
        self.wake_up()

    def greet(self):
        pass


class Child(Parent):
    def greet(self):
        self.callback()
        super().greet()


child = Child(call_back)
child.greet()
