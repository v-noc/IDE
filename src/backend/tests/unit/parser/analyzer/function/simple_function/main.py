def factory():
    """ ID: c51ee26b-d36e-4254-ac43-b8ed574adba2 """

    def add():
        """ ID: 67eb054a-acf4-4a72-a805-a632f7956930 """
        build()
        pass

    def build():
        """ ID: 03f89221-ca63-4fe7-bc06-79c91b3d10b9 """
        pass
    return add

def call_back(call_back_func):
    """ ID: 58e9b3a8-7a8e-4c09-acc2-e2219f8ddfce """
    call_back_func()

def factory_call():
    """ ID: 9e6978a7-e724-4761-b989-4446fc9de7a1 """
    add = factory()
    add()

def curry_call():
    """ ID: 5304efed-5504-4ea8-8677-b90c45943168 """
    factory()()

def main():
    """ ID: 9dfc4beb-43c9-49f7-aa32-42b67b62b7e3 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()