def factory():
    """ ID: 74958d87-fd80-463a-9c9a-4965a3395c0c """

    def add():
        """ ID: 70b259c9-cbf1-4324-af43-53724beb1b23 """
        build()
        pass

    def build():
        """ ID: 388ab2c9-280c-4ee5-84e9-c1b03034032c """
        pass
    return add

def call_back(call_back_func):
    """ ID: 3232bee4-d4aa-4da1-b29d-69ef0f2f7938 """
    call_back_func()

def factory_call():
    """ ID: 6919c6f8-3e9c-42b0-86f1-d683e95c3794 """
    add = factory()
    add()

def curry_call():
    """ ID: c019b462-2f14-4627-8c21-c56eeba50784 """
    factory()()

def main():
    """ ID: 88194cd9-c111-4e1b-b2ec-a7ce71642d19 """
    factory_call()
    curry_call()
    builder = factory()
    call_back(builder)
main()