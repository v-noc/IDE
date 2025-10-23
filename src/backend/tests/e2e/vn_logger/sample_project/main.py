def factory():
    """ ID: c6c82126-d878-4c16-8481-3550c6d48d01 """

    def add():
        """ ID: e8dad8d6-d827-4a7d-a0b2-88597c45b657 """
        build()
        pass

    def build():
        """ ID: 498e7e8b-b156-435b-b6d4-1cb2882c90c3 """
        pass
    return add

def call_back(call_back_func):
    """ ID: 3b3df993-6c68-4b1d-af2b-b25c9e690d35 """
    call_back_func()

def factory_call():
    """ ID: 0d820247-8a42-4265-8982-716f0714ac34 """
    add = factory()
    add()

def curry_call():
    """ ID: b9f6edf9-1151-4fed-84ea-100decc18d00 """
    factory()()

def main():
    """ ID: c121b448-3011-41e3-a34a-1ff9a0fe92da """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()