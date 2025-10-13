def factory():
    """ ID: 1cfa4412-09e6-438e-8544-3670ed05474e """

    def add():
        """ ID: 97a235bb-63aa-41df-88d5-92cb4f421cc2 """
        build()
        pass

    def build():
        """ ID: 94474269-694e-475e-86e9-521707f863b3 """
        pass
    return add

def call_back(call_back_func):
    """ ID: 3136ce43-f803-4736-b449-4009d32a2fa7 """
    call_back_func()

def factory_call():
    """ ID: e75053be-1c5c-4fc0-ad45-0280b2afe8af """
    add = factory()
    add()

def curry_call():
    """ ID: 5c24128a-2e8c-42f4-94f9-d6ed473c3040 """
    factory()()

def main():
    """ ID: 780f194a-ca65-45f4-9163-12f105453884 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()