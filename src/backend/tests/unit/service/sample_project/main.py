def factory():
    """ ID: 0bb3248c-7a93-4fd1-957e-46046e80e9bf """

    def add():
        """ ID: 4059ab3b-0498-4001-94c2-44269055d182 """
        build()
        pass

    def build():
        """ ID: a015f903-bc9b-42e6-9b75-78356c35fbe4 """
        pass
    return add

def call_back(call_back_func):
    """ ID: 9c252e82-b3d1-4ecc-a605-de11acf759f0 """
    call_back_func()

def factory_call():
    """ ID: e4842b9c-ca90-4d1d-be21-0a309a4a1ffa """
    add = factory()
    add()

def curry_call():
    """ ID: c1ef1d4b-3f55-4871-9408-d9a30d4c8087 """
    factory()()

def main():
    """ ID: 03512fd2-b840-4cf3-9024-99dd7c6f3c74 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()