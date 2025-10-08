
# ID: e2a7d54a-ab48-4ec8-bb17-4395f91aaea1
def call_back():
    print("call_back")


# ID: 1eda12a6-e828-4f3f-a47e-f25f469ab8af
class GrandParent:

    # ID: c5cfc89d-09f7-4452-8816-33315ba47bd2
    def wake_up(self):
        pass


# ID: d1df3488-10e8-4112-a8f3-de20ef8476d0
class Parent(GrandParent):

    # ID: 9b2bb177-cc70-444f-ba32-49e7c84a636f
    def __init__(self, callback):
        self.callback = callback
        self.wake_up()

    # ID: c620ca26-a43f-42c4-a1b8-d6f3e048d91c
    def greet(self):
        pass


# ID: 105dcea3-deda-4ba1-afcc-f55d381d7343
class Child(Parent):

    # ID: 7a1663ca-c1fd-4b66-9510-baa8108aa9f4
    def greet(self):
        self.callback()

        super().greet()


child = Child(call_back)

child.greet()