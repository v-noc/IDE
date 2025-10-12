def factory():
    """ ID: 38a4ccfa-e0c7-4c68-a26e-779e856ef6b8 """

    def add():
        """ ID: 5f9ed40b-f6a7-4822-ae53-c861ff556b49 """
        build()
        pass

    def build():
        """ ID: 44915d3a-b9f0-43b7-984e-b86d225f81eb """
        pass
    return add

def call_back(call_back_func):
    """ ID: 0651ba78-720a-4ca2-aa22-1d7fc87f7e5c """
    call_back_func()

def factory_call():
    """ ID: 266a6b2a-7961-4afa-b98e-1f5a4500fccc """
    add = factory()
    add()

def curry_call():
    """ ID: 4de3fe95-21e9-4a7b-8b57-3e3fc5a75cc6 """
    factory()()

def main():
    """ ID: 296c4084-7fed-4384-a0e9-21dd029be248 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()