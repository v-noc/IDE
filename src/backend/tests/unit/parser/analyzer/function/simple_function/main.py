def factory():
    """ ID: 5e33622d-727d-4647-890d-c5dcd5796e50 """

    def add():
        """ ID: de6eb124-8578-4e9e-ba5f-b6ae1f78c479 """
        build()
        pass

    def build():
        """ ID: a616bdb9-9ab5-4b08-ac0f-fae50be33a97 """
        pass
    return add

def call_back(call_back_func):
    """ ID: efd17fa5-7b58-4b5b-918e-9bf3254083a6 """
    call_back_func()

def factory_call():
    """ ID: c796ec61-50eb-4f1d-b800-64a9aa65e17f """
    add = factory()
    add()

def curry_call():
    """ ID: 1efc42ee-d2c6-4dbf-aa4c-a16151ecd487 """
    factory()()

def main():
    """ ID: 01dde4f5-4e98-4423-ad6a-e074faf43a4c """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()