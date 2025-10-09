
# ID: 25ceb825-08b9-4534-834e-1f40751e2992
def call_back():
    print("call_back")


# ID: be3515b3-3c65-425c-86fb-e4c93e962b9a
class GrandParent:

    # ID: e9d31cad-6bbb-416a-8c1b-a644dea6b713
    def wake_up(self):
        pass


# ID: 5153ef60-2207-4d8d-8e91-6752466e8811
class Parent(GrandParent):

    # ID: 83b9366c-894d-4b8e-a836-398cc5065b8c
    def __init__(self, callback):
        self.callback = callback
        self.wake_up()

    # ID: e2247af2-2aa5-4718-9d10-5d27f6ad8850
    def greet(self):
        pass


# ID: 10ecbcd8-7e25-44e7-9535-49df269d7d55
class Child(Parent):

    # ID: 828a0cb8-29bb-47f2-9c6b-015f06d0244b
    def greet(self):
        self.callback()

        super().greet()


child = Child(call_back)

child.greet()
child.greet()