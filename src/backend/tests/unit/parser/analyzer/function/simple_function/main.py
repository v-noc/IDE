
# ID: nodes/826bf132-c642-4dfb-88d6-9a8da252b4e2
def factory():

    # ID: nodes/01cb74cc-f4b0-4550-bead-0aedcdaab082
    def add():
        build()
        pass

    # ID: nodes/92206c1d-77f2-41d3-9b59-04e1c8a89dfd
    def build():
        pass

    return add


# ID: nodes/d6fd2bd2-8a75-4870-ae65-3d6fe17f344f
def call_back(call_back_func):
    call_back_func()


# ID: nodes/efe45ab1-6608-4155-be04-11e66f908431
def factory_call():
    add = factory()
    add()


# ID: nodes/38bae5aa-4d74-4c67-a8d4-f9ee924e1bc6
def curry_call():
    factory()()


# ID: nodes/b7342110-0774-451f-a7d4-7500d798e87f
def main():
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)


main()