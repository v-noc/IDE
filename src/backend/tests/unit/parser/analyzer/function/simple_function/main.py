def factory():
    """ ID: 0135b0ba-9209-4180-a722-e30591b1cff0 """

    def add():
        """ ID: b5689b2a-9ca9-449f-8154-0401dfb47779 """
        build()
        pass

    def build():
        """ ID: f73533d5-f805-4250-a1f1-d2e8f261bd0f """
        pass
    return add

def call_back(call_back_func):
    """ ID: 92b9ac6d-507f-4590-8954-69a664bf1c2f """
    call_back_func()

def factory_call():
    """ ID: 05246666-c580-4716-a33e-d40bac84bfd0 """
    add = factory()
    add()

def curry_call():
    """ ID: dd699658-c56f-41cb-bc1e-bc54d18be1ca """
    factory()()

def main():
    """ ID: 741369e2-a0b9-4d9d-8a7f-30fa966a89d5 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()