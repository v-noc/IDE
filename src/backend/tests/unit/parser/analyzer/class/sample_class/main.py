
# ID: 1a0b913e-07e9-44c7-9bf6-e26657e3fdbb
def call_back():
    print("call_back")


# ID: 48af7c12-f898-4d11-bf09-e283cb56162f
class GrandParent:

    # ID: 9e9de099-510e-4d7c-9115-c1b3edea0139
    def wake_up(self):
        pass


# ID: 0efb0ebf-3e8e-4123-88d3-dbe5b2702b37
class Parent(GrandParent):

    # ID: 7983af39-1a4d-4031-bafa-9b212efebd2e
    def __init__(self, callback):
        self.callback = callback
        self.wake_up()

    # ID: 8f73593e-2f36-4d3a-bc16-6fdeba693c6c
    def greet(self):
        pass


# ID: 355c83b2-fb4a-450b-b37f-171ebee4cff6
class Child(Parent):

    # ID: 47e53a69-0cac-4e52-b898-28d2abebd559
    def greet(self):
        self.callback()

        super().greet()


child = Child(call_back)

child.greet()
child.greet()