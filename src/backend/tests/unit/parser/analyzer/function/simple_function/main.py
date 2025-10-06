
# ID: nodes/158eeac7-aca1-4f7b-9806-f527f297d93b
def factory():

    # ID: nodes/df32a56e-26d5-4b87-b9f2-eab131775987
    def add():
        build()
        pass

    # ID: nodes/1a2a83b0-47b2-409a-ad4f-d14dbf0227ab
    def build():
        pass

    return add


# ID: nodes/bf20778c-b4b2-4252-acb1-b0df6900f8ec
def call_back(call_back_func):
    call_back_func()


# ID: nodes/c733e17c-c62e-4d17-b9ee-b14114ff9288
def factory_call():
    add = factory()
    add()


# ID: nodes/abd7e38e-cd0d-4c3f-a458-33f2562fbe9f
def curry_call():
    factory()()


# ID: nodes/652012d4-10a9-4fd0-997c-3b217b2b707e
def main():
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)


main()