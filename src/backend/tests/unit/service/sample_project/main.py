def factory():
    """ ID: cffdf046-0aea-4262-a7b9-7a64bdb2d9bf """

    def add():
        """ ID: 52ab255a-1be0-40d0-b14d-2b255ad1ec26 """
        build()
        pass

    def build():
        """ ID: adc3822b-014e-4608-b274-6afc9f3f0ae3 """
        pass
    return add

def call_back(call_back_func):
    """ ID: 73b245f5-792c-4610-a6aa-07d7a4dab48d """
    call_back_func()

def factory_call():
    """ ID: 35aa08f2-e293-4944-952b-eb50fda77516 """
    add = factory()
    add()

def curry_call():
    """ ID: d3a7bd64-8df3-45ec-9c85-dc3555429e45 """
    factory()()

def main():
    """ ID: 5b7ca7de-e524-4d5d-b2bf-b26dcd9398b4 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()