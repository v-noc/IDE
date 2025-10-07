# ID: nodes/21348b09-b651-439f-be3a-f12a58559831
def factory():
    # ID: nodes/a0125725-fd67-42f9-8a7c-1617d27fb131
    def add():
        build()
        pass

    # ID: nodes/984169a8-728c-4aeb-b34d-d35d668726ef
    def build():
        pass

    return add


# ID: nodes/aacf60c5-fda1-4a56-a36a-41b4fc135d97
def call_back(call_back_func):
    call_back_func()


# ID: nodes/d4de6ce7-2072-476d-9965-56fe55a3f7b9
def factory_call():
    add = factory()
    add()


# ID: nodes/5d5069d4-b917-4810-8a3e-26b137ebc654
def curry_call():
    factory()()


# ID: nodes/d5d2ecfc-d463-4e5c-8934-96d8d1212ee5
def main():
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)


main()