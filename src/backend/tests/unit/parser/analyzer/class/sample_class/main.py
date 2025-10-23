def call_back():
    """ ID: 563b52c8-bd86-4b4d-b570-8f3e2145989d """
    print('call_back')

class GrandParent:
    """ ID: 5612cddf-238d-4c98-bff0-4e07c8614e96 """

    def wake_up(self):
        """ ID: 17d2ec50-baa7-47bc-a10c-cadc4145c924 """
        pass

class Parent(GrandParent):
    """ ID: 4a7d7288-c3c7-4b1c-83c4-6541dbac5b84 """

    def __init__(self, callback):
        """ ID: 3149c14d-2814-4949-bf08-e501d7e2c639 """
        self.callback = callback
        self.wake_up()

    def greet(self):
        """ ID: 4786e01a-2b6a-41f6-92a3-8af06ce615b2 """
        pass

class Child(Parent):
    """ ID: f7fdc3bd-1728-4fd2-b75e-29236a24d0a1 """

    def greet(self):
        """ ID: 5d6fbb0b-d61e-4bac-92dd-8e3a23e01ab3 """
        self.callback()
        super().greet()
child = Child(call_back)
child.greet()
child.greet()