def call_back():
    """ID: e1d0c9d5-d4d5-4f69-8c05-79023c06bef9"""

    print('call_back')


class GrandParent:
    """ID: 3703bc3d-f443-42f8-a62a-ed8342ef21cf"""

    def wake_up(self):
        """ID: b7560295-8700-400d-b05b-dacf88cff71e"""

        pass


class Parent(GrandParent):
    """ID: 76c518c1-c51e-4606-9fbc-33538a3b48e1"""

    def __init__(self, callback):
        """ID: fb566921-39c9-4cb9-8662-2d1829623082"""

        self.callback = callback
        self.wake_up()

    def greet(self):
        """ID: d2f9e204-c87a-4419-9a93-e0658b5e3755"""

        pass


class Child(Parent):
    """ID: f623c0bb-b152-4749-8af1-30be079b3020"""

    def greet(self):
        """ID: cb33e131-9c11-495a-95ea-c79ab54650db"""

        self.callback()
        super().greet()


child = Child(call_back)
child.greet()
child.greet()
