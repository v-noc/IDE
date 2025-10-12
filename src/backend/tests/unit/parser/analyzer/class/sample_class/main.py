def call_back():
    """ ID: 79035f16-6afb-4dd7-9d29-b647a48788eb """
    print('call_back')

class GrandParent:
    """ ID: 0594d51b-8e2c-47d9-9e69-b64344fc9d6f """

    def wake_up(self):
        """ ID: 70cdf41f-dee5-4c3a-a096-764f24e113dd """
        pass

class Parent(GrandParent):
    """ ID: ca7b53c5-806c-48a3-af74-7141c5a55b5f """

    def __init__(self, callback):
        """ ID: d03a7bb8-d354-43d6-9ff5-c85eebab1211 """
        self.callback = callback
        self.wake_up()

    def greet(self):
        """ ID: 22c4c840-27ed-4f46-8d92-137f3f5edf7a """
        pass

class Child(Parent):
    """ ID: 45429e29-7445-4220-a8cd-52b9d5546d05 """

    def greet(self):
        """ ID: 03599961-a4e6-4f29-9a8a-36d6b5349086 """
        self.callback()
        super().greet()
child = Child(call_back)
child.greet()
child.greet()