# ID: nodes/2deb13e4-0f51-4daa-8617-cff8a49af363
def factory():
    # ID: nodes/5744da18-e671-4d52-acf1-46adb16bb670
    def add():
        build()
        
        # SYNC_TEST_END
        pass

    # ID: nodes/73b9120a-5de5-433e-82b0-94f5186bca2a
    def build():
        pass

    return add


# ID: nodes/826755bc-908d-46b1-a27a-b0652aedb96c
def call_back(call_back_func):
    call_back_func()


# ID: nodes/04c4c707-8749-41c7-b484-4df68ce62a26
def factory_call():
    add = factory()
    add()


# ID: nodes/ac36b945-f8fa-4904-8306-827afe8f7955
def curry_call():
    factory()()


# ID: nodes/03f5983e-8428-4cf2-b510-fc18b7ab0116
def main():
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)


main()