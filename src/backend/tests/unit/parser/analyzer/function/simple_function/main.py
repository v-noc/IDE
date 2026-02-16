
def factory():

    def add():
        build()

    def build():
        build()

    return add


def call_back(call_back_func):
    call_back_func()  # lalal


def factory_call():
    add = factory()
    add()


def curry_call():
    factory()()


def main():
    factory_call()
    curry_call()
    call_back(factory())


main()
