def factory():
    """ ID: 4a518680-b2f9-4b5d-82c6-d8aeb5fc942f """

    def add():
        """ ID: 339c39df-852e-45ed-93c0-3c6e32761cf6 """
        build()
        pass

    def build():
        """ ID: 3d52d24e-fd4c-4df3-b596-389e684adb49 """
        pass
    return add

def call_back(call_back_func):
    """ ID: b8aaffa9-4b6c-4a81-950b-992af6e1f29c """
    call_back_func()

def factory_call():
    """ ID: d5d873cc-be91-4bfb-a931-081ee2eb3fbb """
    add = factory()
    add()

def curry_call():
    """ ID: f403b561-f99c-4a7b-bdec-1dbd65334535 """
    factory()()

def main():
    """ ID: c973e5be-ccdb-4eb2-8ae7-3696200c9e0a """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()