def factory():
    """ ID: bc2d936b-5ce0-4d3f-b7de-13f064543628 """

    def add():
        """ ID: a53c4086-1aa5-4c03-bf00-ed0247e8574b """
        build()
        pass

    def build():
        """ ID: ad646157-1d7f-4db7-a353-aa901e5180c2 """
        pass
    return add

def call_back(call_back_func):
    """ ID: d15ee536-4048-4533-8b67-d96f03060504 """
    call_back_func()

def factory_call():
    """ ID: e5f98f83-6cb8-45e1-8620-fcd4ce67128f """
    add = factory()
    add()

def curry_call():
    """ ID: 7a5a4db5-8e23-4825-8e72-90dc1a131701 """
    factory()()

def main():
    """ ID: 1cd81be6-bfbb-40e3-9324-c8aa05617a3d """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()