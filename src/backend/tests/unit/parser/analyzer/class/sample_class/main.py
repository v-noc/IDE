def call_back():
    """ ID: aafd627f-7d33-4f09-a319-c96a621dfb61 """
    print('call_back')

class GrandParent:
    """ ID: fb195e95-3d02-49e9-ab8b-7f412c5cb290 """

    def wake_up(self):
        """ ID: 6343c191-85fc-4587-b861-bb6961eccd90 """
        pass

class Parent(GrandParent):
    """ ID: 8539c98a-228e-4e25-9dad-e2c3ef18e5b0 """

    def __init__(self, callback):
        """ ID: 5ee25f4f-e608-4e6a-9dab-cf0eca8beeca """
        self.callback = callback
        self.wake_up()

    def greet(self):
        """ ID: 166940dd-8118-4a00-9e9e-7096ef6f0f08 """
        pass

class Child(Parent):
    """ ID: 48b100f9-de90-4900-89cd-41695a16d9bf """

    def greet(self):
        """ ID: 586fd4e2-8d17-4080-8711-84d96cfb151a """
        self.callback()
        super().greet()
child = Child(call_back)
child.greet()
child.greet()