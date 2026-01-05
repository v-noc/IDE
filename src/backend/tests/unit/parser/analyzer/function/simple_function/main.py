"""FileID: 511edd7f-57ee-4abf-ad3e-435a60ca0081"""
def factory():
    """ID: 4443bd2b-bcdc-4135-a8d3-16705dc8da11"""
    def add():
        """ID: 6cfe906e-80c1-4f9a-a984-e7154c91a767"""
        build()

    def build():
        """ID: 0af37d95-b990-4aa8-a6d8-f227f080aa11"""
        build()

    return add


def call_back(call_back_func):
    """ID: 3c2f627c-520f-4b52-8690-bc7f5dc36e09"""
    call_back_func()  # lalal


def factory_call():
    """ID: bf998f1a-d36e-49d8-bd98-2bc279c4428b"""
    add = factory()
    add()


def curry_call():
    """ID: e7398873-f663-4c80-9b20-ff8bbb7b4967"""
    factory()()


def main():
    """ID: 4b20776e-824a-45ce-9644-897fac77af54"""
    factory_call()
    curry_call()
    call_back(factory())


main()
