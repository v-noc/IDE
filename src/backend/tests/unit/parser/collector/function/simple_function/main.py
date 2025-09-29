
def factory():

    def add():
        # build()
        pass

    def build():
        pass

    return add


def call_back(call_back_func):
    call_back_func()


# def factory_call():
#     add = factory()
#     add()


# def curry_call():
#     factory()()


def main():
    # factory_call()
    # curry_call()
    builder = factory()
    call_back(builder)


main()
