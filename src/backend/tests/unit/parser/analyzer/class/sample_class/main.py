# ID: nodes/293d5161-04dc-403e-8267-6270f20dd8d2
def call_back():
    print("call_back")


# ID: nodes/9dc8ac17-beab-4cc0-b3ad-4d8c422ae72b
class GrandParent:
    # ID: nodes/dec488ac-d319-4ef7-810a-029a7e25143b
    def wake_up(self):
        pass


# ID: nodes/f5c27b24-7caa-4b6a-9751-e1759a6914da
# ID: nodes/8d66230e-fe21-4e4c-a6f7-861c582faac9
class Parent(GrandParent):
    # ID: nodes/3e69580e-6b7f-4b03-9348-ec646b62c31e
    def __init__(self, callback):
        self.callback = callback
        self.wake_up()

    # ID: nodes/bb1d332c-252b-4725-ae5d-c7edecfe9822
    def greet(self):
        pass


# ID: nodes/b00ea966-2c91-4738-a9a3-597486644801
class Child(Parent):
    # ID: nodes/44725fae-bab0-4441-a532-40db8ce5b609
    def greet(self):
        self.callback()
        super().greet()


child = Child(call_back)
child.greet()