def factory():
    """ ID: b4d63fd0-ec53-4daf-b715-27172c36949d """

    def add():
        """ ID: e7a995f1-2c90-402b-91f8-ea24eba9cbd7 """
        build()
        pass

    def build():
        """ ID: 7659bfe1-f96e-4dcb-bec6-823764cd3e9b """
        pass
    return add

def call_back(call_back_func):
    """ ID: 3d038c63-a960-4992-acab-774a58ae742d """
    call_back_func()

def factory_call():
    """ ID: 4182f759-5f53-4046-8869-8e322eb1e5a7 """
    add = factory()
    add()

def curry_call():
    """ ID: 81f6a791-085f-4be5-ab4d-8476627529ad """
    factory()()

def main():
    """ ID: c8d8b229-d58f-4c7f-a0be-b80af80c4dea """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()