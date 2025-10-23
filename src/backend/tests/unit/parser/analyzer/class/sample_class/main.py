def call_back():
    """ ID: b72d5d42-97dd-4ba2-9e45-bade488af627 """
    print('call_back')

class GrandParent:
    """ ID: 94ccfadf-f200-4410-93b7-717b783cf708 """

    def wake_up(self):
        """ ID: 7fa9bd9e-a35c-4fff-8b55-59554120b664 """
        pass

class Parent(GrandParent):
    """ ID: 463a185c-acde-4bb8-8cce-7a30f34916a0 """

    def __init__(self, callback):
        """ ID: acbb9505-5e0a-4f09-92fe-587e748f3649 """
        self.callback = callback
        self.wake_up()

    def greet(self):
        """ ID: e6c150de-045f-49bc-855b-f806db9f9e67 """
        pass

class Child(Parent):
    """ ID: 0db48ae0-f65d-49fe-baba-353c83a07061 """

    def greet(self):
        """ ID: cd10e5c8-4ff5-49cf-9815-272edd284234 """
        self.callback()
        super().greet()
child = Child(call_back)
child.greet()
child.greet()