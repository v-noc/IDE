# ID: nodes/4e53e347-92e9-4aa5-8425-23aa6f06a31b
def factory():
    # ID: nodes/5d7befad-6780-4da7-a600-e06e5188c836
    def add():
        build()
        
        # SYNC_TEST_END
        pass

    # ID: nodes/faa10914-1f2e-4645-a2f8-d2ce89ea7f34
    def build():
        pass

    return add


# ID: nodes/c7b31513-fc21-437d-ab4b-31e28c89e519
def call_back(call_back_func):
    call_back_func()


# ID: nodes/338dae26-c625-4e2d-bde2-1f46756158f8
def factory_call():
    add = factory()
    add()


# ID: nodes/4ed56768-7422-464d-967b-8d0f3cf13894
def curry_call():
    factory()()


# ID: nodes/96bbf24e-0ef0-4fd5-8e50-acce77ba781f
def main():
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)


main()