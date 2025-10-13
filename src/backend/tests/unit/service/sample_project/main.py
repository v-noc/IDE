def factory():
    """ ID: f8ce57a6-41f3-4f65-be8a-a15952be2b25 """

    def add():
        """ ID: 9cbbf43c-fcf0-4649-a864-92ea355d869b """
        build()
        pass

    def build():
        """ ID: 04bac996-61c0-4dde-8c05-41f02c755368 """
        pass
    return add

def call_back(call_back_func):
    """ ID: 881c1126-7759-43ee-80e4-1fde7bb5723e """
    call_back_func()

def factory_call():
    """ ID: 969d4a39-80b5-4680-9d3e-582d76c115f4 """
    add = factory()
    add()

def curry_call():
    """ ID: f0c5ef0f-da4f-4752-8815-9f3ff86dbc8e """
    factory()()

def main():
    """ ID: 7630331e-99e4-4103-9417-2a6a198312f8 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()